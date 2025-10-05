import subprocess
from typing import List

from libqtile import bar
from libqtile import hook
from libqtile import layout
from libqtile import log_utils
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
from bayne.default import get_default_mouse
from bayne.default import get_default_rofi
from bayne.default import get_default_switch_group_keys
from bayne.hooks import active_popup
from bayne.hooks import popover

BORDER_FOCUS="#CC1111"
BORDER_NORMAL="#440000"

active_popup.init([
    'opensnitch-ui',
])
popover.init(restack=[
    'jetbrains-idea',
])
systemd_logging.init()

@hook.subscribe.startup_once
def startup():
    subprocess.Popen(["/usr/lib/policykit-1-gnome/polkit-gnome-authentication-agent-1"])
    # home dir backup
    subprocess.Popen(["/usr/bin/vorta"])
    # screenshot
    subprocess.Popen(["gtk-launch", "org.flameshot.Flameshot"])
    # egress firewall
    subprocess.Popen(["gtk-launch", "opensnitch_ui"])


logger = log_utils.logger

rofi = get_default_rofi()

mod = "mod4"

# https://github.com/qtile/qtile/blob/master/libqtile/backend/x11/xkeysyms.py
keys = get_default_keys(mod, rofi)

groups = [Group(name=i, screen_affinity=0) for i in "123456789"]
keys.extend(get_default_switch_group_keys(mod, 9))
keys.extend([
    Key([], 'XF86MonBrightnessUp', lazy.spawn('sudo light -A 10'), desc='Increase brightness'),
    Key([], 'XF86MonBrightnessDown', lazy.spawn('sudo light -U 10'), desc='Decrease brightness'),
    Key([], 'XF86AudioMute',
        lazy.spawn('wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle'),
        lazy.spawn('pw-play /usr/share/sounds/freedesktop/stereo/audio-volume-change.oga'),
        desc='Mute',
    ),
    Key([], 'XF86AudioLowerVolume',
        lazy.spawn('wpctl set-volume @DEFAULT_AUDIO_SINK@ 10%- -l 1.0'),
        lazy.spawn('pw-play /usr/share/sounds/freedesktop/stereo/audio-volume-change.oga'),
        desc='Decrease volume',
    ),
    Key([], 'XF86AudioRaiseVolume',
        lazy.spawn('wpctl set-volume @DEFAULT_AUDIO_SINK@ 10%+ -l 1.0'),
        lazy.spawn('pw-play /usr/share/sounds/freedesktop/stereo/audio-volume-change.oga'),
        desc='Increase volume',
    ),
    Key([mod, 'control'], 'l',
        lazy.spawn('lock'),
        desc='Lock screen',
    ),
    Key([mod], 'm', lazy.next_layout(), desc='Next layout'),
])

layouts: List[Layout] = [
    layout.bsp.Bsp(
        border_focus=BORDER_FOCUS,
        border_normal=BORDER_NORMAL,
        wrap_clients=True,
    ),
    layout.Max(),
]

widget_defaults: dict = dict(
    font="sans",
    fontsize=18,
    padding=3,
)
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
                widget.Backlight(
                    background='#551',
                    fmt='☀️{}',
                    backlight_name='amdgpu_bl0'
                ),
                widget.PulseVolume(
                    emoji=False,
                    fmt='🔊{}',
                    background='#135',
                ),
                widget.Battery(
                    background='#133',
                    format='{char} {percent:2.0%} {hour:d}h{min:02d}m',
                    charge_char='🔌',
                    discharge_char='🔋',
                ),
                widget.Systray(),
            ],
            size=32,
            background="#222",
        ),
        bottom=bar.Bar(
            widgets=[
                widget.WindowTabs(
                    parse_text=lambda name: '█',
                    fmt=f'<span fgcolor="{BORDER_NORMAL}">{"{}"}</span>',
                    separator='',
                    selected=(f'<span fgcolor="{BORDER_FOCUS}">', '</span>'),
                ),
                widget.Spacer(),
                widget.TextBox(fmt="🌐",),
                widget.NetGraph(
                    type='line',
                ),
                widget.TextBox(fmt="⚙️",),
                widget.CPUGraph(
                    type='line',
                ),
                widget.TextBox(fmt="🔲",),
                widget.MemoryGraph(),
            ],
            size=32,
            background="#222",
        )
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
