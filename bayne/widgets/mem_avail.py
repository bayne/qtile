import psutil

from libqtile.widget import base


class MemAvail(base.InLoopPollText):
    """Display available memory in GB, turning red when low."""

    defaults = [
        ("warn_threshold_gb", 8, "Turn red below this many GB available."),
        ("warn_color", "ff0000", "Foreground color when below threshold."),
        ("update_interval", 2, "Update interval in seconds."),
    ]

    def __init__(self, **config):
        base.InLoopPollText.__init__(self, "", **config)
        self.add_defaults(MemAvail.defaults)
        self._normal_fg = self.foreground

    def poll(self):
        mem = psutil.virtual_memory()
        avail_gb = mem.available / (1024 ** 3)

        if avail_gb < self.warn_threshold_gb:
            self.foreground = self.warn_color
        else:
            self.foreground = self._normal_fg

        return f"mem {avail_gb:.1f}GB"
