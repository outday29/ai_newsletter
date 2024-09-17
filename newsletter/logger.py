import sys
from pathlib import Path

from loguru import logger


def setup_logger():
    Path("debug.log").unlink(missing_ok=True)

    logger.remove(0)
    logger.level("INFO", color="<white>")
    logger.level("WARNING", color="<light-red>")

    logger.add(
        sink="debug.log",
        level="DEBUG",
        retention="1 day",
        colorize=False,
    )

    logger.add(
        sink=sys.stderr,
        level="WARNING",
    )
