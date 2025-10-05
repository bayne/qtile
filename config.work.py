import subprocess
from typing import List

from libqtile import bar
from libqtile import hook
from libqtile import layout
from libqtile import log_utils
from libqtile import widget
from libqtile.config import Click
from libqtile.config import Drag
from libqtile.config import Group
from libqtile.config import Key
from libqtile.config import Match
from libqtile.config import Screen
from libqtile.layout.base import Layout
from libqtile.lazy import lazy

from bayne import systemd_logging
from bayne.default import get_default_floating
from bayne.default import get_default_keys
from bayne.default import get_default_layouts
from bayne.default import get_default_switch_group_keys
from bayne.default import get_widget_defaults
from bayne.hooks import active_popup
from bayne.hooks import disable_screensaver
from bayne.hooks import popover
from bayne.rofi import Rofi, RofiScript
from bayne.widgets.outlook_checker import OutlookChecker

logger = log_utils.logger

active_popup.init([
    'opensnitch-ui',
])
popover.init(restack=[
    'jetbrains-idea',
])
systemd_logging.init()
disable_screensaver.init()

BORDER_FOCUS="#CC1111"
BORDER_NORMAL="#440000"

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
    subprocess.run(["/home/bpayne/.screenlayout/default.sh"])

mod: str = "mod4"

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
keys: List[Key] = get_default_keys(mod, rofi)

groups: List[Group] = [Group(name=i, screen_affinity=0) for i in "12345678"]
keys.extend(get_default_switch_group_keys(mod, 8))
keys.extend([
    Key([mod, "control"], "l", lazy.screen.next_group(), desc="next"),
    Key([mod, "control"], "h", lazy.screen.prev_group(), desc="prev"),
    Key([], "XF86AudioRaiseVolume", lazy.to_screen(0), desc="main screen"),
    Key([], "XF86AudioLowerVolume", lazy.to_screen(1), desc="off screen"),
])

groups.append(Group(
    name="9",
    screen_affinity=1,
    layouts=[layout.Max()],
))
keys.extend(
    [
        Key(
            [mod, "shift"],
            "9",
            lazy.window.togroup("9", switch_group=False),
            lazy.group["9"].toscreen(1),
            desc="move focused window to group 9",
        ),
    ]
)

layouts: List[Layout] = get_default_layouts()

widget_defaults = get_widget_defaults()
extension_defaults = widget_defaults.copy()

screens = [
    Screen(
        background="#555",
        top=bar.Bar(
            widgets=[
                widget.GroupBox(),
                widget.WindowName(),
                widget.Clock(format="%a %b %d %I:%M:%S %p"),
                OutlookChecker(),
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
            size=20,
            background="#591a7d",
        ),
    ),
    Screen(
        width=1920,
        height=1080,
        background="#333",
    )
]

# Drag floating layouts.
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

dgroups_key_binder = None
dgroups_app_rules = []  # type: list
follow_mouse_focus = False
bring_front_click = False
floats_kept_above = True
cursor_warp = True
floating_layout = layout.Floating(
    float_rules=[
        *layout.Floating.default_float_rules,
        *get_default_floating(),
        Match(wm_class="center-modal"),
        Match(wm_class="gpauth"),
    ]
)
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True
auto_minimize = True
wmname = "LG3D"
