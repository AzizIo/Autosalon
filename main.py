"""Точка входа приложения «Автосалон»."""
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox

from composition import build_controllers
from exceptions import ApplicationError
from logging_config import setup_logging
from models.database_init import ensure_database
from views.main_window import MainWindow


def main() -> int:
    logger = setup_logging()
    app = QApplication(sys.argv)
    try:
        ensure_database()
        window = MainWindow(**build_controllers())
    except ApplicationError as error:
        logger.critical("Запуск невозможен: %s", error)
        QMessageBox.critical(None, "Автосалон", f"Не удалось запустить приложение:\n{error}")
        return 1
    window.show()
    logger.info("Приложение «Автосалон» запущено")
    code = app.exec()
    logger.info("Приложение завершено (код %s)", code)
    return code


if __name__ == "__main__":
    sys.exit(main())
