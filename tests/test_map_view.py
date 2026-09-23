import unittest

import pandas as pd

from map_view import create_weather_map, temperature_color


class MapViewTests(unittest.TestCase):
    def test_temperature_colors(self) -> None:
        self.assertEqual(temperature_color(19), "blue")
        self.assertEqual(temperature_color(20), "green")
        self.assertEqual(temperature_color(25), "orange")
        self.assertEqual(temperature_color(30), "red")

    def test_map_contains_known_region(self) -> None:
        frame = pd.DataFrame([{
            "regionName": "臺北市",
            "dataDate": "2026-04-14",
            "mint": 20,
            "maxt": 30,
        }])
        html = create_weather_map(frame).get_root().render()
        self.assertIn("臺北市", html)


if __name__ == "__main__":
    unittest.main()

