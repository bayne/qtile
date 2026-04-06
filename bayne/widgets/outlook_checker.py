import os
from datetime import datetime, timedelta

import icalendar
import pytz
import recurring_ical_events
import requests

from libqtile.log_utils import logger
from libqtile.widget.base import BackgroundPoll


class OutlookChecker(BackgroundPoll):
    defaults = [
        ("update_interval", 1, "Update time in seconds."),
        ("request_update_interval", 600, "Request update time in seconds."),
        ("timezone", pytz.timezone("America/Los_Angeles"), "Timezone"),
        ("foreground", "33ff33", "foreground color"),
        ("foreground_active", "ff8888", "foreground color when meeting is active"),
        ("foreground_not_today", "8CFFF0", "foreground color when meeting is not today"),
        ("lookahead", 7, "days to look ahead in the calendar"),
    ]

    def __init__(self, **config):
        BackgroundPoll.__init__(self, "", **config)
        self.add_defaults(OutlookChecker.defaults)
        self.markup = False
        self.foreground_inactive = self.foreground
        self.last_update = datetime.now(self.timezone)
        self.cached_calendar = None
        self.force_update()

    def _normalize_dt(self, dt) -> datetime:
        """Convert a date or datetime to a timezone-aware datetime."""
        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                return self.timezone.localize(dt)
            return dt.astimezone(self.timezone)
        # date (all-day event) — treat as start of day
        return self.timezone.localize(datetime.combine(dt, datetime.min.time()))

    def _poll(self):
        now: datetime = datetime.now(self.timezone)

        if (
            self.cached_calendar is None
            or self.last_update + timedelta(seconds=self.request_update_interval) < now
        ):
            response = requests.get(os.environ["OUTLOOK_ICS_URL"])
            self.cached_calendar = icalendar.Calendar.from_ical(response.text)
            self.last_update = now

        window_end = now + timedelta(days=self.lookahead)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        events = recurring_ical_events.of(self.cached_calendar).between(today_start, window_end)

        # Exclude canceled events
        events = [
            e
            for e in events
            if not str(e.get("SUMMARY", "")).startswith("Canceled:")
        ]

        # Filter: event hasn't ended yet
        events = [
            e
            for e in events
            if self._normalize_dt(e["DTEND"].dt) > now
        ]

        if not events:
            return "No next event"

        # Find next event by start time
        next_event = min(events, key=lambda e: self._normalize_dt(e["DTSTART"].dt))

        subject = str(next_event.get("SUMMARY", "unknown"))
        start = self._normalize_dt(next_event["DTSTART"].dt)
        event_end = self._normalize_dt(next_event["DTEND"].dt)
        day = datetime.strftime(start, "%a")
        start_time = datetime.strftime(start, "%-I:%M %p")
        end_time = datetime.strftime(event_end, "%-I:%M %p")

        if now.date() < start.date():
            self.foreground = self.foreground_not_today
        elif start <= now <= event_end:
            self.foreground = self.foreground_active
        else:
            self.foreground = self.foreground_inactive

        return f"[[{subject} {day} @ {start_time}-{end_time}]]"

    async def apoll(self):
        try:
            return self._poll()
        except Exception:
            logger.exception("Failed to poll for outlook events")
            return "Error something went wrong"

