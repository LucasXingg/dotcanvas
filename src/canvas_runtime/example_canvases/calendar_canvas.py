from src.canvas_runtime.base_canvas import _BaseCanvas
from src.canvas_runtime.package_manager import install_package

from PIL import Image, ImageDraw, ImageFont

class Canvas(_BaseCanvas):

    ID = "calendar_canvas"

    @classmethod
    def render(cls, params: dict | None = None) -> Image.Image:
        return cls._render(CONFIG, params=params)

    @staticmethod
    def event_text(params: dict | None = None) -> dict:
        install_package("caldav", "icalendar")

        from caldav import DAVClient
        from icalendar import Calendar
        from datetime import datetime, timedelta, timezone

        username = "example@icloud.com" # replace with your Apple ID email
        password = "abcd-abcd-abcd-abcd"  # App-specific password
        # (https://account.apple.com/account/manage -> App-Specific Passwords)

        if username == "example@icloud.com":
            return {
                "type": "TextView",
                "location_x": 16,
                "location_y": 52,
                "width": 120,
                "height": 40,
                "text": "\nNo Apple Account info",
                "fill": "#111827",
                "font_size": 15,
            }

        client = DAVClient(
            url="https://caldav.icloud.com/",
            username=username,
            password=password
        )

        # === connect ===
        principal = client.principal()

        # Get all calendars
        calendars = principal.calendars()
        calendar = next(
            (cal for cal in calendars if cal.name == "School"),
            None
        )

        # === search time window ===
        now = datetime.now(timezone.utc)
        window_end = now + timedelta(days=7)  # search one week ahead

        if calendar is not None:
            events = calendar.date_search(start=now, end=window_end)
        else:
            events = []

        next_event = None
        next_start = None

        for event in events:
            cal = Calendar.from_ical(event.data)
            for component in cal.walk():
                if component.name != "VEVENT":
                    continue
                start = component.get("dtstart").dt
                end = component.get("dtend").dt
                summary = component.get("summary")

                # ensure datetimes are timezone-aware
                if start.tzinfo is None:
                    start = start.replace(tzinfo=timezone.utc)

                if start > now:
                    if next_event is None or start < next_start:
                        next_event = (summary, start, end)
                        next_start = start

        # === return result ===
        if next_event:
            name, start, end = next_event
            result = f"Next Event:\n{name if len(name) < 15 else name[:10]}\n{str(start)[5:10]}\n{str(start)[11:16]} - {str(end)[11:16]}"
        else:
            result = "No Event This Week"


        return {
            "type": "TextView",
            "location_x": 16,
            "location_y": 52,
            "width": 120,
            "height": 40,
            "text": result,
            "fill": "#111827",
            "font_size": 15,
        }


    @staticmethod
    def Weather_view(params: dict | None = None) -> dict:
        import requests

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": 40.8, # New York
            "longitude": -73.9,
            "hourly": "temperature_2m",
            "forecast_days": 1,
            "timezone": "auto"
        }
        resp = requests.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        temps = data["hourly"]["temperature_2m"]
        temp = f"{min(temps)}\u2103-{max(temps)}\u2103"

        return {
            "type": "TextView",
            "location_x": 160,
            "location_y": 115,
            "width": 120,
            "height": 40,
            "text": temp,
            "fill": "#111827",
            "font_size": 18,
        }


    @staticmethod
    def date_view(params: dict | None = None) -> dict:
        from datetime import datetime

        # Current date
        today = datetime.today()
        current_mmdd = today.strftime("%m-%d")


        return {
            "type": "TextView",
            "location_x": 233,
            "location_y": 16,
            "width": 120,
            "height": 40,
            "text": current_mmdd,
            "fill": "#111827",
            "font_size": 18,
        }


    @staticmethod
    def icon_view(params: dict | None = None) -> dict:
        import random

        LUCIDE_ICONS_SCHOOL = [
            "book", "graduation-cap", "school", "library", "pencil",
            "notebook-text", "pen-line", "ruler", "microscope", "atom",
            "calendar", "calendar-days", "clock", "alarm-clock", "hourglass",
            "list-todo", "check-square", "users", "chalkboard", "presentation",
            "coffee", "bus"
        ]

        icon = random.choice(LUCIDE_ICONS_SCHOOL)

        return {
            "type": "LucideIconView",
            "location_x": 222,
            "location_y": 52,
            "width": 58,
            "height": 58,
            "icon": icon,
            "color": "#F59E0B",
            "background_fill": "#FEF3C7",
        }


    @staticmethod
    def head_view(params: dict | None = None) -> dict:
        from datetime import datetime

        # Current date
        today = datetime.today()

        # Parse the given start date
        start_date = params.get("start_date") if params.get("start_date") else "2025-09-01"
        start_date_datetime = datetime.strptime(start_date, "%Y-%m-%d")

        # Calculate the difference in weeks (rounded up)
        days_diff = (today - start_date_datetime).days
        week_num = days_diff // 7 + 1  # +1 so the start week counts as week 1


        return {
            "type": "TextView",
            "location_x": 16,
            "location_y": 16,
            "width": 120,
            "height": 40,
            "text": f"Week {week_num} of Semester",
            "fill": "#111827",
            "font_size": 18,
        }


CONFIG = {
    "name": "calendar_canvas",
    "views": {
        "event_text": Canvas.event_text,
        "Weather_view": Canvas.Weather_view,
        "date_view": Canvas.date_view,
        "icon_view": Canvas.icon_view,
        "head_view": Canvas.head_view,
    }  # view_id -> view_builder
}

if __name__ == "__main__":
    img = Canvas.render()
    img.show()
