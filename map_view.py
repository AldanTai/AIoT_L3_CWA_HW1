"""Folium 台灣天氣地圖。"""

from __future__ import annotations

import folium
import pandas as pd
from folium.plugins import HeatMap


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
    if value < 10:
        return "#2b6cb0"
    if value < 15:
        return "#3182ce"
    if value < 20:
        return "#38a169"
    if value < 25:
        return "#ecc94b"
    if value < 30:
        return "#ed8936"
    if value < 35:
        return "#e53e3e"
    return "#9b2c2c"


TILE_STYLES: dict[str, tuple[str, str]] = {
    "深色": (
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/"
        "tile/{z}/{y}/{x}",
        "Tiles &copy; Esri",
    ),
    "街道": ("OpenStreetMap", "OpenStreetMap"),
    "淺色": (
        "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_"
        "Base/MapServer/tile/{z}/{y}/{x}",
        "Tiles &copy; Esri",
    ),
}


def _temperature_legend() -> str:
    stops = "#2b6cb0,#3182ce,#38a169,#ecc94b,#ed8936,#e53e3e,#9b2c2c"
    return f"""
    <div style="position:fixed;right:16px;bottom:26px;z-index:9999;width:220px;
      padding:10px 12px;background:rgba(15,23,42,.92);color:white;border-radius:6px;
      box-shadow:0 4px 14px rgba(0,0,0,.25);font:12px sans-serif">
      <div style="font-weight:700;margin-bottom:7px">平均氣溫 (°C)</div>
      <div style="height:9px;border-radius:4px;background:linear-gradient(to right,{stops})"></div>
      <div style="display:flex;justify-content:space-between;margin-top:4px;color:#d1d5db">
        <span>&lt;10</span><span>15</span><span>20</span><span>25</span><span>30</span><span>35+</span>
      </div>
    </div>
    """


def create_weather_map(
    frame: pd.DataFrame,
    tile_style: str = "深色",
    display_mode: str = "標記",
    show_labels: bool = True,
) -> folium.Map:
    """由指定日期的預報 DataFrame 建立台灣地圖。"""
    tiles, attribution = TILE_STYLES.get(tile_style, TILE_STYLES["深色"])
    weather_map = folium.Map(
        location=[23.7, 121.0],
        zoom_start=7,
        tiles=tiles,
        attr=attribution,
        control_scale=True,
    )
    heat_points: list[list[float]] = []
    for row in frame.itertuples(index=False):
        coordinates = REGION_COORDINATES.get(str(row.regionName))
        if coordinates is None:
            continue
        average = (float(row.mint) + float(row.maxt)) / 2
        heat_weight = max(0.0, min(1.0, (average + 10) / 50))
        heat_points.append([coordinates[0], coordinates[1], heat_weight])
        popup = (
            f"<strong>{row.regionName}</strong><br>"
            f"日期：{row.dataDate}<br>"
            f"最低溫：{float(row.mint):g}°C<br>"
            f"最高溫：{float(row.maxt):g}°C<br>"
            f"平均溫：{average:g}°C<br>"
            f"日夜溫差：{float(row.maxt) - float(row.mint):g}°C"
        )
        if display_mode == "標記":
            folium.CircleMarker(
                location=coordinates,
                radius=10,
                color="white",
                weight=2,
                fill=True,
                fill_color=temperature_color(average),
                fill_opacity=0.9,
                tooltip=f"{row.regionName}：{float(row.mint):g}–{float(row.maxt):g}°C",
                popup=folium.Popup(popup, max_width=260),
            ).add_to(weather_map)
            if show_labels:
                folium.Marker(
                    coordinates,
                    icon=folium.DivIcon(
                        icon_size=(54, 20),
                        icon_anchor=(-12, 10),
                        html=(
                            '<div style="color:white;font:700 12px sans-serif;'
                            'text-shadow:0 1px 3px #000;white-space:nowrap">'
                            f"{average:g}°</div>"
                        ),
                    ),
                ).add_to(weather_map)

    if display_mode == "熱度圖" and heat_points:
        HeatMap(
            heat_points,
            min_opacity=0.35,
            radius=34,
            blur=26,
            gradient={
                0.2: "#2b6cb0",
                0.4: "#38a169",
                0.6: "#ecc94b",
                0.8: "#ed8936",
                1.0: "#9b2c2c",
            },
        ).add_to(weather_map)

    weather_map.get_root().html.add_child(folium.Element(_temperature_legend()))
    return weather_map
