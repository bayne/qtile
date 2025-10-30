import os
import subprocess
from typing import List

from bayne import systemd_logging
from bayne.default import get_default_floating
from bayne.default import get_default_mouse
from bayne.dqhd_workflow import DQHDWorkflow
from bayne.dqhd_workflow import MAIN_SCREEN_IDX
from bayne.hooks import active_popup
from bayne.hooks import disable_screensaver
from bayne.hooks import popover
from bayne.rofi import Rofi
from bayne.rofi import RofiScript
from bayne.widgets.outlook_checker import OutlookChecker
from libqtile import hook
from libqtile import layout
from libqtile import log_utils
from libqtile import widget
from libqtile.config import Group
from libqtile.config import Key
from libqtile.config import Match
from libqtile.config import Mouse
from libqtile.config import Screen
from libqtile.layout.base import Layout
from libqtile.lazy import lazy

logger = log_utils.logger

active_popup.init([
    'opensnitch-ui',
])
popover.init(restack=[
    'jetbrains-idea',
])
systemd_logging.init()
disable_screensaver.init()

@hook.subscribe.startup_once
def startup():
    subprocess.Popen(["/usr/lib/policykit-1-gnome/polkit-gnome-authentication-agent-1"])
    # home dir backup
    subprocess.Popen(["/usr/bin/vorta"])
    # screenshot
    subprocess.Popen(["gtk-launch", "org.flameshot.Flameshot"])
    # egress firewall
    subprocess.Popen(["gtk-launch", "opensnitch_ui"])
    subprocess.run(["/usr/bin/systemctl", "--user", "start", "spice-vdagent"])


ACTIVE_BAR = "#591a7d"
INACTIVE_BAR = "#55475E"

mod = "mod4"
dqhd_workflow = DQHDWorkflow(
    active_bar=ACTIVE_BAR,
    inactive_bar=INACTIVE_BAR,
    mod=mod,
    warp=True,
    theme_mode='fallback',
)
dqhd_workflow.register_hooks()

SHARE_SCREEN_IDX = 3

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

env = os.environ.copy()
env.update({'PATH': env['PATH'] + ':/home/bpayne/.bin'})
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

share_group: Group = Group(name="SH", screen_affinity=SHARE_SCREEN_IDX, layouts=[layout.Max()])
groups.append(share_group)

keys.extend([
    Key([], "XF86AudioRaiseVolume", lazy.to_screen(MAIN_SCREEN_IDX), desc="move to main screen"),
    Key([], "XF86AudioLowerVolume", lazy.to_screen(SHARE_SCREEN_IDX), desc="move to share screen"),
])

keys.extend(
    [
        Key(
            [mod, "shift"],
            "9",
            lazy.window.togroup(share_group.name, switch_group=False),
            desc="move focused window to group 9",
        ),
    ]
)

layouts: List[Layout] = dqhd_workflow.layouts()

# Top:5120x1440 (split into: 1280x1440,2560x1440,1280x1440)  Bottom:1920x1080 (no split)
# 1280x1440+0+0, 2560x1440+1280+0, 1280x1440+3840+0, 1920x1080+0+1440
fake_screens: List[Screen] = [
    *dqhd_workflow.fake_screens(extra_widgets=[
        OutlookChecker(),
        widget.Spacer(),
    ]),
]
fake_screens.insert(SHARE_SCREEN_IDX, Screen(
    background="#333",
    x=0, y=1440, width=1920, height=1080,
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
       Match(wm_class="center-modal"),
       Match(wm_class="gpauth"),
   ]
)
auto_fullscreen: bool = True
focus_on_window_activation = "smart"
reconfigure_screens: bool = True
auto_minimize = True
wmname = "LG3D"
