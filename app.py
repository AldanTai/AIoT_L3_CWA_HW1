"""Taiwan Weather Forecast Streamlit 應用程式。"""

from __future__ import annotations

import os

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

    if st.sidebar.button("更新 CWA 預報", type="primary", use_container_width=True):
        if not api_key:
            st.sidebar.error("請先設定 CWA API Key。")
            return
        try:
            with st.spinner("正在下載並更新天氣資料…"):
                count = refresh_weather(api_key)
            st.sidebar.success(f"已處理 {count} 筆氣溫預報。")
            st.cache_data.clear()
            st.rerun()
        except WeatherAPIError as exc:
            st.sidebar.error(str(exc))
        except Exception as exc:  # UI 邊界：避免資料庫問題讓整頁中斷
            st.sidebar.error(f"更新資料失敗：{exc}")


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
    st.title("🌤️ Taiwan Weather Forecast")
    st.caption("中央氣象署開放資料 × Python × SQLite × Streamlit")

    updated = last_updated()
    if updated:
        st.caption(f"資料庫最後更新：{updated} UTC")

    regions = cached_regions()
    dates = cached_dates()
    if not regions:
        st.info("資料庫目前沒有預報資料。請先設定 API Key，再按左側的「更新 CWA 預報」。")
        return

    region = st.selectbox("選擇地區", regions)
    region_frame = cached_region_forecasts(region)
    if region_frame.empty:
        st.warning("所選地區目前沒有資料。")
    else:
        chart_frame = region_frame.copy()
        chart_frame["dataDate"] = pd.to_datetime(chart_frame["dataDate"])
        chart_frame = chart_frame.sort_values("dataDate").set_index("dataDate")

        st.subheader(f"{region}氣溫趨勢")
        st.line_chart(
            chart_frame.rename(columns={"mint": "最低溫 °C", "maxt": "最高溫 °C"}),
            y=["最低溫 °C", "最高溫 °C"],
            color=["#1677ff", "#ef4444"],
        )
        display_frame = region_frame.rename(
            columns={"dataDate": "日期", "mint": "最低溫（°C）", "maxt": "最高溫（°C）"}
        )
        st.dataframe(display_frame, hide_index=True, use_container_width=True)

    if dates:
        st.divider()
        st.subheader("台灣氣溫地圖")
        selected_date = st.selectbox("選擇地圖日期", dates, index=len(dates) - 1)
        map_frame = cached_date_forecasts(selected_date)
        if map_frame.empty:
            st.warning("所選日期目前沒有地圖資料。")
        else:
            st_folium(
                create_weather_map(map_frame),
                width=None,
                height=560,
                returned_objects=[],
                use_container_width=True,
            )


render_sidebar()
render_dashboard()

