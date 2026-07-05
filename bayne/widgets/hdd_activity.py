import time

import cairocffi
import psutil

from libqtile.widget import base

ANIM_INTERVAL = 0.05


class HDDActivity(base._Widget, base.MarginMixin):
    """Display disk read/write rates as horizontal bars with color thresholds.

    Two stacked horizontal bars (read on top, write on bottom).
    Colors: green (<60%), yellow (60-80%), red (>80%) of max_rate.
    Interpolates between samples at ~20fps for smooth animation.
    """

    orientations = base.ORIENTATION_HORIZONTAL
    defaults = [
        ("frequency", 1, "Update frequency in seconds"),
        ("max_rate_mb", 500, "MB/s considered 100% for bar scaling"),
        ("color_low", "00ff00", "Color for usage < 60%"),
        ("color_mid", "ffff00", "Color for usage 60-80%"),
        ("color_high", "ff0000", "Color for usage > 80%"),
        ("threshold_mid", 60, "Percentage threshold for mid color"),
        ("threshold_high", 80, "Percentage threshold for high color"),
    ]

    def __init__(self, width=60, **config):
        base._Widget.__init__(self, width, **config)
        self.add_defaults(HDDActivity.defaults)
        self.add_defaults(base.MarginMixin.defaults)
        self._io_prev = psutil.disk_io_counters()
        self._prev = [0.0, 0.0]
        self._target = [0.0, 0.0]
        self._display = [0.0, 0.0]
        self._sample_time = time.monotonic()
        self._anim_gen = 0

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        self.drawer.ctx.set_antialias(cairocffi.ANTIALIAS_NONE)

    def timer_setup(self):
        self.timeout_add(self.frequency, self._sample)

    def _sample(self):
        self._anim_gen += 1
        gen = self._anim_gen
        cur = psutil.disk_io_counters()
        read_bytes = (cur.read_bytes - self._io_prev.read_bytes) / self.frequency
        write_bytes = (cur.write_bytes - self._io_prev.write_bytes) / self.frequency
        self._io_prev = cur

        max_bytes = self.max_rate_mb * 1024 * 1024
        self._prev = list(self._display)
        self._target = [
            min(100.0, read_bytes / max_bytes * 100.0),
            min(100.0, write_bytes / max_bytes * 100.0),
        ]
        self._sample_time = time.monotonic()
        self.timeout_add(ANIM_INTERVAL, lambda: self._animate(gen))
        self.timeout_add(self.frequency, self._sample)

    def _animate(self, gen):
        if gen != self._anim_gen:
            return
        t = (time.monotonic() - self._sample_time) / self.frequency
        if t >= 1.0:
            return
        self._display = [p + (c - p) * t for p, c in zip(self._prev, self._target)]
        self.draw()
        self.timeout_add(ANIM_INTERVAL, lambda: self._animate(gen))

    def _color_for_pct(self, pct):
        if pct >= self.threshold_high:
            return self.color_high
        if pct >= self.threshold_mid:
            return self.color_mid
        return self.color_low

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)

        available_height = self.bar.height - self.margin_y * 2
        available_width = self.width - self.margin_x * 2
        bar_height = max(1, (available_height - 2) // 2)
        x = self.margin_x

        for i, pct in enumerate(self._display):
            y = self.margin_y + i * (bar_height + 2)
            bar_w = max(1, int(available_width * pct / 100.0))

            self.drawer.set_source_rgb(self._color_for_pct(pct))
            self.drawer.ctx.rectangle(x, y, bar_w, bar_height)
            self.drawer.ctx.fill()

        self.drawer.draw(
            offsetx=self.offsetx, offsety=self.offsety, width=self.width, height=self.bar.height
        )
