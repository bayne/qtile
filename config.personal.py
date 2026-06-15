import os
import re
import subprocess
from re import Pattern

from pystemd.dbuslib import DBus
from pystemd.systemd1 import Unit

from bayne import systemd_logging
from bayne.default import get_default_floating
from bayne.default import get_default_mouse
from bayne.dqhd_workflow import DQHDWorkflow
from bayne.dqhd_workflow import EnvGroup
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

active_popup.init(
    [
        "opensnitch-ui",
    ]
)
popover.init(
    restack=[
        "jetbrains-idea",
    ]
)
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

    with DBus(user_mode=True) as bus:
        u = Unit("xephyr.service", bus=bus)
        u.load()
        u.Unit.Start(b"replace")



ACTIVE_BAR = "#222222FF"
INACTIVE_BAR = "#444444FF"
MOD = "mod4"

WORK_VM_WM_CLASS = "remote-viewer"

WORK_VM_WIN_1_NAME = "work (1)"
WORK_VM_WIN_2_NAME = "work (2)"
WORK_MBP_WIN_NAME = "work_mbp"
WORK_XEPHYR1_PATTERN: Pattern = re.compile(r"^Xephyr on :1.0")

WORK_WINDOW_NAMES = [WORK_VM_WIN_1_NAME, WORK_VM_WIN_2_NAME, WORK_MBP_WIN_NAME]

logger = log_utils.logger

MAIN_SCREEN_IDX = 0
LEFT_SCREEN_IDX = 1
RIGHT_SCREEN_IDX = 2
WORK_SCREEN_IDX = 3

dqhd_workflow = DQHDWorkflow(
    active_bar=ACTIVE_BAR,
    inactive_bar=INACTIVE_BAR,
    warp=True,
    theme_mode="preferred",
)
dqhd_workflow.register_hooks()


@hook.subscribe.client_new
def on_client_new(client):
    logger.info(f"client new: {client.name}")


@hook.subscribe.client_urgent_hint_changed
def on_urgent_hint_change(client):
    logger.info(f"client urgent hint changed: {client.name}")


@hook.subscribe.current_screen_change
def on_screen_change_hide_work_group():
    if (
        qtile.current_screen != qtile.screens[WORK_SCREEN_IDX]
        or qtile.current_group.name != EnvGroup.W1_GROUP
    ):
        qtile.groups_map[EnvGroup.W1_GROUP].hide()


env = os.environ.copy()
env.update({"PATH": env["PATH"] + ":/home/bpayne/.bin"})
rofi = Rofi(
    [
        RofiScript(
            name="intellij", path="/home/bpayne/Code/mine/dotfile/rofi-scripts/jetbrains.py"
        ),
        RofiScript(
            name="bookmark", path="/home/bpayne/Code/mine/dotfile/rofi-scripts/bookmarks.py"
        ),
    ]
)

groups: list[Group] = [*dqhd_workflow.groups()]

work_groups = [
    Group(
        name=EnvGroup.W1_GROUP,
        screen_affinity=WORK_SCREEN_IDX,
        matches=[
            Match(title=WORK_VM_WIN_1_NAME, wm_class=WORK_VM_WM_CLASS),
            Match(title=WORK_XEPHYR1_PATTERN),
        ],
    ),
    Group(
        name=EnvGroup.W2_GROUP,
        screen_affinity=MAIN_SCREEN_IDX,
        matches=[Match(wm_class=WORK_VM_WM_CLASS)],
    ),
    Group(
        name=EnvGroup.MBP_GROUP,
        screen_affinity=MAIN_SCREEN_IDX,
        matches=[Match(title=WORK_MBP_WIN_NAME)],
    ),
]
groups.extend(work_groups)


def get_keys(mod):

    def rebind_mod(new_mod):
        qtile.ungrab_keys()
        for key in get_keys(new_mod):
            qtile.grab_key(key)
        logger.info(f"rebind mod to {mod}")

    def focus_on_env(env_group: EnvGroup):
        def get_screen_and_key():
            match env_group:
                case EnvGroup.W1_GROUP:
                    return WORK_SCREEN_IDX, "mod5"
                case EnvGroup.W2_GROUP:
                    return MAIN_SCREEN_IDX, "mod5"
                case EnvGroup.MBP_GROUP:
                    return MAIN_SCREEN_IDX, "mod4"
                case EnvGroup.PERSONAL:
                    return MAIN_SCREEN_IDX, "mod4"

        def handler(_qtile):
            screen_idx, mod_key = get_screen_and_key()
            if env_group != EnvGroup.PERSONAL:
                _qtile.focus_screen(screen_idx)
                _qtile.current_screen.set_group(_qtile.groups_map.get(env_group))
                if _qtile.current_window:
                    _qtile.current_window.bring_to_front()
            rebind_mod(mod_key)

        return lazy.function(handler)

    return [
        *dqhd_workflow.keys(mod),
        # mod1 is alt key
        Key(["mod1", "shift"], "4", lazy.spawn("flameshot gui"), desc="screenshot"),
        Key([mod], "q", lazy.window.kill(), desc="Kill focused window"),
        Key([mod, "control"], "r", lazy.restart(), desc="Reload the config"),
        Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
        Key([mod], "r", rofi.show()),
        Key([], "Help", focus_on_env(EnvGroup.PERSONAL), desc="focus on personal"),
        Key([], "XF86Search", focus_on_env(EnvGroup.MBP_GROUP), desc="focus on mbp"),
        Key(["mod1", "control"], "9", focus_on_env(EnvGroup.W1_GROUP), desc="W1"),
        Key(
            ["mod1", "control"],
            "0",
            focus_on_env(EnvGroup.W2_GROUP),
            desc="W2",
        ),
        Key(
            [mod, "control"],
            "l",
            lazy.spawn("lock", shell=True),
            desc="Lock screen",
        ),
    ]

# https://github.com/qtile/qtile/blob/master/libqtile/backend/x11/xkeysyms.py
keys = get_keys(MOD)

layouts: list[Layout] = dqhd_workflow.layouts()

# 5120 x 1440
# 1280x1440,2560x1440,1280x1440
# 1280x1440+0+0,2560x1440+1280+0,1280x1440+3840+0
fake_screens: list[Screen] = dqhd_workflow.fake_screens(
    extra_widgets=[
        widget.Spacer(),
        widget.GroupBox(
            visible_groups=[g.name for g in work_groups],
            active="#B283D4FF",
        ),
    ]
)
fake_screens.insert(
    WORK_SCREEN_IDX,
    Screen(
        background="#00000000",
        x=0,
        y=0,
        width=5120,
        height=1440,
    ),
)

# Drag floating layouts.
mouse: list[Mouse] = get_default_mouse(MOD)
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
