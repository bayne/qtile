import asyncio
import subprocess
from typing import List

from libqtile import bar
from libqtile import hook
from libqtile import layout
from libqtile import log_utils
from libqtile import qtile
from libqtile import widget
from libqtile.config import Group
from libqtile.config import Key
from libqtile.config import Mouse
from libqtile.config import Screen
from libqtile.layout.base import Layout
from libqtile.lazy import lazy

from bayne import systemd_logging
from bayne.default import get_default_floating
from bayne.default import get_default_keys
from bayne.default import get_default_layouts
from bayne.default import get_default_mouse
from bayne.default import get_default_switch_group_keys
from bayne.default import get_widget_defaults
from bayne.hooks import active_popup
from bayne.hooks import disable_screensaver
from bayne.hooks import popover
from bayne.rofi import Rofi
from bayne.rofi import RofiScript

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

logger = log_utils.logger


@hook.subscribe.client_new
@hook.subscribe.client_name_updated
async def new_work_viewer(client):
    if "DeckLink Quad HDMI Recorder (1)" in client.name:
        client.togroup(MBP_GROUP)
    if "remote-viewer" in client.get_wm_class():
        if "work (1)" in client.name:
            client.togroup(W1_GROUP)
            qtile.groups[9].toscreen(0)
            await asyncio.sleep(1.0)
            qtile.spawn(['xdotool', 'key', 'F11'])
        elif "work (2)" in client.name:
            client.togroup(W2_GROUP)

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
# https://github.com/qtile/qtile/blob/master/libqtile/backend/x11/xkeysyms.py
keys = get_default_keys(mod, rofi)

groups = [Group(name=i, screen_affinity=0) for i in "123456789"]
groups.append(Group(name=W1_GROUP, screen_affinity=0))
groups.append(Group(name=W2_GROUP, screen_affinity=0))
groups.append(Group(name=MBP_GROUP, screen_affinity=0))
keys.extend(get_default_switch_group_keys(mod, 9))
keys.extend([
    Key([], 'XF86Search',
        lazy.group[MBP_GROUP].toscreen(),
        lazy.group[MBP_GROUP].focus_by_name('DeckLink Quad HDMI Recorder (1)'),
        desc="focus on mbp"
        ),
    Key(['mod1', "control"], "9", lazy.group[W1_GROUP].toscreen(), desc="W1"),
    Key(['mod1', "control"], "0",
        lazy.group[W2_GROUP].toscreen(),
        lazy.group[W2_GROUP].focus_by_name('work (2)'),
        desc="W2",
    ),
    Key([mod, 'control'], 'l',
        lazy.spawn('lock', shell=True),
        desc='Lock screen',
    ),
])

layouts: List[Layout] = get_default_layouts()

widget_defaults: dict = get_widget_defaults()
extension_defaults = widget_defaults.copy()

screens: List[Screen] = [
    Screen(
        background="#555",
        top=bar.Bar(
            widgets=[
                widget.GroupBox(),
                widget.WindowName(),
                widget.Clock(format="%a %b %d %I:%M:%S %p"),
                widget.Spacer(),
                widget.TextBox(fmt="🌐",),
                widget.NetGraph(
                    type='line',
                    margin_x=0,
                    margin_y=0,
                    border_width=0,
                ),
                widget.TextBox(fmt="⚙️",),
                widget.CPUGraph(
                    type='line',
                    margin_x=0,
                    margin_y=0,
                    border_width=0,
                ),
                widget.TextBox(fmt="🔲",),
                widget.MemoryGraph(
                    type='line',
                    margin_x=0,
                    margin_y=0,
                    border_width=0,
                ),
                widget.Systray(),
            ],
            size=24,
            background="#222",
        ),
    )
]

# Drag floating layouts.
mouse: List[Mouse] = get_default_mouse(mod)
dgroups_key_binder = None
dgroups_app_rules = []  # type: list
follow_mouse_focus = False
bring_front_click: bool = False
floats_kept_above: bool = True
cursor_warp: bool = False
floating_layout: layout.Floating = layout.Floating(
   float_rules=[
       *layout.Floating.default_float_rules,
       *get_default_floating(),
   ]
)
auto_fullscreen: bool = True
focus_on_window_activation: bool = "smart"
reconfigure_screens: bool = True
auto_minimize = True
wmname = "LG3D"
