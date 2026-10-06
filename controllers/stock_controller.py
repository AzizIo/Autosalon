"""Контроллер остатков автомобилей."""
from services.stock_service import StockService


class StockController:
    def __init__(self, service: StockService):
        self._service = service

    def get_dealerships(self):
        return self._service.get_dealerships()

    def get_stock(self, dealership_id: int | None):
        return self._service.get_stock(dealership_id)
