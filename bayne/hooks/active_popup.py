import asyncio
from typing import List

from libqtile.hook import qtile_hooks
from libqtile.log_utils import logger

def _create_hook(wm_classes):
    async def hook(client):
        if (set(wm_classes) & set(client.get_wm_class())):
            await asyncio.sleep(0.5)
            client.togroup(client.qtile.current_group.name, switch_group=False)
    return hook

def init(wm_classes: List[str]):
    logger.info("Initializing active popup hook")
    hook = _create_hook(wm_classes)
    qtile_hooks.subscribe.client_managed(hook)