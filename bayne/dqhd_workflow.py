from enum import Enum
from typing import Literal, get_args

from bayne.widgets.cpu_bars import CPUBars
from bayne.widgets.disk_free import DiskFree
from bayne.widgets.hdd_activity import HDDActivity
from bayne.widgets.mem_avail import MemAvail
from bayne.widgets.net_speed import NetSpeed
from libqtile import bar, hook, layout, log_utils, qtile
from libqtile.config import Group, Key, Screen
from libqtile.group import _Group
from libqtile.layout.base import Layout
from libqtile.lazy import LazyCall, lazy
from libqtile.widget.base import _Widget, MarginMixin
from libqtile.widget.clock import Clock
from libqtile.widget.graph import MemoryGraph, NetGraph
from libqtile.widget.groupbox import GroupBox
from libqtile.widget.spacer import Spacer
from libqtile.widget.statusnotifier import StatusNotifier
from libqtile.widget.systray import Systray
from libqtile.widget.tasklist import TaskList
from libqtile.widget.textbox import TextBox

logger = log_utils.logger

ICON_SIZE = 22
BAR_SIZE = 28
BACKGROUND_COLOR = "#555555FF"
MAIN_SCREEN_IDX = 0
LEFT_SCREEN_IDX = 1
RIGHT_SCREEN_IDX = 2


WorkspaceNumberKey = Literal["1", "2", "3", "4", "5"]


def sort_window(group: _Group):
    clients = group.layout.clients

    def _sort_window(window):
        if window not in clients:
            return -1
        return (-clients.index(window) + clients.current_index - 1) % (len(clients))

    return _sort_window


class CustomTaskList(TaskList):
    def __init__(self, **config):
        super().__init__(
            theme_path="Papirus-Dark",
            icon_size=ICON_SIZE,
            border_width=4,
            highlight_method="block",
            spacing=0,
            padding_y=8,
            padding_x=2,
            margin_x=7,
            margin_y=0,
            markup_normal="",
            markup_focused=" {}",
            window_name_location=False,
            border="#215578",
            unfocused_border="#557983",
            **config,
        )

    @property
    def windows(self):
        windows = super().windows
        windows = sorted(windows, key=sort_window(self.bar.screen.group))
        return windows


class CustomStatusNotifier(StatusNotifier):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        logger.info("CustomStatusNotifier initialized")


def _groups(prefix: str, screen_affinity: int) -> dict[WorkspaceNumberKey, Group]:
    return {
        i: Group(name=f"{prefix}{i}", screen_affinity=screen_affinity)
        for i in get_args(WorkspaceNumberKey)
    }


class DQHDWorkflow:
    def __init__(
        self,
        active_bar: str,
        inactive_bar: str,
        warp: bool,
        theme_mode: str,
    ):
        self.active_bar = active_bar
        self.inactive_bar = inactive_bar
        self.warp = warp
        self.theme_mode = theme_mode
        self.main_groups: dict[WorkspaceNumberKey, Group] = _groups("M", MAIN_SCREEN_IDX)
        self.left_groups: dict[WorkspaceNumberKey, Group] = _groups("L", LEFT_SCREEN_IDX)
        self.right_groups: dict[WorkspaceNumberKey, Group] = _groups("R", RIGHT_SCREEN_IDX)
        self.last_main_group = None

    def register_hooks(
        self,
    ):

        @hook.subscribe.client_name_updated
        async def on_client_name_updated(client):
            if not client.has_focus:
                client.urgent = True

        @hook.subscribe.current_screen_change
        def on_screen_change_update_top_bar_background():
            for screen in qtile.screens:
                if screen.top is None:
                    continue
                screen.top.background = self.inactive_bar

            if qtile.current_screen.top is not None:
                qtile.current_screen.top.background = self.active_bar

        @hook.subscribe.setgroup
        def set_last_main_group(*_):
            group_name = qtile.current_screen.group.name
            if (
                group_name in [g.name for g in self.main_groups.values()]
                and self.last_main_group != group_name
            ):
                self.last_main_group = group_name

    def groups(self):
        groups = []
        groups.extend(self.main_groups.values())
        groups.extend(self.left_groups.values())
        groups.extend(self.right_groups.values())
        return groups

    def _main_screen(self, _qtile):
        _qtile.focus_screen(MAIN_SCREEN_IDX, warp=self.warp)
        if (
            self.last_main_group is not None
            and _qtile.current_screen.group.name != self.last_main_group
        ):
            _qtile.screens[MAIN_SCREEN_IDX].toggle_group(self.last_main_group)

    def get_group_for_current_screen(self, _qtile, number: WorkspaceNumberKey) -> _Group:
        if _qtile.current_screen == _qtile.screens[MAIN_SCREEN_IDX]:
            return _qtile.groups_map.get(self.main_groups[number].name)
        elif _qtile.current_screen == _qtile.screens[LEFT_SCREEN_IDX]:
            return _qtile.groups_map.get(self.left_groups[number].name)
        elif _qtile.current_screen == _qtile.screens[RIGHT_SCREEN_IDX]:
            return _qtile.groups_map.get(self.right_groups[number].name)
        else:
            raise ValueError(f"current_screen is not in screens: {_qtile.current_screen}")

    def _group_switch(self, number: WorkspaceNumberKey) -> LazyCall:
        def _switch(_qtile):
            _group = self.get_group_for_current_screen(_qtile, number)
            if _group:
                _qtile.current_screen.set_group(_group)

        return lazy.function(_switch)

    def _move_window_to_group(self, number: WorkspaceNumberKey) -> LazyCall:
        def _move(_qtile):
            _group = self.get_group_for_current_screen(_qtile, number)
            if _group:
                _qtile.current_window.togroup(_group.name)

        return lazy.function(_move)

    def _screen_move_left(self, _qtile):
        current_index = _qtile.screens.index(_qtile.current_screen)
        if current_index == RIGHT_SCREEN_IDX:
            _qtile.focus_screen(MAIN_SCREEN_IDX, warp=self.warp)
        elif current_index == MAIN_SCREEN_IDX:
            _qtile.focus_screen(LEFT_SCREEN_IDX, warp=self.warp)

    @staticmethod
    def _screen_move_window_left(_qtile):
        current_index = _qtile.screens.index(_qtile.current_screen)
        if current_index == RIGHT_SCREEN_IDX:
            _qtile.current_window.toscreen(MAIN_SCREEN_IDX)
        elif current_index == MAIN_SCREEN_IDX:
            _qtile.current_window.toscreen(LEFT_SCREEN_IDX)

    def _screen_move_right(self, _qtile):
        current_index = _qtile.screens.index(_qtile.current_screen)
        if current_index == LEFT_SCREEN_IDX:
            _qtile.focus_screen(MAIN_SCREEN_IDX, warp=self.warp)
        elif current_index == MAIN_SCREEN_IDX:
            _qtile.focus_screen(RIGHT_SCREEN_IDX, warp=self.warp)

    @staticmethod
    def _screen_move_window_right(_qtile):
        current_index = _qtile.screens.index(_qtile.current_screen)
        if current_index == LEFT_SCREEN_IDX:
            _qtile.current_window.toscreen(MAIN_SCREEN_IDX)
        elif current_index == MAIN_SCREEN_IDX:
            _qtile.current_window.toscreen(RIGHT_SCREEN_IDX)

    @staticmethod
    def components(group: Group | str):
        name = group if isinstance(group, str) else group.name
        if name == "MBP":
            return "MBP", 1
        return name[0], int(name[1:])

    @staticmethod
    def get_screen_idx(group: Group):
        match DQHDWorkflow.components(group):
            case "M", _:
                return MAIN_SCREEN_IDX
            case "L", _:
                return LEFT_SCREEN_IDX
            case "R", _:
                return RIGHT_SCREEN_IDX
            case _:
                return MAIN_SCREEN_IDX

    @staticmethod
    def focus(window, warp=False):
        if not window.group:
            return

        if warp:
            window.toscreen(qtile.current_screen.index)
            qtile.current_group.focus(window)
            return

        group = window.group
        screen_idx = DQHDWorkflow.get_screen_idx(group)

        qtile.screens[screen_idx].set_group(group)
        group.focus(window)

    @staticmethod
    def _rank_closest(_qtile, predicate):
        """Return the window dict closest to the current group, or None.

        Ranks candidates by (active_distance, screen_distance, group_distance).
        `predicate` is called with each window dict from `_qtile.windows()`.
        """
        current_group = _qtile.current_group
        current_windows = filter(lambda s: s.group.current_window, _qtile.screens)
        current_windows = list(map(lambda s: s.group.current_window.wid, current_windows))

        def active_distance(w):
            return 0 if w["id"] in current_windows else 1

        def group_distance(w):
            _, n = DQHDWorkflow.components(w["group"])
            _, cn = DQHDWorkflow.components(current_group.name)
            return abs(n - cn)

        def screen_distance(w):
            group = DQHDWorkflow.components(w["group"])
            cg, _cn = DQHDWorkflow.components(current_group.name)

            match group:
                case g, _ if g == cg:
                    return 0
                case "M", _:
                    return 1
                case "L", _:
                    return 2
                case "R", _:
                    return 3
                case _:
                    return 4

        def rank(w):
            return (active_distance(w), screen_distance(w), group_distance(w))

        windows = list(filter(predicate, _qtile.windows()))
        if not windows:
            return None
        return min(windows, key=rank)

    @staticmethod
    def _open_terminal(_qtile):
        def is_kitty(w):
            return w["group"] != "MBP" and "kitty" in w["wm_class"]

        match = DQHDWorkflow._rank_closest(_qtile, is_kitty)
        if match is not None:
            window = _qtile.windows_map.get(match["id"])
            if window is not None:
                DQHDWorkflow.focus(window, warp=True)
                return
        _qtile.spawn("sensible-terminal")

    @staticmethod
    def focus_for_tmux(x_wid=None):
        """Focus a kitty window for a tmxb notification.

        Called via `qtile cmd-obj -o cmd -f eval` from tmxb. Returns True if a
        window was focused, False otherwise (caller can spawn a new terminal).

          1. If `x_wid` is set and matches a live window → focus it directly.
          2. Otherwise rank all kitty windows by closest-terminal heuristic.

        tmxb is responsible for resolving the originating tmux client to an X
        window id (via `xdotool search --pid`) before calling — qtile's window
        info dict does not expose pids.
        """
        from libqtile import qtile as _qtile

        if _qtile is None:
            return False

        windows_map = _qtile.windows_map

        if x_wid is not None:
            try:
                wid = int(x_wid)
            except (TypeError, ValueError):
                wid = None
            if wid is not None and wid in windows_map:
                DQHDWorkflow.focus(windows_map[wid], warp=True)
                return True

        def is_kitty(w):
            return w["group"] != "MBP" and "kitty" in w["wm_class"]

        match = DQHDWorkflow._rank_closest(_qtile, is_kitty)
        if match is None:
            return False
        window = windows_map.get(match["id"])
        if window is None:
            return False
        DQHDWorkflow.focus(window, warp=True)
        return True

    def keys(self, mod="mod4") -> list[Key]:
        keys = []

        for number_key in get_args(WorkspaceNumberKey):
            keys.extend(
                [
                    Key(
                        [mod],
                        number_key,
                        self._group_switch(number_key),
                        desc=f"Switch to group {number_key}",
                    ),
                    Key(
                        [mod, "shift"],
                        number_key,
                        self._move_window_to_group(number_key),
                        desc=f"Switch to group {number_key}",
                    ),
                ]
            )

        keys.append(Key([mod], "grave", lazy.function(self._main_screen), desc="last main group"))

        # https://github.com/qtile/qtile/blob/master/libqtile/backend/x11/xkeysyms.py
        keys.extend(
            [
                Key([mod], "h", lazy.function(self._screen_move_left), desc="Move focus to left"),
                Key(
                    [mod], "l", lazy.function(self._screen_move_right), desc="Move focus to right"
                ),
                Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
                Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
                Key([mod], "Tab", lazy.layout.next(), desc="Move window focus to next window"),
                Key(
                    [mod], "t", lazy.function(DQHDWorkflow._open_terminal), desc="Launch terminal"
                ),
                Key(
                    [mod, "shift"],
                    "Tab",
                    lazy.layout.previous(),
                    desc="Move window focus to prev window",
                ),
                Key(
                    [mod, "shift"],
                    "h",
                    lazy.function(self._screen_move_window_left),
                    lazy.function(self._screen_move_left),
                    desc="Move window to the left",
                ),
                Key(
                    [mod, "shift"],
                    "l",
                    lazy.function(self._screen_move_window_right),
                    lazy.function(self._screen_move_right),
                    desc="Move window to the right",
                ),
                Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move window down"),
                Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),
            ]
        )

        return keys

    @staticmethod
    def layouts() -> list[Layout]:
        return [
            layout.Max(),
        ]

    @staticmethod
    def _main_screen_window_name_parse(window_name: str):
        if len(window_name) > 50:
            return window_name[:50] + "…"
        return window_name

    def fake_screens(self, extra_widgets: list[_Widget] = None) -> list[Screen]:
        # 5120x1440
        # 1280x1440+0+0, 2560x1440+1280+0, 1280x1440+3840+0
        fake_screens: list[Screen] = []
        fake_screens.insert(
            MAIN_SCREEN_IDX,
            Screen(
                background=BACKGROUND_COLOR,
                top=bar.Bar(
                    margin=[4, 2, 4, 2],
                    widgets=[
                        GroupBox(visible_groups=[g.name for g in self.main_groups.values()]),
                        CustomTaskList(
                            parse_text=self._main_screen_window_name_parse,
                            theme_mode=self.theme_mode,
                        ),
                        Clock(format="%a %b %d %I:%M:%S %p"),
                        *extra_widgets,
                        Systray(
                            icon_size=ICON_SIZE,
                            padding=4,
                        ),
                        Spacer(length=4),
                    ],
                    size=BAR_SIZE,
                    background=self.active_bar,
                ),
                left=bar.Gap(2),
                right=bar.Gap(2),
                bottom=bar.Gap(4),
                x=1280,
                y=0,
                width=2560,
                height=1440,
            ),
        )
        fake_screens.insert(
            LEFT_SCREEN_IDX,
            Screen(
                background=BACKGROUND_COLOR,
                top=bar.Bar(
                    margin=[4, 2, 4, 4],
                    widgets=[
                        GroupBox(visible_groups=[g.name for g in self.left_groups.values()]),
                        CustomTaskList(theme_mode=self.theme_mode),
                    ],
                    size=BAR_SIZE,
                    background=self.active_bar,
                ),
                left=bar.Gap(4),
                right=bar.Gap(2),
                bottom=bar.Gap(4),
                x=0,
                y=0,
                width=1280,
                height=1440,
            ),
        )
        fake_screens.insert(
            RIGHT_SCREEN_IDX,
            Screen(
                background=BACKGROUND_COLOR,
                top=bar.Bar(
                    margin=[4, 4, 4, 2],
                    widgets=[
                        GroupBox(visible_groups=[g.name for g in self.right_groups.values()]),
                        CustomTaskList(theme_mode=self.theme_mode),
                        NetSpeed(),
                        NetGraph(
                            type="box",
                            margin_x=0,
                            margin_y=0,
                            border_width=0,
                        ),
                        TextBox(
                            fmt="cpu",
                        ),
                        CPUBars(
                            width=64,
                            margin_x=2,
                            margin_y=4,
                        ),
                        MemAvail(),
                        MemoryGraph(
                            type="box",
                            margin_x=0,
                            margin_y=0,
                            border_width=0,
                        ),
                        DiskFree(format="hdd {free:.0f}GB"),
                        HDDActivity(
                            margin_x=2,
                            margin_y=4,
                        ),
                    ],
                    size=BAR_SIZE,
                    background=self.active_bar,
                ),
                left=bar.Gap(2),
                right=bar.Gap(4),
                bottom=bar.Gap(4),
                x=3840,
                y=0,
                width=1280,
                height=1440,
            ),
        )
        return fake_screens

class EnvGroup(str, Enum):
    MBP_GROUP = "MBP"
    W1_GROUP = "W1"
    W2_GROUP = "W2"
    PERSONAL = "M1"

    def __str__(self):
        return self.value

    def __reduce__(self):
        return self.__class__, (self.value,)
