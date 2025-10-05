import asyncio
from typing import List

from libqtile.hook import qtile_hooks
from libqtile.log_utils import logger

def _create_restack_hook(wm_classes):
    async def hook(client):
        if (set(wm_classes) & set(client.get_wm_class())) and client.has_focus:
            await asyncio.sleep(0.5)
            client.bring_to_front()
    return hook

def init(restack: List[str]):
    logger.info("Initializing restack hook")
    restack_hook = _create_restack_hook(restack)
    qtile_hooks.subscribe.client_managed(restack_hook)