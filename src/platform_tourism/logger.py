"""Logging configuration for the pipeline.

Call :func:`setup_logging` exactly once at the program entry point
(typically in ``main.py``). Library modules should not configure
logging themselves; they should just do::

    logger = logging.getLogger(__name__)
"""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from platform_tourism.config import PROJECT_ROOT

LOG_DIR: Path = PROJECT_ROOT / "logs"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    console_level: int | str | None = None,
    log_to_file: bool = True,
    log_file: str = "pipeline.log",
) -> None:
    """Configure the root logger with console and rotating-file handlers.

    Safe to call more than once: subsequent calls are no-ops, so test
    suites and notebooks won't end up with duplicate handlers.

    Args:
        console_level: Minimum level for the console handler. If ``None``,
            falls back to the ``LOG_LEVEL`` env var, then ``"INFO"``.
        log_to_file: If True, also write to a rotating log file in
            ``LOG_DIR``. The file handler always captures ``DEBUG`` and up.
        log_file: Filename for the rotating log file.
    """
    root = logging.getLogger()
    if root.handlers:  # already configured
        return

    if console_level is None:
        console_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    root.setLevel(logging.DEBUG)  # let handlers do the filtering
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console = logging.StreamHandler(stream=sys.stdout)
    console.setLevel(console_level)
    console.setFormatter(formatter)
    root.addHandler(console)

    if log_to_file:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            LOG_DIR / log_file,
            maxBytes=5_000_000,  # 5 MB
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    logging.captureWarnings(True)  # route warnings.warn() here too
    root.debug("Logging configured: console=%s, file=%s", console_level, log_to_file)
