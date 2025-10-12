import os
import subprocess
from typing import Dict
from typing import get_args
from typing import List
from typing import Literal

from bayne import systemd_logging
from bayne.default import get_default_floating
from bayne.default import get_default_mouse
from bayne.default import get_widget_defaults
from bayne.hooks import active_popup
from bayne.hooks import disable_screensaver
from bayne.hooks import popover
from bayne.rofi import Rofi
from bayne.rofi import RofiScript
from libqtile import bar
from libqtile import hook
from libqtile import layout
from libqtile import log_utils
from libqtile import qtile
from libqtile import widget
from libqtile.config import Group
from libqtile.config import Key
from libqtile.config import Match
from libqtile.config import Mouse
from libqtile.config import Screen
from libqtile.group import _Group
from libqtile.layout.base import Layout
from libqtile.lazy import lazy
from libqtile.lazy import LazyCall

active_popup.init([
    'opensnitch-ui',
])
popover.init(restack=[
    'jetbrains-idea',
])
systemd_logging.init()
disable_screensaver.init()

@hook.subscribe.startup_once
def startup_once():
    subprocess.Popen(["/usr/lib/policykit-1-gnome/polkit-gnome-authentication-agent-1"])
    # home dir backup
    subprocess.Popen(["/usr/bin/vorta"])
    # screenshot
    subprocess.Popen(["gtk-launch", "org.flameshot.Flameshot"])
    # egress firewall
    subprocess.Popen(["gtk-launch", "opensnitch_ui"])

    subprocess.Popen(["1password", "--silent"])

MBP_GROUP = "MBP"
W1_GROUP = "W1"
W2_GROUP = "W2"

ACTIVE_BAR = "#222"
INACTIVE_BAR = "#444"

WORK_VM_WM_CLASS = 'remote-viewer'

WORK_VM_WIN_1_NAME = 'work (1)'
WORK_VM_WIN_2_NAME = 'work (2)'
WORK_MBP_WIN_NAME = 'DeckLink Quad HDMI Recorder (1)'

WORK_WINDOW_NAMES = [
    WORK_VM_WIN_1_NAME,
    WORK_VM_WIN_2_NAME,
    WORK_MBP_WIN_NAME
]

logger = log_utils.logger

MAIN_SCREEN_IDX = 0
LEFT_SCREEN_IDX = 1
RIGHT_SCREEN_IDX = 2
WORK_SCREEN_IDX = 3

mod = "mod4"
rofi = Rofi(
    [
        RofiScript(
            name="intellij",
            path="/home/bpayne/Code/mine/dotfile/rofi-scripts/jetbrains.py"
        ),
        RofiScript(
            name="bookmark",
            path="/home/bpayne/Code/mine/dotfile/rofi-scripts/bookmarks.py"
        )
    ]
)

@hook.subscribe.current_screen_change
def on_screen_change_update_top_bar_background():
    for screen in qtile.screens:
        if screen.top is None:
            continue
        screen.top.background = INACTIVE_BAR
        for widget in screen.top.widgets:
            widget.background = INACTIVE_BAR

    qtile.current_screen.top.background = ACTIVE_BAR
    for widget in qtile.current_screen.top.widgets:
        widget.background = ACTIVE_BAR

@hook.subscribe.current_screen_change
def on_screen_change_hide_work_group():
    if qtile.current_screen != qtile.screens[WORK_SCREEN_IDX] or qtile.current_group.name != W1_GROUP:
        qtile.groups_map[W1_GROUP].hide()

def _screen_move_left(_qtile):
    current_index = _qtile.screens.index(_qtile.current_screen)
    if current_index == RIGHT_SCREEN_IDX:
        _qtile.focus_screen(MAIN_SCREEN_IDX)
    elif current_index == MAIN_SCREEN_IDX:
        _qtile.focus_screen(LEFT_SCREEN_IDX)

def _screen_move_window_left(_qtile):
    current_index = _qtile.screens.index(_qtile.current_screen)
    if current_index == RIGHT_SCREEN_IDX:
        _qtile.current_window.toscreen(MAIN_SCREEN_IDX)
    elif current_index == MAIN_SCREEN_IDX:
        _qtile.current_window.toscreen(LEFT_SCREEN_IDX)

def _screen_move_right(_qtile):
    current_index = _qtile.screens.index(_qtile.current_screen)
    if current_index == LEFT_SCREEN_IDX:
        _qtile.focus_screen(MAIN_SCREEN_IDX)
    elif current_index == MAIN_SCREEN_IDX:
        _qtile.focus_screen(RIGHT_SCREEN_IDX)

def _screen_move_window_right(_qtile):
    current_index = _qtile.screens.index(_qtile.current_screen)
    if current_index == LEFT_SCREEN_IDX:
        _qtile.current_window.toscreen(MAIN_SCREEN_IDX)
    elif current_index == MAIN_SCREEN_IDX:
        _qtile.current_window.toscreen(RIGHT_SCREEN_IDX)

# https://github.com/qtile/qtile/blob/master/libqtile/backend/x11/xkeysyms.py
env = os.environ.copy()
env.update({'PATH': env['PATH'] + ':/home/bpayne/.bin'})
keys = [
    Key([mod], "h", lazy.function(_screen_move_left), desc="Move focus to left"),
    Key([mod], "l", lazy.function(_screen_move_right), desc="Move focus to right"),
    Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
    Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
    Key([mod], "Tab", lazy.layout.next(), desc="Move window focus to next window"),
    Key([mod, "shift"], "Tab", lazy.layout.previous(), desc="Move window focus to prev window"),
    Key([mod, "shift"], "h", lazy.function(_screen_move_window_left), lazy.function(_screen_move_left), desc="Move window to the left"),
    Key([mod, "shift"], "l", lazy.function(_screen_move_window_right), lazy.function(_screen_move_right), desc="Move window to the right"),
    Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move window down"),
    Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),
    # mod1 is alt key
    Key(["mod1", "shift"], "4", lazy.spawn('flameshot gui'), desc="screenshot"),
    # Grow windows. If current window is on the edge of screen and direction
    # will be to screen edge - window would shrink.
    Key([mod], "t", lazy.spawn('alacritty'), desc="Launch terminal"),
    Key([mod], "q", lazy.window.kill(), desc="Kill focused window"),
    Key([mod, "control"], "r", lazy.restart(), desc="Reload the config"),
    Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
    Key([mod], "r", rofi.show())
]

groups: List[Group] = []

WorkspaceNumberKey = Literal["1", "2", "3", "4", "5"]

main_groups: Dict[WorkspaceNumberKey, Group] = dict([(i, Group(name=f'M{i}', screen_affinity=MAIN_SCREEN_IDX)) for i in get_args(WorkspaceNumberKey)])
groups.extend(main_groups.values())

left_groups: Dict[WorkspaceNumberKey, Group] = dict([(i, Group(name=f'L{i}', screen_affinity=LEFT_SCREEN_IDX)) for i in get_args(WorkspaceNumberKey)])
groups.extend(left_groups.values())

right_groups: Dict[WorkspaceNumberKey, Group] = dict([(i, Group(name=f'R{i}', screen_affinity=RIGHT_SCREEN_IDX)) for i in get_args(WorkspaceNumberKey)])
groups.extend(right_groups.values())

work_groups = [
    Group(name=W1_GROUP, screen_affinity=WORK_SCREEN_IDX, matches=[Match(title=WORK_VM_WIN_1_NAME, wm_class=WORK_VM_WM_CLASS)]),
    Group(name=W2_GROUP, screen_affinity=MAIN_SCREEN_IDX, matches=[Match(wm_class=WORK_VM_WM_CLASS)]),
    Group(name=MBP_GROUP, screen_affinity=MAIN_SCREEN_IDX, matches=[Match(title=WORK_MBP_WIN_NAME)]),
]
groups.extend(work_groups)

def _w1(_qtile):
    _qtile.focus_screen(WORK_SCREEN_IDX)
    _qtile.current_screen.set_group(_qtile.groups_map.get(W1_GROUP))

def _w2(_qtile):
    _qtile.focus_screen(MAIN_SCREEN_IDX)
    _qtile.current_screen.set_group(_qtile.groups_map.get(W2_GROUP))

def _mbp(_qtile):
    _qtile.focus_screen(MAIN_SCREEN_IDX)
    _qtile.current_screen.set_group(_qtile.groups_map.get(MBP_GROUP))

last_main_group = None

@hook.subscribe.setgroup
def set_last_main_group(*_):
    global last_main_group
    group_name = qtile.current_screen.group.name
    if group_name in [g.name for g in main_groups.values()] and last_main_group != group_name:
        last_main_group = group_name

def _main_screen(_qtile):
    global last_main_group
    _qtile.focus_screen(MAIN_SCREEN_IDX)
    if last_main_group is not None and _qtile.current_screen.group.name != last_main_group:
        _qtile.screens[MAIN_SCREEN_IDX].toggle_group(last_main_group)

def get_group_for_current_screen(_qtile, number: WorkspaceNumberKey) -> _Group:
    if _qtile.current_screen == _qtile.screens[MAIN_SCREEN_IDX]:
        return _qtile.groups_map.get(main_groups[number].name)
    elif _qtile.current_screen == _qtile.screens[LEFT_SCREEN_IDX]:
        return _qtile.groups_map.get(left_groups[number].name)
    elif _qtile.current_screen == _qtile.screens[RIGHT_SCREEN_IDX]:
        return _qtile.groups_map.get(right_groups[number].name)
    else:
        raise ValueError(
            f"current_screen is not in screens: {_qtile.current_screen}"
        )

def group_switch(number: WorkspaceNumberKey) -> LazyCall:
    def _switch(_qtile):
        _group = get_group_for_current_screen(_qtile, number)
        if _group:
            _qtile.current_screen.set_group(_group)
    return lazy.function(_switch)

def move_window_to_group(number: WorkspaceNumberKey) -> LazyCall:
    def _move(_qtile):
        _group = get_group_for_current_screen(_qtile, number)
        if _group:
            _qtile.current_window.togroup(_group.name)
    return lazy.function(_move)

for number_key in get_args(WorkspaceNumberKey):
    keys.extend([
        Key(
            [mod],
            number_key,
            group_switch(number_key),
            desc=f"Switch to group {number_key}"
        ),
        Key(
            [mod, "shift"],
            number_key,
            move_window_to_group(number_key),
            desc=f"Switch to group {number_key}"
        ),
    ])

keys.extend([
    Key([mod], "grave",
        lazy.function(_main_screen),
        desc="last main group"
        ),
    Key([], 'XF86Search',
        lazy.function(_mbp),
        desc="focus on mbp"
    ),
    Key(['mod1', "control"], "9",
        lazy.function(_w1),
        desc="W1"
    ),
    Key(['mod1', "control"], "0",
        lazy.function(_w2),
        desc="W2",
    ),
    Key([mod, 'control'], 'l',
        lazy.spawn('lock', shell=True),
        desc='Lock screen',
    ),
])

layouts: List[Layout] = [
    layout.Max(),
]

widget_defaults: dict = get_widget_defaults()
extension_defaults = widget_defaults.copy()

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


# 5120 x 1440
# 1280x1440,2560x1440,1280x1440
# 1280x1440+0+0,2560x1440+1280+0,1280x1440+3840+0
fake_screens: List[Screen] = []
fake_screens.insert(MAIN_SCREEN_IDX, Screen(
    background="#555",
    top=bar.Bar(
        widgets=[
            widget.GroupBox(visible_groups=[g.name for g in main_groups.values()]),
            CustomTaskList(
                parse_text=lambda x: '',
                stretch=False,
                window_name_location=True,
            ),
            widget.WindowName(),
            widget.Clock(format="%a %b %d %I:%M:%S %p"),
            widget.Spacer(),
            widget.GroupBox(
                visible_groups=[g.name for g in work_groups],
                active="#B283D4",
            ),
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
            widget.GroupBox(visible_groups=[g.name for g in left_groups.values()]),
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
            widget.GroupBox(visible_groups=[g.name for g in right_groups.values()]),
            CustomTaskList(
                parse_text=lambda x: '',
                stretch=False,
                window_name_location=True,
            ),
            widget.WindowName(),
        ], size=24, background=ACTIVE_BAR, ),
    x=3840, y=0, width=1280, height=1440,
))
fake_screens.insert(WORK_SCREEN_IDX, Screen(
    background="#00000000",
    x=0, y=0, width=5120, height=1440,
))

# Drag floating layouts.
mouse: List[Mouse] = get_default_mouse(mod)
dgroups_key_binder = None
dgroups_app_rules = []  # type: list
follow_mouse_focus = False
bring_front_click: bool = False
floats_kept_above: bool = True
cursor_warp: bool = True
floating_layout: layout.Floating = layout.Floating(
   float_rules=[
       *layout.Floating.default_float_rules,
       *get_default_floating(),
   ]
)
auto_fullscreen: bool = True
focus_on_window_activation = "smart"
reconfigure_screens: bool = True
auto_minimize = True
wmname = "LG3D"
