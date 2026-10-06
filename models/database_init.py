"""Создание файла базы данных AutoSalon.db из sql/schema.sql и тестовых данных sql/seed.sql."""
import logging
import sqlite3
from pathlib import Path

import config
from exceptions import IntegrationError

logger = logging.getLogger("autosalon.init")


def ensure_database(db_path: str | Path = config.DB_PATH, with_seed: bool = True) -> bool:
    """Создаёт базу, если файла нет. Возвращает True, если база была создана сейчас."""
    db_path = Path(db_path)
    if db_path.exists():
        logger.debug("База данных найдена: %s", db_path)
        return False
    try:
        schema = config.SCHEMA_PATH.read_text(encoding="utf-8")
        seed = config.SEED_PATH.read_text(encoding="utf-8") if with_seed else ""
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            conn.executescript(schema)
            if seed:
                conn.executescript(seed)
    except (OSError, sqlite3.Error) as error:
        db_path.unlink(missing_ok=True)
        logger.error("Не удалось создать базу данных: %s", error)
        raise IntegrationError(f"Не удалось создать базу данных: {error}") from error
    logger.info("Создана база данных %s (тестовые данные: %s)", db_path, with_seed)
    return True
