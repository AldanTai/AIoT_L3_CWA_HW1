"""Folium 台灣天氣地圖。"""

from __future__ import annotations

import folium
import pandas as pd


REGION_COORDINATES: dict[str, tuple[float, float]] = {
    "基隆市": (25.1276, 121.7392),
    "臺北市": (25.0375, 121.5637),
    "台北市": (25.0375, 121.5637),
    "新北市": (25.0169, 121.4628),
    "桃園市": (24.9937, 121.3010),
    "新竹市": (24.8138, 120.9675),
    "新竹縣": (24.8387, 121.0177),
    "苗栗縣": (24.5602, 120.8214),
    "臺中市": (24.1477, 120.6736),
    "台中市": (24.1477, 120.6736),
    "彰化縣": (24.0756, 120.5440),
    "南投縣": (23.9609, 120.9719),
    "雲林縣": (23.7092, 120.4313),
    "嘉義市": (23.4801, 120.4491),
    "嘉義縣": (23.4518, 120.2555),
    "臺南市": (22.9999, 120.2270),
    "台南市": (22.9999, 120.2270),
    "高雄市": (22.6273, 120.3014),
    "屏東縣": (22.5519, 120.5488),
    "宜蘭縣": (24.7021, 121.7378),
    "花蓮縣": (23.9911, 121.6112),
    "臺東縣": (22.7554, 121.1500),
    "台東縣": (22.7554, 121.1500),
    "澎湖縣": (23.5712, 119.5793),
    "金門縣": (24.4494, 118.3767),
    "連江縣": (26.1605, 119.9517),
}


def temperature_color(value: float) -> str:
    if value < 20:
        return "blue"
    if value < 25:
        return "green"
    if value < 30:
        return "orange"
    return "red"


def create_weather_map(frame: pd.DataFrame) -> folium.Map:
    """由指定日期的預報 DataFrame 建立台灣地圖。"""
    weather_map = folium.Map(location=[23.7, 121.0], zoom_start=7, tiles="OpenStreetMap")
    for row in frame.itertuples(index=False):
        coordinates = REGION_COORDINATES.get(str(row.regionName))
        if coordinates is None:
            continue
        average = (float(row.mint) + float(row.maxt)) / 2
        popup = (
            f"<strong>{row.regionName}</strong><br>"
            f"日期：{row.dataDate}<br>"
            f"最低溫：{float(row.mint):g}°C<br>"
            f"最高溫：{float(row.maxt):g}°C"
        )
        folium.CircleMarker(
            location=coordinates,
            radius=9,
            color="white",
            weight=2,
            fill=True,
            fill_color=temperature_color(average),
            fill_opacity=0.85,
            tooltip=f"{row.regionName}：{float(row.mint):g}–{float(row.maxt):g}°C",
            popup=folium.Popup(popup, max_width=250),
        ).add_to(weather_map)
    return weather_map
