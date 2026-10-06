"""Контроллер отчётов. Ошибки параметров приходят как ValidationError (подкласс ApplicationError)."""
from services.report_service import ReportService


class ReportController:
    def __init__(self, service: ReportService):
        self._service = service

    def get_dealerships(self):
        return self._service.get_dealerships()

    def sales_by_period(self, start_date: str, end_date: str):
        return self._service.sales_by_period(start_date, end_date)

    def cars_by_manufacturer(self):
        return self._service.cars_by_manufacturer()

    def stock_by_dealership(self, dealership_id: int | None):
        return self._service.stock_by_dealership(dealership_id)
