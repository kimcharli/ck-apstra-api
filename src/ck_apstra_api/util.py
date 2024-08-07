from datetime import datetime
import logging

class CustomFormatter(logging.Formatter):
    black = "\x1b[30;21m"
    grey = "\x1b[38;21m"
    dark_gray = "\x1b[90;21m"
    white = "\x1b[37;21m"
    bright_white = "\x1b[97;21m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: white + format + reset,
        logging.INFO: dark_gray + format + reset,
        logging.WARNING: yellow + format + reset,
        logging.ERROR: red + format + reset,
        logging.CRITICAL: bold_red + format + reset
    }

    def format(self, record):
        levelname = record.levelname.ljust(8)  # Set the level name to a fixed width (e.g., 8 characters)
        record.levelname = levelname
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def prep_logging(log_level: str = 'INFO', log_name: str = 'root'):
    '''Configure logging options'''
    timestamp = datetime.now().strftime("%Y%m%d-%H:%H:%S")
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.DEBUG)

    fh = logging.FileHandler(f'ck_apstra_api_{timestamp.replace(":", "")}.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(CustomFormatter())
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)
    logger.addHandler(fh)
    return logger


def deep_copy(obj):
    """Retun nested deep copy of an object"""
    if type(obj) is dict:
        return {k: deep_copy(v) for k, v in obj.items()}
    if type(obj) is list:
        return [deep_copy(v) for v in obj]
    return obj
