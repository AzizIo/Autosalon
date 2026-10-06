"""Настройка журналирования (logging) приложения.

Файл logs/autosalon.log получает сообщения от DEBUG и выше, консоль — от INFO.
"""
import logging
import sys
from logging.handlers import RotatingFileHandler

import config

LOG_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"


def setup_logging(console_level: int = logging.INFO) -> logging.Logger:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("autosalon")
    if logger.handlers:                      # повторный вызов не дублирует обработчики
        return logger
    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    file_handler = RotatingFileHandler(
        config.LOG_FILE, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
