"""Бизнес-логика остатков."""
from contracts import SaleRepository


class StockService:
    def __init__(self, repository: SaleRepository):
        self._repo = repository

    def get_dealerships(self):
        return self._repo.get_all_dealerships()

    def get_stock(self, dealership_id: int | None):
        if dealership_id is None:
            return []
        return self._repo.get_stock_by_dealership(dealership_id)
