from asyncio import subprocess

from libqtile.hook import qtile_hooks
from libqtile.log_utils import logger


def _create_hook():
    async def hook():
        ## disabling screensaver due to issues with screen not turning back on
        # disable screensaver
        await subprocess.create_subprocess_exec("/usr/bin/xset", "s", "off")
        # disable energy star features (related to screensaver)
        await subprocess.create_subprocess_exec("/usr/bin/xset", "-dpms")

    return hook

def init():
    logger.info("Initializing screensaver disable hook")
    hook = _create_hook()
    qtile_hooks.subscribe.startup(hook)