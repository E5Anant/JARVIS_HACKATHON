from datetime import datetime
import pytz
from unisonai import BaseTool, Field

class TimezoneCurrentTime(BaseTool):
    name = "TimezoneCurrentTime"
    description = "Get the current date and time for a given timezone (e.g., 'Asia/Kolkata')"
    params = [
        Field("timezone", "IANA timezone string, e.g. 'Asia/Kolkata'")
    ]

    def _run(self, timezone: str):
        try:
            tz = pytz.timezone(timezone)
        except Exception as e:
            return {"error": f"Invalid timezone '{timezone}': {e}"}

        now = datetime.now(tz)
        formatted = now.strftime("%Y-%m-%d %H:%M:%S %Z%z")
        return {"timezone": timezone, "current_time": formatted}
