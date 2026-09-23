"""Taiwan Weather Forecast Streamlit 應用程式。"""

from __future__ import annotations

import os
import time

import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from database import (
    forecasts_for_date,
    forecasts_for_region,
    last_updated,
    list_dates,
    list_regions,
    upsert_forecasts,
)
from fetch_weather import (
    DEFAULT_DATASET_ID,
    WeatherAPIError,
    fetch_weather_data,
    parse_temperature_forecasts,
    records_from_frame,
)
from map_view import create_weather_map


st.set_page_config(page_title="Taiwan Weather Forecast", page_icon="🌤️", layout="wide")


def get_api_key() -> str:
    """優先讀取 Streamlit Secrets，找不到時使用環境變數。"""
    try:
        value = st.secrets.get("CWA_API_KEY", "")
    except (FileNotFoundError, KeyError):
        value = ""
    return str(value or os.getenv("CWA_API_KEY", "")).strip()


def refresh_weather(api_key: str) -> int:
    payload = fetch_weather_data(api_key, DEFAULT_DATASET_ID)
    frame = parse_temperature_forecasts(payload)
    if frame.empty:
        raise WeatherAPIError("API 回應中沒有可用的最低與最高氣溫資料。")
    return upsert_forecasts(records_from_frame(frame))


def render_sidebar() -> None:
    st.sidebar.header("資料控制")
    st.sidebar.caption(f"CWA 資料集：`{DEFAULT_DATASET_ID}`")
    api_key = get_api_key()
    if api_key:
        st.sidebar.success("已載入 CWA API Key")
    else:
        st.sidebar.warning("尚未設定 CWA API Key")
        st.sidebar.caption("請複製 `.streamlit/secrets.toml.example` 並填入授權碼。")
        return

    last_refresh = st.session_state.get("cwa_last_refresh", 0.0)
    if time.monotonic() - last_refresh < 600:
        st.sidebar.caption("資料每 10 分鐘自動檢查更新。")
        return

    st.session_state["cwa_last_refresh"] = time.monotonic()
    try:
        with st.spinner("正在下載並更新天氣資料…"):
            count = refresh_weather(api_key)
        st.cache_data.clear()
        st.sidebar.success(f"已自動更新 {count} 筆氣溫預報。")
    except WeatherAPIError as exc:
        st.sidebar.error(str(exc))
    except Exception as exc:  # UI 邊界：避免資料庫問題讓整頁中斷
        st.sidebar.error(f"自動更新資料失敗：{exc}")


@st.cache_data(ttl=60)
def cached_regions() -> list[str]:
    return list_regions()


@st.cache_data(ttl=60)
def cached_dates() -> list[str]:
    return list_dates()


@st.cache_data(ttl=60)
def cached_region_forecasts(region: str) -> pd.DataFrame:
    return forecasts_for_region(region)


@st.cache_data(ttl=60)
def cached_date_forecasts(data_date: str) -> pd.DataFrame:
    return forecasts_for_date(data_date)


def render_dashboard() -> None:
    st.title("Taiwan Weather Forecast")
    st.caption("中央氣象署 7 日氣溫預報 | CWA Open Data")

    updated = last_updated()
    if updated:
        st.caption(f"資料庫最後更新：{updated} UTC · 頁面每 10 分鐘檢查新資料")

    regions = cached_regions()
    dates = cached_dates()
    if not regions:
        st.info("資料庫目前沒有預報資料。請先設定 API Key，再按左側的「更新 CWA 預報」。")
        return

    if not dates:
        st.info("目前沒有可顯示的預報日期。")
        return

    selected_date = st.sidebar.selectbox("預報日期", dates, index=len(dates) - 1)
    source_frame = cached_date_forecasts(selected_date).copy()
    source_frame["平均溫"] = (source_frame["mint"] + source_frame["maxt"]) / 2
    source_frame["日夜溫差"] = source_frame["maxt"] - source_frame["mint"]

    selected_regions = st.sidebar.multiselect(
        "縣市篩選",
        source_frame["regionName"].tolist(),
        placeholder="顯示全部縣市",
    )
    temperature_bounds = (
        int(source_frame["平均溫"].min()),
        int(source_frame["平均溫"].max()) + 1,
    )
    temperature_range = st.sidebar.slider(
        "平均氣溫範圍 (°C)",
        min_value=temperature_bounds[0],
        max_value=temperature_bounds[1],
        value=temperature_bounds,
    )
    display_mode = st.sidebar.segmented_control(
        "地圖模式", ["標記", "熱度圖"], default="標記"
    )
    tile_style = st.sidebar.segmented_control(
        "底圖", ["深色", "街道", "淺色"], default="深色"
    )
    show_labels = st.sidebar.toggle("顯示溫度標籤", value=True)

    filtered = source_frame[
        source_frame["平均溫"].between(*temperature_range, inclusive="both")
    ]
    if selected_regions:
        filtered = filtered[filtered["regionName"].isin(selected_regions)]

    if filtered.empty:
        st.warning("目前的篩選條件沒有符合的縣市。")
        return

    hottest = filtered.loc[filtered["maxt"].idxmax()]
    coldest = filtered.loc[filtered["mint"].idxmin()]
    widest = filtered.loc[filtered["日夜溫差"].idxmax()]
    metric_columns = st.columns(4)
    metric_columns[0].metric("顯示縣市", f"{len(filtered)} 個")
    metric_columns[1].metric(f"最高溫 · {hottest['regionName']}", f"{hottest['maxt']:g}°C")
    metric_columns[2].metric(f"最低溫 · {coldest['regionName']}", f"{coldest['mint']:g}°C")
    metric_columns[3].metric(
        f"最大溫差 · {widest['regionName']}", f"{widest['日夜溫差']:g}°C"
    )

    map_tab, trend_tab, data_tab = st.tabs(["全台地圖", "縣市趨勢", "預報資料"])

    with map_tab:
        st_folium(
            create_weather_map(
                filtered,
                tile_style=tile_style or "深色",
                display_mode=display_mode or "標記",
                show_labels=show_labels,
            ),
            width=None,
            height=610,
            returned_objects=[],
            use_container_width=True,
        )

    with trend_tab:
        region = st.selectbox("選擇縣市", regions)
        region_frame = cached_region_forecasts(region)
        chart_frame = region_frame.copy()
        chart_frame["dataDate"] = pd.to_datetime(chart_frame["dataDate"])
        chart_frame = chart_frame.sort_values("dataDate").set_index("dataDate")
        st.subheader(f"{region}氣溫趨勢")
        st.line_chart(
            chart_frame.rename(columns={"mint": "最低溫 °C", "maxt": "最高溫 °C"}),
            y=["最低溫 °C", "最高溫 °C"],
            color=["#1677ff", "#ef4444"],
        )
        st.dataframe(
            region_frame.rename(
                columns={"dataDate": "日期", "mint": "最低溫 (°C)", "maxt": "最高溫 (°C)"}
            ),
            hide_index=True,
            width="stretch",
        )

    with data_tab:
        table = filtered.sort_values("maxt", ascending=False).rename(
            columns={
                "regionName": "縣市",
                "dataDate": "日期",
                "mint": "最低溫 (°C)",
                "maxt": "最高溫 (°C)",
            }
        )
        st.dataframe(table, hide_index=True, width="stretch")


render_sidebar()
render_dashboard()

