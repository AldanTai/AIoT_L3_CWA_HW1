import unittest
from unittest.mock import Mock, patch

from fetch_weather import WeatherAPIError, fetch_weather_data, parse_temperature_forecasts


SAMPLE_PAYLOAD = {
    "success": "true",
    "records": {
        "location": [
            {
                "locationName": "臺北市",
                "weatherElement": [
                    {
                        "elementName": "MinT",
                        "time": [
                            {
                                "startTime": "2026-04-14 06:00:00",
                                "parameter": {"parameterName": "20"},
                            }
                        ],
                    },
                    {
                        "elementName": "MaxT",
                        "time": [
                            {
                                "startTime": "2026-04-14 06:00:00",
                                "parameter": {"parameterName": "30"},
                            }
                        ],
                    },
                ],
            }
        ]
    },
}


class ParseForecastTests(unittest.TestCase):
    def test_parses_minimum_and_maximum_temperature(self) -> None:
        frame = parse_temperature_forecasts(SAMPLE_PAYLOAD)
        self.assertEqual(frame.to_dict("records"), [{
            "regionName": "臺北市",
            "dataDate": "2026-04-14",
            "mint": 20.0,
            "maxt": 30.0,
        }])

    def test_missing_maximum_temperature_returns_empty_frame(self) -> None:
        payload = {
            "records": {
                "location": [{
                    "locationName": "臺北市",
                    "weatherElement": [SAMPLE_PAYLOAD["records"]["location"][0]["weatherElement"][0]],
                }]
            }
        }
        self.assertTrue(parse_temperature_forecasts(payload).empty)

    def test_invalid_temperature_is_ignored(self) -> None:
        payload = SAMPLE_PAYLOAD.copy()
        payload = {"records": {"location": [dict(SAMPLE_PAYLOAD["records"]["location"][0])]}}
        elements = [dict(item) for item in payload["records"]["location"][0]["weatherElement"]]
        elements[0] = dict(elements[0])
        elements[0]["time"] = [{"startTime": "2026-04-14", "parameter": {"parameterName": "35"}}]
        payload["records"]["location"][0]["weatherElement"] = elements
        self.assertTrue(parse_temperature_forecasts(payload).empty)


class FetchWeatherTests(unittest.TestCase):
    def test_rejects_empty_api_key(self) -> None:
        with self.assertRaises(WeatherAPIError):
            fetch_weather_data("")

    @patch("fetch_weather.requests.get")
    def test_fetches_valid_payload(self, get: Mock) -> None:
        response = Mock()
        response.json.return_value = SAMPLE_PAYLOAD
        response.raise_for_status.return_value = None
        get.return_value = response
        self.assertEqual(fetch_weather_data("secret"), SAMPLE_PAYLOAD)
        get.assert_called_once()


if __name__ == "__main__":
    unittest.main()

