import os
import re
import subprocess
from re import Pattern
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

ACTIVE_BAR = "#222222FF"
INACTIVE_BAR = "#444444FF"
mod = "mod4"

WORK_VM_WM_CLASS = 'remote-viewer'

WORK_VM_WIN_1_NAME = 'work (1)'
WORK_VM_WIN_2_NAME = 'work (2)'
WORK_MBP_WIN_NAME = 'work_mbp'
WORK_XEPHYR_PATTERN: Pattern = re.compile(r'Xephyr.*')

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

def components(group: Group | str):
    name = group if isinstance(group, str) else group.name
    return name[0], int(name[1:])

def get_screen_idx(group: Group):
    match components(group):
        case 'M', _: return MAIN_SCREEN_IDX
        case 'L', _: return LEFT_SCREEN_IDX
        case 'R', _: return RIGHT_SCREEN_IDX
        case _: return MAIN_SCREEN_IDX

def focus(window):
    if not window.group:
        return
    group = window.group
    screen_idx = get_screen_idx(group)

    qtile.focus_screen(screen_idx)
    qtile.screens[screen_idx].set_group(group)
    group.focus(window)

dqhd_workflow = DQHDWorkflow(
    active_bar=ACTIVE_BAR,
    inactive_bar=INACTIVE_BAR,
    mod=mod,
    warp=True,
    theme_mode='preferred',
)
dqhd_workflow.register_hooks()

@hook.subscribe.client_new
def on_client_new(client):
    logger.info(f"client new: {client.name}")

@hook.subscribe.client_name_updated
def on_name_change(client):
    current_windows = filter(lambda s: s.group.current_window, qtile.screens)
    current_windows = list(map(lambda s: s.group.current_window.wid, current_windows))
    if client.wid not in current_windows:
        focus(client)

@hook.subscribe.client_urgent_hint_changed
def on_urgent_hint_change(client):
    logger.info(f"client urgent hint changed: {client.name}")

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

groups: List[Group] = [
    *dqhd_workflow.groups()
]

work_groups = [
    Group(name=W1_GROUP, screen_affinity=WORK_SCREEN_IDX, matches=[Match(title=WORK_VM_WIN_1_NAME, wm_class=WORK_VM_WM_CLASS), Match(title=WORK_XEPHYR_PATTERN)]),
    Group(name=W2_GROUP, screen_affinity=MAIN_SCREEN_IDX, matches=[Match(wm_class=WORK_VM_WM_CLASS)]),
    Group(name=MBP_GROUP, screen_affinity=MAIN_SCREEN_IDX, matches=[Match(title=WORK_MBP_WIN_NAME)]),
]
groups.extend(work_groups)

def _handle_terminal_key(_qtile):
    current_group = _qtile.current_group
    current_windows = filter(lambda s: s.group.current_window, _qtile.screens)
    current_windows = list(map(lambda s: s.group.current_window.wid, current_windows))

    def active_distance(w):
        return 0 if w['id'] in current_windows else 1

    def group_distance(w):
        _, n = components(w['group'])
        _, cn = components(current_group.name)
        return abs(n - cn)

    def screen_distance(w):
        group = components(w['group'])
        cg, cn = components(current_group.name)

        match group:
            case g, _ if g == cg: return 0
            case 'M', _: return 1
            case 'L', _: return 2
            case 'R', _: return 3
            case _: return 4

    def rank(w):
        return (
            active_distance(w),
            screen_distance(w),
            group_distance(w),
        )

    def find_closest():
        windows = _qtile.windows()
        windows = list(filter(lambda w: 'Alacritty' in w['wm_class'], windows))
        if not windows:
            return None
        wid = min(windows, key=lambda w: rank(w))['id']
        return _qtile.windows_map.get(wid)

    closest = find_closest()
    if closest:
        focus(closest)
    else:
        _qtile.spawn('alacritty')

def get_keys(__personal, __mbp, __w1, __w2, _mod):
    return [
        *dqhd_workflow.keys(),
        # mod1 is alt key
        Key(["mod1", "shift"], "4", lazy.spawn('flameshot gui'), desc="screenshot"),
        # Grow windows. If current window is on the edge of screen and direction
        # will be to screen edge - window would shrink.
        Key([_mod], "t", lazy.function(_handle_terminal_key), desc="Launch terminal"),
        Key([_mod], "q", lazy.window.kill(), desc="Kill focused window"),
        Key([_mod, "control"], "r", lazy.restart(), desc="Reload the config"),
        Key([_mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
        Key([_mod], "r", rofi.show()),

        Key([], 'Help',
            lazy.function(__personal),
            desc="focus on personal"
            ),

        Key([], 'XF86Search',
            lazy.function(__mbp),
            desc="focus on mbp"
            ),
        Key(['mod1', "control"], "9",
            lazy.function(__w1),
            desc="W1"
            ),
        Key(['mod1', "control"], "0",
            lazy.function(__w2),
            desc="W2",
            ),
        Key([mod, 'control'], 'l',
            lazy.spawn('lock', shell=True),
            desc='Lock screen',
            ),
    ]

def rebind_mod(new_mod):
    global mod
    global keys
    mod = new_mod
    dqhd_workflow.mod = mod
    keys = get_keys(_personal, _mbp, _w1, _w2, mod)
    qtile.ungrab_keys()
    for key in keys:
        qtile.grab_key(key)
    logger.info(f"rebind mod to {mod}")

def _w1(_qtile):
    _qtile.focus_screen(WORK_SCREEN_IDX)
    _qtile.current_screen.set_group(_qtile.groups_map.get(W1_GROUP))
    _qtile.current_window.bring_to_front()

    rebind_mod("mod5")

def _w2(_qtile):
    _qtile.focus_screen(MAIN_SCREEN_IDX)
    _qtile.current_screen.set_group(_qtile.groups_map.get(W2_GROUP))
    _qtile.current_window.bring_to_front()

    rebind_mod("mod5")

def _mbp(_qtile):
    _qtile.focus_screen(MAIN_SCREEN_IDX)
    _qtile.current_screen.set_group(_qtile.groups_map.get(MBP_GROUP))
    rebind_mod("mod4")
    _qtile.current_window.bring_to_front()

def _personal(_qtile):
    rebind_mod("mod4")

# https://github.com/qtile/qtile/blob/master/libqtile/backend/x11/xkeysyms.py
keys = get_keys(_personal, _mbp, _w1, _w2, mod)

layouts: List[Layout] = dqhd_workflow.layouts()

# 5120 x 1440
# 1280x1440,2560x1440,1280x1440
# 1280x1440+0+0,2560x1440+1280+0,1280x1440+3840+0
fake_screens: List[Screen] = dqhd_workflow.fake_screens(extra_widgets=[
    widget.Spacer(),
    widget.GroupBox(
        visible_groups=[g.name for g in work_groups],
        active="#B283D4FF",
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
