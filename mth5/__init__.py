# package file

import logging
from mth5.utils.mth5logger import MTH5Logger

__version__ = '0.0.1'

MTH5Logger.load_config()

logging.getLogger(__name__).addHandler(logging.NullHandler())

# from mth5.utils import mth5logger

# mth5logger.MTH5Logger.load_config()
# logger = mth5logger.MTH5Logger.get_logger(__name__)
# logger.info("Initiating Logger for MTH5")
