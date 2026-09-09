"""
Procura — Structured Logging Configuration
"""

import logging
import sys


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure application logging with structured format."""
    logger = logging.getLogger("procura")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# Application-wide logger
logger = setup_logging()
