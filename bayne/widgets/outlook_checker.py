import sys
from datetime import datetime, timedelta

from libqtile import widget
from libqtile.log_utils import logger

import subprocess, requests, pytz


def _get_password(entry):
    result = subprocess.run(["pass", entry], capture_output=True, text=True, check=True)
    return result.stdout.strip()

class OutlookChecker(widget.base.ThreadPoolText):
    SHOW_AS_RANK = {
        "busy": 0,
        "tentative": 1,
    }

    defaults = [
        ("update_interval", 1, "Update time in seconds."),
        ("request_update_interval", 600, "Request update time in seconds."),
        ("timezone", pytz.timezone('America/Los_Angeles'), "Timezone"),
        ("foreground", "33ff33", "foreground color"),
        ("foreground_active", "ff8888", "foreground color when meeting is active"),
        ("foreground_not_today", "8CFFF0", "foreground color when meeting is not today"),
    ]

    def __init__(self, **config):
        widget.base.ThreadPoolText.__init__(self, "", **config)
        self.add_defaults(OutlookChecker.defaults)
        self.markup = False
        self.foreground_inactive = self.foreground
        self.url = _get_password("outlook-event-url")
        self.last_update = datetime.now(self.timezone)
        self.previous_response = None
        self.force_update()

    def _show_as_rank(self, show_as: str) -> int:
        if show_as not in self.SHOW_AS_RANK:
            return sys.maxsize
        return self.SHOW_AS_RANK[show_as]

    def _get_datetime(self, date_string: str):
        return pytz.utc.localize(datetime.fromisoformat(date_string)).astimezone(self.timezone)

    def _poll(self):
        now: datetime = datetime.now(self.timezone)

        if not self.previous_response or self.last_update + timedelta(seconds=self.request_update_interval) < now:
            response = requests.get(self.url)
            self.previous_response = response
            self.last_update = now
        else:
            response = self.previous_response

        events = response.json()['value']
        events = filter(lambda e: e['isReminderOn'] or e['showAs'] == 'busy', events)
        events = filter(lambda e: 'subject' not in e or not e['subject'].startswith('Canceled:'), events)
        events = sorted(events, key=lambda e: self._show_as_rank(e['showAs']))
        events = filter(lambda e: self._get_datetime(e['start']) > now or now <= self._get_datetime(e['end']), events)
        next_event = min(events, default={}, key=lambda e: e['start'])
        if not next_event:
            return "No next event"

        subject, start, end = next_event.get('subject', 'unknown'), next_event['start'], next_event['end']
        start: datetime = self._get_datetime(start)
        end: datetime = self._get_datetime(end)
        day = datetime.strftime(start, "%a")
        start_time = datetime.strftime(start, "%-I:%M %p")
        end_time = datetime.strftime(end, "%-I:%M %p")

        if now.day < start.day:
            self.foreground = self.foreground_not_today
        elif start <= now <= end:
            self.foreground = self.foreground_active
        else:
            self.foreground = self.foreground_inactive

        return f"[[{subject} {day} @ {start_time}-{end_time}]]"

    def poll(self):
        try:
            return self._poll()
        except Exception as e:
            logger.exception("Failed to poll for outlook events")
            return f"Error something went wrong"

