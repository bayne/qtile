import time

import psutil

from libqtile.widget import base

ANIM_INTERVAL = 0.05


class NetSpeed(base.InLoopPollText):
    """Display network speed in MB/s, turning red when high.

    Interpolates between samples at ~20fps for smooth animation.
    """

    defaults = [
        ("warn_threshold_mb", 10, "Turn red above this many MB/s total."),
        ("warn_color", "ff0000", "Foreground color when above threshold."),
        ("update_interval", 1, "Update interval in seconds."),
        ("interface", None, "Interface to monitor, None for all."),
    ]

    def __init__(self, **config):
        base.InLoopPollText.__init__(self, "", **config)
        self.add_defaults(NetSpeed.defaults)
        self._normal_fg = self.foreground
        self._io_prev = psutil.net_io_counters(pernic=False)
        self._prev_down = 0.0
        self._prev_up = 0.0
        self._target_down = 0.0
        self._target_up = 0.0
        self._sample_time = time.monotonic()

    def timer_setup(self):
        super().timer_setup()

    @staticmethod
    def _fmt_speed(bytes_per_sec):
        mb = bytes_per_sec / (1024 * 1024)
        return f"{mb:.1f}MB/s"

    def poll(self):
        cur = psutil.net_io_counters(pernic=False)
        down = (cur.bytes_recv - self._io_prev.bytes_recv) / self.update_interval
        up = (cur.bytes_sent - self._io_prev.bytes_sent) / self.update_interval
        self._io_prev = cur

        self._prev_down = self._target_down
        self._prev_up = self._target_up
        self._target_down = down
        self._target_up = up
        self._sample_time = time.monotonic()
        self.timeout_add(ANIM_INTERVAL, self._animate)

        return self._format(down, up)

    def _format(self, down, up):
        total_mb = (down + up) / (1024 * 1024)
        if total_mb > self.warn_threshold_mb:
            self.foreground = self.warn_color
        else:
            self.foreground = self._normal_fg
        return f"net ↓{self._fmt_speed(down)} ↑{self._fmt_speed(up)}"

    def _animate(self):
        t = (time.monotonic() - self._sample_time) / self.update_interval
        if t >= 1.0:
            return
        display_down = self._prev_down + (self._target_down - self._prev_down) * t
        display_up = self._prev_up + (self._target_up - self._prev_up) * t
        self.update(self._format(display_down, display_up))
        self.timeout_add(ANIM_INTERVAL, self._animate)
