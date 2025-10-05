import os
from typing import Iterable
from typing import List

from libqtile import hook
from libqtile import layout
from libqtile import log_utils
from libqtile import qtile
from libqtile.config import Click
from libqtile.config import Drag
from libqtile.config import Key
from libqtile.config import Match
from libqtile.lazy import lazy

from bayne.rofi import Rofi
from bayne.rofi import RofiScript

logger = log_utils.logger

def get_default_rofi():
    return Rofi(
        [
            RofiScript(
                name="intellij",
                path="/home/bpayne/Code/mine/dotfile/rofi-scripts/jetbrains.py"
            )
        ]
    )

def get_default_keys(mod: str, rofi: Rofi = None) -> List[Key]:
    env = os.environ.copy()
    env.update({'PATH': env['PATH'] + ':/home/bpayne/.bin'})
    rofi = Rofi([]) if rofi is None else rofi
    return [
        Key([mod], "h", lazy.layout.left(), desc="Move focus to left"),
        Key([mod], "l", lazy.layout.right(), desc="Move focus to right"),
        Key([mod], "j", lazy.layout.down(), desc="Move focus down"),
        Key([mod], "k", lazy.layout.up(), desc="Move focus up"),
        Key([mod], "Tab", lazy.layout.next(), desc="Move window focus to next window"),
        Key([mod, "shift"], "Tab", lazy.layout.previous(), desc="Move window focus to prev window"),
        Key([mod, "shift"], "h", lazy.layout.shuffle_left(), desc="Move window to the left"),
        Key([mod, "shift"], "l", lazy.layout.shuffle_right(), desc="Move window to the right"),
        Key([mod, "shift"], "j", lazy.layout.shuffle_down(), desc="Move window down"),
        Key([mod, "shift"], "k", lazy.layout.shuffle_up(), desc="Move window up"),
        # mod1 is alt key
        Key(["mod1", "shift"], "4", lazy.spawn('flameshot gui'), desc="screenshot"),
        # Grow windows. If current window is on the edge of screen and direction
        # will be to screen edge - window would shrink.
        Key([mod], "n", lazy.layout.normalize(), desc="Reset all window sizes"),
        Key([mod], "t", lazy.spawn('alacritty'), desc="Launch terminal"),
        Key([mod], "q", lazy.window.kill(), desc="Kill focused window"),
        Key([mod, "control"], "r", lazy.reload_config(), desc="Reload the config"),
        Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
        Key([mod], "r", rofi.show())
    ]



default_groups = []
last_default_group = None

@hook.subscribe.setgroup
def change_group(*args):
    global last_default_group
    group_name = qtile.current_screen.group.name
    if group_name in default_groups and last_default_group != group_name:
        last_default_group = group_name

@lazy.function
def toggle_last_default_group(e):
    global last_default_group
    if last_default_group is not None and qtile.current_screen.group.name != last_default_group:
        qtile.screens[0].toggle_group(last_default_group)

def get_default_switch_group_keys(mod, count) -> Iterable[Key]:
    global last_default_group
    global default_groups
    default_groups = range(1, count + 1)
    default_groups = map(str, default_groups)
    default_groups = list(default_groups)

    for i in default_groups:
        yield Key(
            [mod],
            str(i),
            lazy.group[str(i)].toscreen(0),
            desc="Switch to group {}".format(i),
        )
        yield Key(
            [mod, "shift"],
            str(i),
            lazy.window.togroup(str(i), switch_group=False),
            desc="Switch to & move focused window to group {}".format(i),
        )
    yield Key([mod], "grave", toggle_last_default_group, desc="last group")

def get_widget_defaults() -> dict:
    return dict(
        font="sans",
        fontsize=12,
        padding=3,
    )

def get_default_floating() -> List[Match]:
    return [
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(wm_class="floatingvim"),  # gitk
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
    ]

def get_default_mouse(mod):
    return [
        Drag([mod], "Button1", lazy.window.set_position_floating(), start=lazy.window.get_position()),
        Drag([mod], "Button3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
        Click([mod], "Button2", lazy.window.bring_to_front()),
    ]

def get_default_layouts():
    return [
        layout.MonadThreeCol(auto_maximize=True),
    ]
