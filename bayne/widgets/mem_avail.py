import time

import psutil

from libqtile.widget import base

ANIM_INTERVAL = 0.05


class MemAvail(base.InLoopPollText):
    """Display available memory in GB, turning red when low.

    Interpolates between samples at ~20fps for smooth animation.
    """

    defaults = [
        ("warn_threshold_gb", 8, "Turn red below this many GB available."),
        ("warn_color", "ff0000", "Foreground color when below threshold."),
        ("update_interval", 2, "Update interval in seconds."),
    ]

    def __init__(self, **config):
        base.InLoopPollText.__init__(self, "", **config)
        self.add_defaults(MemAvail.defaults)
        self._normal_fg = self.foreground
        self._prev_gb = 0.0
        self._target_gb = 0.0
        self._sample_time = time.monotonic()
        self._anim_gen = 0

    def timer_setup(self):
        super().timer_setup()

    def poll(self):
        self._anim_gen += 1
        gen = self._anim_gen
        mem = psutil.virtual_memory()
        self._prev_gb = self._target_gb
        self._target_gb = mem.available / (1024 ** 3)
        self._sample_time = time.monotonic()
        self.timeout_add(ANIM_INTERVAL, lambda: self._animate(gen))
        return self._format(self._target_gb)

    def _format(self, avail_gb):
        if avail_gb < self.warn_threshold_gb:
            self.foreground = self.warn_color
        else:
            self.foreground = self._normal_fg
        return f"mem {avail_gb:.1f}GB"

    def _animate(self, gen):
        if gen != self._anim_gen:
            return
        t = (time.monotonic() - self._sample_time) / self.update_interval
        if t >= 1.0:
            return
        display_gb = self._prev_gb + (self._target_gb - self._prev_gb) * t
        self.update(self._format(display_gb))
        self.timeout_add(ANIM_INTERVAL, lambda: self._animate(gen))
