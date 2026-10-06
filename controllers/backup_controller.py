"""Контроллер резервного копирования."""
import logging

from exceptions import ApplicationError
from services.backup_service import BackupService

logger = logging.getLogger("autosalon.controller.backup")


class BackupController:
    def __init__(self, service: BackupService):
        self._service = service

    def create_backup(self, destination: str):
        """Возвращает (путь копии или None, сообщение об ошибке или None)."""
        try:
            return self._service.create_backup(destination), None
        except ApplicationError as error:
            logger.error("Резервная копия не создана: %s", error)
            return None, str(error)

    def restore_backup(self, source: str):
        """Возвращает (признак успеха, сообщение об ошибке или None)."""
        try:
            self._service.restore_backup(source)
            return True, None
        except ApplicationError as error:
            logger.error("Восстановление не выполнено: %s", error)
            return False, str(error)
