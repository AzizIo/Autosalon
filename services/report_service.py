"""Бизнес-логика отчётов: проверка параметров и вызов наборов данных."""
import logging
from datetime import date

from contracts import ReportRepository, SaleRepository
from exceptions import ValidationError

logger = logging.getLogger("autosalon.bll.report")


class ReportService:
    def __init__(self, reports: ReportRepository, dictionaries: SaleRepository):
        self._reports = reports
        self._dictionaries = dictionaries

    def get_dealerships(self):
        return self._dictionaries.get_all_dealerships()

    def sales_by_period(self, start_date: str, end_date: str):
        try:
            start, end = date.fromisoformat(start_date), date.fromisoformat(end_date)
        except (ValueError, TypeError):
            raise ValidationError("Даты периода указаны некорректно") from None
        if start > end:
            raise ValidationError("Начало периода не может быть позже его окончания")
        logger.debug("Формирование отчёта продаж: %s — %s", start_date, end_date)
        return self._reports.sales_by_period(start_date, end_date)

    def cars_by_manufacturer(self):
        return self._reports.cars_by_manufacturer()

    def stock_by_dealership(self, dealership_id: int | None):
        if dealership_id is None:
            return []
        return self._reports.stock_by_dealership(dealership_id)
