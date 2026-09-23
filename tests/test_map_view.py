import unittest

import pandas as pd

from map_view import create_weather_map, temperature_color


class MapViewTests(unittest.TestCase):
    def test_temperature_colors(self) -> None:
        self.assertEqual(temperature_color(9), "#2b6cb0")
        self.assertEqual(temperature_color(14), "#3182ce")
        self.assertEqual(temperature_color(19), "#38a169")
        self.assertEqual(temperature_color(24), "#ecc94b")
        self.assertEqual(temperature_color(29), "#ed8936")
        self.assertEqual(temperature_color(34), "#e53e3e")
        self.assertEqual(temperature_color(35), "#9b2c2c")

    def test_map_contains_known_region(self) -> None:
        frame = pd.DataFrame([{
            "regionName": "臺北市",
            "dataDate": "2026-04-14",
            "mint": 20,
            "maxt": 30,
        }])
        html = create_weather_map(frame).get_root().render()
        self.assertIn("臺北市", html)
        self.assertIn("平均氣溫", html)

    def test_heatmap_mode(self) -> None:
        frame = pd.DataFrame([{
            "regionName": "臺北市",
            "dataDate": "2026-04-14",
            "mint": 20,
            "maxt": 30,
        }])
        html = create_weather_map(frame, display_mode="熱度圖").get_root().render()
        self.assertIn("L.heatLayer", html)


if __name__ == "__main__":
    unittest.main()

