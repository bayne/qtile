import os
import subprocess
from typing import List

from bayne import systemd_logging
from bayne.default import get_default_floating
from bayne.default import get_default_mouse
from bayne.dqhd_workflow import DQHDWorkflow
from bayne.hooks import active_popup
from bayne.hooks import disable_screensaver
from bayne.hooks import popover
from bayne.rofi import Rofi
from bayne.rofi import RofiScript
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
from libqtile.layout.base import Layout
from libqtile.lazy import lazy

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
mod = "mod4"

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

dqhd_workflow = DQHDWorkflow(
    active_bar=ACTIVE_BAR,
    inactive_bar=INACTIVE_BAR,
    mod=mod
)
dqhd_workflow.register_hooks()

@hook.subscribe.current_screen_change
def on_screen_change_hide_work_group():
    if qtile.current_screen != qtile.screens[WORK_SCREEN_IDX] or qtile.current_group.name != W1_GROUP:
        qtile.groups_map[W1_GROUP].hide()

env = os.environ.copy()
env.update({'PATH': env['PATH'] + ':/home/bpayne/.bin'})
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
# https://github.com/qtile/qtile/blob/master/libqtile/backend/x11/xkeysyms.py
keys = [
    *dqhd_workflow.keys(),
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

groups: List[Group] = [
    *dqhd_workflow.groups()
]

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

keys.extend([
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

layouts: List[Layout] = dqhd_workflow.layouts()

# 5120 x 1440
# 1280x1440,2560x1440,1280x1440
# 1280x1440+0+0,2560x1440+1280+0,1280x1440+3840+0
fake_screens: List[Screen] = dqhd_workflow.fake_screens(extra_widgets=[
    widget.Spacer(),
    widget.GroupBox(
        visible_groups=[g.name for g in work_groups],
        active="#B283D4",
    ),
])
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
