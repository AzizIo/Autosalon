"""Бизнес-логика резервного копирования: единая обработка ошибок файлов и базы данных."""
import logging
import sqlite3
from pathlib import Path

from contracts import BackupRepository
from exceptions import ApplicationError, IntegrationError

logger = logging.getLogger("autosalon.bll.backup")


class BackupService:
    def __init__(self, backup: BackupRepository):
        self._backup = backup

    def create_backup(self, destination: str | Path) -> Path:
        logger.debug("Создание резервной копии: %s", destination)
        try:
            return self._backup.create_backup(destination)
        except ApplicationError:
            raise
        except (OSError, sqlite3.Error) as error:
            logger.error("Ошибка резервного копирования: %s", error)
            raise IntegrationError(f"Не удалось создать резервную копию: {error}") from error

    def restore_backup(self, source: str | Path) -> Path:
        logger.debug("Восстановление из копии: %s", source)
        try:
            return self._backup.restore_backup(source)
        except ApplicationError:
            raise
        except (OSError, sqlite3.Error) as error:
            logger.error("Ошибка восстановления: %s", error)
            raise IntegrationError(f"Не удалось восстановить базу данных: {error}") from error
