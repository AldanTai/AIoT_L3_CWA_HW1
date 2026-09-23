"""中央氣象署 API 用戶端與氣溫資料解析工具。"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Any

import pandas as pd
import requests


DEFAULT_DATASET_ID = "F-C0032-001"
API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/{dataset_id}"
FORECAST_COLUMNS = ["regionName", "dataDate", "mint", "maxt"]


class WeatherAPIError(RuntimeError):
    """CWA API 請求或回應格式錯誤。"""


def fetch_weather_data(
    api_key: str,
    dataset_id: str = DEFAULT_DATASET_ID,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """向 CWA Open Data API 取得 JSON 資料。"""
    if not api_key or not api_key.strip():
        raise WeatherAPIError("尚未設定 CWA API Key。")

    try:
        response = requests.get(
            API_URL.format(dataset_id=dataset_id),
            params={"Authorization": api_key.strip(), "format": "JSON"},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.Timeout as exc:
        raise WeatherAPIError("連線中央氣象署逾時，請稍後再試。") from exc
    except requests.RequestException as exc:
        raise WeatherAPIError(f"無法取得中央氣象署資料：{exc}") from exc
    except ValueError as exc:
        raise WeatherAPIError("中央氣象署回應不是有效的 JSON。") from exc

    if not isinstance(payload, dict):
        raise WeatherAPIError("中央氣象署回應格式不正確。")
    if str(payload.get("success", "")).lower() != "true":
        message = payload.get("message") or "API 回報請求失敗，請檢查授權碼與資料集。"
        raise WeatherAPIError(str(message))
    if not isinstance(payload.get("records"), dict):
        raise WeatherAPIError("API 回應缺少 records 資料。")
    return payload


def _locations_from_records(records: dict[str, Any]) -> list[dict[str, Any]]:
    """兼容 CWA 不同資料集的地區節點命名。"""
    locations = records.get("location") or records.get("Location")
    if isinstance(locations, list):
        return [item for item in locations if isinstance(item, dict)]

    containers = records.get("Locations") or records.get("locations") or []
    if isinstance(containers, dict):
        containers = [containers]
    result: list[dict[str, Any]] = []
    if isinstance(containers, list):
        for container in containers:
            if not isinstance(container, dict):
                continue
            nested = container.get("Location") or container.get("location") or []
            if isinstance(nested, list):
                result.extend(item for item in nested if isinstance(item, dict))
    return result


def _element_name(element: dict[str, Any]) -> str:
    return str(element.get("elementName") or element.get("ElementName") or "")


def _times(element: dict[str, Any]) -> list[dict[str, Any]]:
    values = element.get("time") or element.get("Time") or []
    return values if isinstance(values, list) else []


def _temperature_value(item: dict[str, Any]) -> float | None:
    """讀取 36 小時與一般預報格式中的溫度值。"""
    raw: Any = None
    parameter = item.get("parameter")
    if isinstance(parameter, dict):
        raw = parameter.get("parameterName") or parameter.get("ParameterName")

    if raw is None:
        element_value = item.get("elementValue") or item.get("ElementValue")
        if isinstance(element_value, list) and element_value:
            first = element_value[0]
            raw = first.get("value") if isinstance(first, dict) else first
        elif isinstance(element_value, dict):
            raw = element_value.get("value")
        elif element_value is not None:
            raw = element_value

    try:
        return float(raw) if raw not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _date_value(item: dict[str, Any]) -> str | None:
    raw = (
        item.get("startTime")
        or item.get("StartTime")
        or item.get("dataTime")
        or item.get("DataTime")
    )
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        try:
            return pd.to_datetime(raw).date().isoformat()
        except (TypeError, ValueError):
            return None


def parse_temperature_forecasts(payload: dict[str, Any]) -> pd.DataFrame:
    """將 CWA JSON 轉為 regionName/dataDate/mint/maxt DataFrame。"""
    records = payload.get("records")
    if not isinstance(records, dict):
        raise WeatherAPIError("資料缺少 records 節點。")

    rows: list[dict[str, Any]] = []
    for location in _locations_from_records(records):
        region = location.get("locationName") or location.get("LocationName")
        elements = location.get("weatherElement") or location.get("WeatherElement") or []
        if not region or not isinstance(elements, list):
            continue

        by_name = {
            _element_name(element): element
            for element in elements
            if isinstance(element, dict)
        }
        min_times = _times(by_name.get("MinT", {}))
        max_times = _times(by_name.get("MaxT", {}))

        minima = {_date_value(item): _temperature_value(item) for item in min_times}
        maxima = {_date_value(item): _temperature_value(item) for item in max_times}
        for date in sorted((set(minima) & set(maxima)) - {None}):
            mint, maxt = minima[date], maxima[date]
            if mint is None or maxt is None or mint > maxt:
                continue
            rows.append(
                {
                    "regionName": str(region),
                    "dataDate": date,
                    "mint": mint,
                    "maxt": maxt,
                }
            )

    frame = pd.DataFrame(rows, columns=FORECAST_COLUMNS)
    if frame.empty:
        return frame
    frame["dataDate"] = pd.to_datetime(frame["dataDate"], errors="coerce").dt.strftime("%Y-%m-%d")
    frame[["mint", "maxt"]] = frame[["mint", "maxt"]].apply(pd.to_numeric, errors="coerce")
    frame = frame.dropna().drop_duplicates(["regionName", "dataDate"], keep="last")
    return frame.sort_values(["regionName", "dataDate"]).reset_index(drop=True)


def records_from_frame(frame: pd.DataFrame) -> Iterable[tuple[str, str, float, float]]:
    """將 DataFrame 轉為 SQLite executemany 所需的 tuple。"""
    for row in frame.itertuples(index=False):
        yield (str(row.regionName), str(row.dataDate), float(row.mint), float(row.maxt))

