import requests
from unisonai import BaseTool, Field

class UserLocation(BaseTool):
    name = "UserLocation"
    description = "Get the user's general location (city, region, country, lat/lon) based on IP"
    params = []  # no params needed from the user

    def _run(self):
        try:
            resp = requests.get("https://ipapi.co/json/")
            resp.raise_for_status()
            data = resp.json()
            # Extract only useful fields
            result = {
                "ip": data.get("ip"),
                "city": data.get("city"),
                "region": data.get("region"),
                "country": data.get("country_name"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "timezone": data.get("timezone"),
            }
            return result
        except Exception as e:
            return {"error": str(e)}
