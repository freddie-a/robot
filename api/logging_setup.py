"""Sets up logging for modules"""
import logging
import sys

def create_sublogger(level, path=None):
    """Sets up a sublogger"""
    formatter = logging.Formatter("%(asctime)s %(name)s %(process)d %(levelname)s %(message)s")
    if path is None:
        logger_handler = logging.StreamHandler(sys.stdout)
    else:
        logger_handler = logging.FileHandler(path)
    logger_handler.setLevel(level)
    logger_handler.setFormatter(formatter)
    return logger_handler

def add_handlers():
    """Add root logger handlers"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(create_sublogger(logging.DEBUG, "robot.log"))
    root_logger.addHandler(create_sublogger(logging.DEBUG))
