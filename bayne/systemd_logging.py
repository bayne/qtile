import logging
from libqtile import log_utils
from systemd.journal import JournalHandler

def init():
    logger = log_utils.logger
    journal_handlers = filter(lambda h: isinstance(h, JournalHandler), logger.handlers,)
    if len(list(journal_handlers)) > 0:
        logger.info("systemd logging already initialized")
        return
    logger.setLevel(logging.INFO)
    journal_handler = JournalHandler()
    journal_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(journal_handler)