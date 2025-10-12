from typing import List, Literal, Dict, get_args

from bayne.default import get_widget_defaults
from bayne.rofi import Rofi, RofiScript
from bayne.widgets.outlook_checker import OutlookChecker
from libqtile import hook, qtile, log_utils, layout, widget, bar
import os

from libqtile.command.interface import Layout
from libqtile.config import Key, Group, Screen
from libqtile.group import _Group
from libqtile.lazy import lazy, LazyCall

logger = log_utils.logger

MAIN_SCREEN_IDX = 0
LEFT_SCREEN_IDX = 1
RIGHT_SCREEN_IDX = 2

ACTIVE_BAR = "#591a7d"
INACTIVE_BAR = "#444"

mod = "mod4"

WorkspaceNumberKey = Literal["1", "2", "3", "4", "5"]

def sort_window(group: _Group):
    clients = group.layout.clients

    def _sort_window(window):
        if window not in clients:
            return -1
        return (-clients.index(window) + clients.current_index - 1) % (len(clients))

    return _sort_window

class CustomTaskList(widget.TaskList):
    @property
    def windows(self):
        windows = super().windows
        windows = sorted(windows, key=sort_window(self.bar.screen.group))
        return windows

def _groups(prefix: str, screen_affinity: int) -> Dict[WorkspaceNumberKey, Group]:
    return dict([(i, Group(name=f'{prefix}{i}', screen_affinity=screen_affinity)) for i in get_args(WorkspaceNumberKey)])

class DQHDWorkflow:
    def __init__(
        self,
        active_bar: str,
        inactive_bar: str,
        mod: str,            
    ):
        self.active_bar = active_bar
        self.inactive_bar = inactive_bar
        self.mod = mod
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
                for widget in screen.top.widgets:
                    widget.background = self.inactive_bar

            qtile.current_screen.top.background = self.active_bar
            for widget in qtile.current_screen.top.widgets:
                widget.background = self.active_bar

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
        _qtile.focus_screen(MAIN_SCREEN_IDX)
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

    def group_switch(self, number: WorkspaceNumberKey) -> LazyCall:
        def _switch(_qtile):
            _group = self.get_group_for_current_screen(_qtile, number)
            if _group:
                _qtile.current_screen.set_group(_group)
        return lazy.function(_switch)

    def move_window_to_group(self, number: WorkspaceNumberKey) -> LazyCall:
        def _move(_qtile):
            _group = self.get_group_for_current_screen(_qtile, number)
            if _group:
                _qtile.current_window.togroup(_group.name)
        return lazy.function(_move)

    @staticmethod
    def _screen_move_left(_qtile):
        current_index = _qtile.screens.index(_qtile.current_screen)
        if current_index == RIGHT_SCREEN_IDX:
            _qtile.focus_screen(MAIN_SCREEN_IDX)
        elif current_index == MAIN_SCREEN_IDX:
            _qtile.focus_screen(LEFT_SCREEN_IDX)

    @staticmethod
    def _screen_move_window_left(_qtile):
        current_index = _qtile.screens.index(_qtile.current_screen)
        if current_index == RIGHT_SCREEN_IDX:
            _qtile.current_window.toscreen(MAIN_SCREEN_IDX)
        elif current_index == MAIN_SCREEN_IDX:
            _qtile.current_window.toscreen(LEFT_SCREEN_IDX)

    @staticmethod
    def _screen_move_right(_qtile):
        current_index = _qtile.screens.index(_qtile.current_screen)
        if current_index == LEFT_SCREEN_IDX:
            _qtile.focus_screen(MAIN_SCREEN_IDX)
        elif current_index == MAIN_SCREEN_IDX:
            _qtile.focus_screen(RIGHT_SCREEN_IDX)

    @staticmethod
    def _screen_move_window_right(_qtile):
        current_index = _qtile.screens.index(_qtile.current_screen)
        if current_index == LEFT_SCREEN_IDX:
            _qtile.current_window.toscreen(MAIN_SCREEN_IDX)
        elif current_index == MAIN_SCREEN_IDX:
            _qtile.current_window.toscreen(RIGHT_SCREEN_IDX)

    def keys(self):
        keys = []

        for number_key in get_args(WorkspaceNumberKey):
            keys.extend([
                Key(
                    [mod],
                    number_key,
                    self.group_switch(number_key),
                    desc=f"Switch to group {number_key}"
                ),
                Key(
                    [mod, "shift"],
                    number_key,
                    self.move_window_to_group(number_key),
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

    @staticmethod
    def layouts():
        return [
            layout.Max(),
        ]

    def fake_screens(self):
        # 5120x1440
        # 1280x1440+0+0, 2560x1440+1280+0, 1280x1440+3840+0
        fake_screens: List[Screen] = []
        fake_screens.insert(MAIN_SCREEN_IDX, Screen(
            background="#555",
            top=bar.Bar(
                widgets=[
                    widget.GroupBox(visible_groups=[g.name for g in self.main_groups.values()]),
                    CustomTaskList(
                        parse_text=lambda x: '',
                        stretch=False,
                        window_name_location=True,
                    ),
                    widget.WindowName(),
                    widget.Clock(format="%a %b %d %I:%M:%S %p"),
                    OutlookChecker(),
                    widget.Spacer(),
                    widget.TextBox(fmt="net", ),
                    widget.NetGraph(
                        type='line',
                        margin_x=0,
                        margin_y=0,
                        border_width=0,
                    ),
                    widget.TextBox(fmt="cpu", ),
                    widget.CPUGraph(
                        type='line',
                        margin_x=0,
                        margin_y=0,
                        border_width=0,
                    ),
                    widget.TextBox(fmt="mem", ),
                    widget.MemoryGraph(
                        type='line',
                        margin_x=0,
                        margin_y=0,
                        border_width=0,
                    ),
                    widget.Systray(padding=0),
                    widget.Spacer(length=8)
                ],
                size=24,
                background=ACTIVE_BAR,
            ),
            x=1280, y=0, width=2560, height=1440,
        ))
        fake_screens.insert(LEFT_SCREEN_IDX, Screen(
            background="#555",
            top=bar.Bar(
                widgets=[
                    widget.GroupBox(visible_groups=[g.name for g in self.left_groups.values()]),
                    CustomTaskList(
                        parse_text=lambda x: '',
                        stretch=False,
                        window_name_location=True,
                    ),
                    widget.WindowName(),
                ], size=24, background=ACTIVE_BAR, ),
            x=0, y=0, width=1280, height=1440,
        ))
        fake_screens.insert(RIGHT_SCREEN_IDX, Screen(
            background="#555",
            top=bar.Bar(
                widgets=[
                    widget.GroupBox(visible_groups=[g.name for g in self.right_groups.values()]),
                    CustomTaskList(
                        parse_text=lambda x: '',
                        stretch=False,
                        window_name_location=True,
                    ),
                    widget.WindowName(),
                ], size=24, background=ACTIVE_BAR, ),
            x=3840, y=0, width=1280, height=1440,
        ))