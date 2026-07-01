import time

import cairocffi
import psutil

from libqtile.widget import base

ANIM_INTERVAL = 0.05


class CPUBars(base._Widget, base.MarginMixin):
    """Display per-core CPU usage as vertical bars with color thresholds.

    Each core gets a vertical bar. Colors: green (<60%), yellow (60-80%), red (>80%).
    Interpolates between samples at ~20fps for smooth animation.
    """

    orientations = base.ORIENTATION_HORIZONTAL
    defaults = [
        ("frequency", 1, "Update frequency in seconds"),
        ("bar_width", 4, "Width of each core bar in pixels"),
        ("bar_spacing", 1, "Spacing between bars in pixels"),
        ("color_low", "00ff00", "Color for usage < 60%"),
        ("color_mid", "ffff00", "Color for usage 60-80%"),
        ("color_high", "ff0000", "Color for usage > 80%"),
        ("threshold_mid", 60, "Percentage threshold for mid color"),
        ("threshold_high", 80, "Percentage threshold for high color"),
    ]

    def __init__(self, **config):
        self._core_count = psutil.cpu_count()
        width = config.pop("width", None)
        if width is None:
            width = 10
        base._Widget.__init__(self, width, **config)
        self.add_defaults(CPUBars.defaults)
        self.add_defaults(base.MarginMixin.defaults)
        self._prev = [0.0] * self._core_count
        self._target = [0.0] * self._core_count
        self._display = [0.0] * self._core_count
        self._sample_time = time.monotonic()

    def _configure(self, qtile, bar):
        super()._configure(qtile, bar)
        self.drawer.ctx.set_antialias(cairocffi.ANTIALIAS_NONE)

    def calculate_length(self):
        return (
            self._core_count * self.bar_width
            + (self._core_count - 1) * self.bar_spacing
            + self.margin_x * 2
        )

    def timer_setup(self):
        self.timeout_add(self.frequency, self._sample)

    def _sample(self):
        self._prev = list(self._display)
        self._target = psutil.cpu_percent(percpu=True)
        self._sample_time = time.monotonic()
        self.timeout_add(ANIM_INTERVAL, self._animate)
        self.timeout_add(self.frequency, self._sample)

    def _animate(self):
        t = (time.monotonic() - self._sample_time) / self.frequency
        if t >= 1.0:
            return
        self._display = [
            p + (c - p) * t for p, c in zip(self._prev, self._target)
        ]
        self.draw()
        self.timeout_add(ANIM_INTERVAL, self._animate)

    def _color_for_pct(self, pct):
        if pct >= self.threshold_high:
            return self.color_high
        if pct >= self.threshold_mid:
            return self.color_mid
        return self.color_low

    def draw(self):
        self.drawer.clear(self.background or self.bar.background)

        available_height = self.bar.height - self.margin_y * 2
        x = self.margin_x

        for pct in self._display:
            bar_h = max(1, int(available_height * pct / 100.0))
            y = self.margin_y + (available_height - bar_h)

            self.drawer.set_source_rgb(self._color_for_pct(pct))
            self.drawer.ctx.rectangle(x, y, self.bar_width, bar_h)
            self.drawer.ctx.fill()

            x += self.bar_width + self.bar_spacing

        self.drawer.draw(
            offsetx=self.offsetx, offsety=self.offsety, width=self.length, height=self.bar.height
        )
