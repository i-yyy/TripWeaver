from __future__ import annotations

import unittest

from app.services.amap_service import AmapService


SEARCH_RESPONSE = """
[TOOL_CALL_RESULT:amap_maps_text_search:keywords=museum,city=beijing]
{
  "status": "1",
  "count": "2",
  "info": "OK",
  "infocode": "10000",
  "pois": [
    {
      "id": "B000A83B54",
      "name": "Palace Museum",
      "type": "museum",
      "address": "4 Jingshan Front Street, Dongcheng District",
      "location": "116.397026,39.918058",
      "cityname": "Beijing",
      "adname": "Dongcheng"
    },
    {
      "id": "B000A8UIN8",
      "name": "National Museum of China",
      "type": "museum",
      "address": "16 East Changan Street, Dongcheng District",
      "location": "116.401394,39.904844",
      "cityname": "Beijing",
      "adname": "Dongcheng"
    }
  ]
}
[/TOOL_CALL_RESULT]
"""

WEATHER_RESPONSE = """
[TOOL_RESPONSE:{"status": "1", "count": "1", "info": "OK", "infocode": "10000", "lives": [{"province": "Beijing", "city": "Beijing", "adcode": "110000", "weather": "Sunny", "temperature": "27", "winddirection": "Southwest", "windpower": "<=3", "humidity": "19", "reporttime": "2024-05-17 14:49:15"}]}]
"""


class FakeMCPTool:
    def run(self, payload):
        tool_name = payload["tool_name"]
        if tool_name == "maps_text_search":
            return SEARCH_RESPONSE
        if tool_name == "maps_weather":
            return WEATHER_RESPONSE
        raise AssertionError(f"Unexpected tool: {tool_name}")


class AmapServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = AmapService(mcp_tool=FakeMCPTool())

    def test_search_poi_parses_structured_pois(self) -> None:
        pois = self.service.search_poi("museum", "beijing")

        self.assertEqual(len(pois), 2)
        self.assertEqual(pois[0].name, "Palace Museum")
        self.assertEqual(pois[0].location.longitude, 116.397026)
        self.assertEqual(pois[1].address, "16 East Changan Street, Dongcheng District")

    def test_get_weather_parses_live_weather(self) -> None:
        weather = self.service.get_weather("beijing")

        self.assertEqual(len(weather), 1)
        self.assertEqual(weather[0].date, "2024-05-17")
        self.assertEqual(weather[0].day_weather, "Sunny")
        self.assertEqual(weather[0].day_temp, 27)


if __name__ == "__main__":
    unittest.main()
