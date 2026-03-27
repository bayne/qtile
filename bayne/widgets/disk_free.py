import psutil

from libqtile.widget import base


class DiskFree(base.InLoopPollText):
    """Display remaining disk space in GB, turning red when low."""

    defaults = [
        ("path", "/", "Partition path to monitor."),
        ("warn_threshold_gb", 100, "Turn red below this many GB free."),
        ("warn_color", "ff0000", "Foreground color when below threshold."),
        ("update_interval", 30, "Update interval in seconds."),
        ("format", "disk {free:.0f}GB", "Display format. Available: {free}, {total}, {used}, {percent}."),
    ]

    def __init__(self, **config):
        base.InLoopPollText.__init__(self, "", **config)
        self.add_defaults(DiskFree.defaults)
        self._normal_fg = self.foreground

    def poll(self):
        usage = psutil.disk_usage(self.path)
        free_gb = usage.free / (1024 ** 3)
        total_gb = usage.total / (1024 ** 3)
        used_gb = usage.used / (1024 ** 3)

        if free_gb < self.warn_threshold_gb:
            self.foreground = self.warn_color
        else:
            self.foreground = self._normal_fg

        return self.format.format(
            free=free_gb,
            total=total_gb,
            used=used_gb,
            percent=usage.percent,
        )
