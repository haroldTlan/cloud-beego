import logging
import logging.config
import sys
from env import config, raw_config
import db
from caused import caused

logging.config.dictConfig(raw_config['log'])
logger = logging.getLogger('speedio')

def log_exc(func):
    def _log_exc(*vargs, **kv):
        try:
            ret = func(*vargs, **kv)
        except Exception as e:
            logger.error(caused(e).detail)
            raise e
        else:
            return ret
    return _log_exc

def debug(msg):
    logger.debug(msg)

def info(msg):
    logger.info(msg)

def warning(msg):
    logger.warning(msg)

def error(msg):
    logger.error(msg)

def critical(msg):
    logger.critical(msg)

def journal_info(message):
    db.Journal.create(level='info', message=message)

def journal_warning(message):
    db.Journal.create(level='warning', message=message)

def journal_critical(message):
    db.Journal.create(level='critical', message=message)
