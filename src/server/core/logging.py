import logging
import sys

from loguru import _defaults, logger


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentaion.
    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record: logging.LogRecord):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    # disable handlers for specific gunicorn loggers
    # to redirect their output to the default gunicorn logger
    # works with gunicorn==0.11.6
    intercept_handler = InterceptHandler()
    for name in logging.root.manager.loggerDict:
        if name.startswith("gunicorn"):
            logging.getLogger(name).handlers = [intercept_handler]

    formatter = (
        "[<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green>] "
        "[<level>{level}</level>] "
        "[<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan>] "
        "<level>{message}</level> <level>{exception}</level>"
    )
    handlers = [
        {
            "sink": sys.stdout,
            "format": formatter,
            "filter": lambda record: record["level"].no < _defaults.LOGURU_WARNING_NO,
        },
        {
            "sink": sys.stderr,
            "format": formatter,
            "filter": lambda record: record["level"].no >= _defaults.LOGURU_WARNING_NO,
        },
    ]
    logger.configure(handlers=handlers)
