import psutil

from libqtile.widget import base


class NetSpeed(base.InLoopPollText):
    """Display network speed in KB/s or MB/s, turning red when high."""

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
        self._prev = psutil.net_io_counters(pernic=False)

    @staticmethod
    def _fmt_speed(bytes_per_sec):
        kb = bytes_per_sec / 1024
        if kb >= 1024:
            return f"{kb / 1024:.1f}MB/s"
        return f"{kb:.0f}KB/s"

    def poll(self):
        cur = psutil.net_io_counters(pernic=False)
        down = (cur.bytes_recv - self._prev.bytes_recv) / self.update_interval
        up = (cur.bytes_sent - self._prev.bytes_sent) / self.update_interval
        self._prev = cur

        total_mb = (down + up) / (1024 * 1024)
        if total_mb > self.warn_threshold_mb:
            self.foreground = self.warn_color
        else:
            self.foreground = self._normal_fg

        return f"net ↓{self._fmt_speed(down)} ↑{self._fmt_speed(up)}"
