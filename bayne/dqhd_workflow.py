from typing import Dict
from typing import get_args
from typing import List
from typing import Literal

from libqtile import bar
from libqtile import hook
from libqtile import layout
from libqtile import log_utils
from libqtile import qtile
from libqtile.config import Group
from libqtile.config import Key
from libqtile.config import Screen
from libqtile.group import _Group
from libqtile.layout.base import Layout
from libqtile.lazy import lazy
from libqtile.lazy import LazyCall
from libqtile.widget.base import _Widget
from libqtile.widget.clock import Clock
from libqtile.widget.graph import CPUGraph
from libqtile.widget.graph import MemoryGraph
from libqtile.widget.graph import NetGraph
from libqtile.widget.groupbox import GroupBox
from libqtile.widget.spacer import Spacer
from libqtile.widget.statusnotifier import StatusNotifier
from libqtile.widget.tasklist import TaskList
from libqtile.widget.textbox import TextBox

logger = log_utils.logger

ICON_SIZE = 22
BAR_SIZE = 28
BACKGROUND_COLOR = "#555555FF"
MAIN_SCREEN_IDX = 0
LEFT_SCREEN_IDX = 1
RIGHT_SCREEN_IDX = 2

mod = "mod4"

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
            theme_mode='preferred',
            theme_path='/usr/share/icons/Papirus-Dark',
            icon_size=ICON_SIZE,
            border_width=4,
            highlight_method='block',
            spacing=0,
            padding_y=8,
            padding_x=2,
            margin=0,
            markup_normal="",
            markup_focused=" {}",
            window_name_location=False,
            **config
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

def _groups(prefix: str, screen_affinity: int) -> Dict[WorkspaceNumberKey, Group]:
    return { i: Group(name=f'{prefix}{i}', screen_affinity=screen_affinity) for i in get_args(WorkspaceNumberKey) }

class DQHDWorkflow:
    def __init__(
        self,
        active_bar: str,
        inactive_bar: str,
        mod: str,
        warp: bool,
    ):
        self.active_bar = active_bar
        self.inactive_bar = inactive_bar
        self.mod = mod
        self.warp = warp
        self.main_groups: Dict[WorkspaceNumberKey, Group] = _groups('M', MAIN_SCREEN_IDX)
        self.left_groups: Dict[WorkspaceNumberKey, Group] = _groups('L', LEFT_SCREEN_IDX)
        self.right_groups: Dict[WorkspaceNumberKey, Group] = _groups('R', RIGHT_SCREEN_IDX)
        self.last_main_group = None

    def register_hooks(self,):
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
            if group_name in [g.name for g in self.main_groups.values()] and self.last_main_group != group_name:
                self.last_main_group = group_name

    def groups(self):
        groups = []
        groups.extend(self.main_groups.values())
        groups.extend(self.left_groups.values())
        groups.extend(self.right_groups.values())
        return groups

    def _main_screen(self, _qtile):
        _qtile.focus_screen(MAIN_SCREEN_IDX, warp=self.warp)
        if self.last_main_group is not None and _qtile.current_screen.group.name != self.last_main_group:
            _qtile.screens[MAIN_SCREEN_IDX].toggle_group(self.last_main_group)

    def get_group_for_current_screen(self, _qtile, number: WorkspaceNumberKey) -> _Group:
        if _qtile.current_screen == _qtile.screens[MAIN_SCREEN_IDX]:
            return _qtile.groups_map.get(self.main_groups[number].name)
        elif _qtile.current_screen == _qtile.screens[LEFT_SCREEN_IDX]:
            return _qtile.groups_map.get(self.left_groups[number].name)
        elif _qtile.current_screen == _qtile.screens[RIGHT_SCREEN_IDX]:
            return _qtile.groups_map.get(self.right_groups[number].name)
        else:
            raise ValueError(
                f"current_screen is not in screens: {_qtile.current_screen}"
            )

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

    def keys(self) -> List[Key]:
        keys = []

        for number_key in get_args(WorkspaceNumberKey):
            keys.extend([
                Key(
                    [mod],
                    number_key,
                    self._group_switch(number_key),
                    desc=f"Switch to group {number_key}"
                ),
                Key(
                    [mod, "shift"],
                    number_key,
                    self._move_window_to_group(number_key),
                    desc=f"Switch to group {number_key}"
                ),
            ])

        keys.append(Key([mod], "grave",
            lazy.function(self._main_screen),
            desc="last main group"
        ))

        # https://github.com/qtile/qtile/blob/master/libqtile/backend/x11/xkeysyms.py
        keys.extend([
            Key([self.mod], "h", lazy.function(self._screen_move_left), desc="Move focus to left"),
            Key([self.mod], "l", lazy.function(self._screen_move_right), desc="Move focus to right"),
            Key([self.mod], "j", lazy.layout.down(), desc="Move focus down"),
            Key([self.mod], "k", lazy.layout.up(), desc="Move focus up"),
            Key([self.mod], "Tab", lazy.layout.next(), desc="Move window focus to next window"),
            Key([self.mod, "shift"], "Tab", lazy.layout.previous(), desc="Move window focus to prev window"),
            Key([self.mod, "shift"], "h", lazy.function(self._screen_move_window_left), lazy.function(self._screen_move_left), desc="Move window to the left"),
            Key([self.mod, "shift"], "l", lazy.function(self._screen_move_window_right), lazy.function(self._screen_move_right), desc="Move window to the right"),
            Key([self.mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move window down"),
            Key([self.mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),
        ])

        return keys

    @staticmethod
    def layouts() -> List[Layout]:
        return [
            layout.Max(),
        ]

    @staticmethod
    def _main_screen_window_name_parse(window_name: str):
        if len(window_name) > 50:
            return window_name[:50] + "…"
        return window_name

    def fake_screens(self, extra_widgets: List[_Widget] = None) -> List[Screen]:
        # 5120x1440
        # 1280x1440+0+0, 2560x1440+1280+0, 1280x1440+3840+0
        fake_screens: List[Screen] = []
        fake_screens.insert(MAIN_SCREEN_IDX, Screen(
            background=BACKGROUND_COLOR,
            top=bar.Bar(
                widgets=[
                    GroupBox(visible_groups=[g.name for g in self.main_groups.values()]),
                    CustomTaskList(
                        parse_text=self._main_screen_window_name_parse,
                    ),
                    Clock(format="%a %b %d %I:%M:%S %p"),
                    *extra_widgets,
                    TextBox(fmt="net", ),
                    NetGraph(
                        type='line',
                        margin_x=0,
                        margin_y=0,
                        border_width=0,
                    ),
                    TextBox(fmt="cpu", ),
                    CPUGraph(
                        type='line',
                        margin_x=0,
                        margin_y=0,
                        border_width=0,
                    ),
                    TextBox(fmt="mem", ),
                    MemoryGraph(
                        type='line',
                        margin_x=0,
                        margin_y=0,
                        border_width=0,
                    ),
                    CustomStatusNotifier(
                        icon_size=ICON_SIZE,
                        padding=4,
                        icon_theme='Papirus-Dark',
                    ),
                    Spacer(length=4)
                ],
                size=BAR_SIZE,
                background=self.active_bar,
            ),
            x=1280, y=0, width=2560, height=1440,
        ))
        fake_screens.insert(LEFT_SCREEN_IDX, Screen(
            background=BACKGROUND_COLOR,
            top=bar.Bar(
                widgets=[
                    GroupBox(visible_groups=[g.name for g in self.left_groups.values()]),
                    CustomTaskList(),
                ], size=BAR_SIZE, background=self.active_bar, ),
            x=0, y=0, width=1280, height=1440,
        ))
        fake_screens.insert(RIGHT_SCREEN_IDX, Screen(
            background=BACKGROUND_COLOR,
            top=bar.Bar(
                widgets=[
                    GroupBox(visible_groups=[g.name for g in self.right_groups.values()]),
                    CustomTaskList(),

                ], size=BAR_SIZE, background=self.active_bar, ),
            x=3840, y=0, width=1280, height=1440,
        ))
        return fake_screens