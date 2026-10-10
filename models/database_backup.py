"""Резервное копирование и восстановление базы данных SQLite."""
import logging
import os
import sqlite3
import tempfile
from pathlib import Path

from exceptions import IntegrationError

from . import data_access

logger = logging.getLogger("autosalon.backup")

def _validate_database(connection: sqlite3.Connection):
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise IntegrationError(f"Проверка целостности не пройдена: {integrity}")

    tables = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        )
    }
    required = {"Cars", "Manufacturers", "Dealerships", "Sales", "SaleItems", "Stock"}
    missing = required - tables
    if missing:
        raise IntegrationError(
            "Файл не содержит обязательные таблицы: " + ", ".join(sorted(missing))
        )

    connection.execute("PRAGMA foreign_keys = ON")
    violations = connection.execute("PRAGMA foreign_key_check").fetchone()
    if violations:
        raise IntegrationError("В файле обнаружено нарушение внешних ключей")

def create_backup(destination: str | Path) -> Path:
    source_path = Path(data_access.DB_PATH).resolve()
    destination_path = Path(destination).resolve()
    if source_path == destination_path:
        raise IntegrationError("Путь резервной копии совпадает с файлом рабочей базы")

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(source_path) as source, sqlite3.connect(destination_path) as target:
        source.backup(target)
        _validate_database(target)
    logger.info("Создана резервная копия: %s", destination_path)
    return destination_path

def restore_backup(source: str | Path) -> Path:
    source_path = Path(source).resolve()
    database_path = Path(data_access.DB_PATH).resolve()
    if source_path == database_path:
        raise IntegrationError("Выберите файл резервной копии, а не рабочую базу")
    if not source_path.is_file():
        raise IntegrationError(f"Файл резервной копии не найден: {source_path}")

    database_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f"{database_path.stem}-restore-",
        suffix=database_path.suffix,
        dir=database_path.parent,
    )
    os.close(descriptor)
    temporary_path = Path(temporary_name)
    try:
        with sqlite3.connect(source_path.as_uri() + "?mode=ro", uri=True) as source_db:
            _validate_database(source_db)
            with sqlite3.connect(temporary_path) as restored_db:
                source_db.backup(restored_db)
                _validate_database(restored_db)
        os.replace(temporary_path, database_path)
    finally:
        temporary_path.unlink(missing_ok=True)
    logger.info("База данных восстановлена из %s", source_path)
    return database_path
