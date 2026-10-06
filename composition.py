"""Точка композиции: здесь модули связываются через контракты (внедрение зависимостей).

    data_access (SQLite) → Service → Controller → MainWindow
"""
from controllers.backup_controller import BackupController
from controllers.car_controller import CarController
from controllers.report_controller import ReportController
from controllers.sale_controller import SaleController
from controllers.stock_controller import StockController
from models import data_access, database_backup, report_queries
from services.backup_service import BackupService
from services.car_service import CarService
from services.report_service import ReportService
from services.sale_service import SaleService
from services.stock_service import StockService


def build_controllers() -> dict:
    """Создаёт сервисы и контроллеры. Модули слоя данных передаются в конструкторы сервисов."""
    return {
        "car_controller": CarController(CarService(data_access)),
        "sale_controller": SaleController(SaleService(data_access)),
        "stock_controller": StockController(StockService(data_access)),
        "report_controller": ReportController(ReportService(report_queries, data_access)),
        "backup_controller": BackupController(BackupService(database_backup)),
    }
