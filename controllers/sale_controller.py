"""Контроллер истории продаж и оформления продажи."""
import logging

from contracts import SaleServiceContract
from exceptions import ApplicationError, ValidationError

logger = logging.getLogger("autosalon.controller.sale")


class SaleController:
    def __init__(self, service: SaleServiceContract):
        self._service = service

    def get_sale_history(self):
        return self._service.get_sale_history()

    def get_dealerships(self):
        return self._service.get_dealerships()

    def get_employees(self, dealership_id: int | None):
        return self._service.get_employees(dealership_id)

    def get_customers(self):
        return self._service.get_customers()

    def search_cars(self, text: str):
        return self._service.search_cars(text)

    def create_sale(self, dealership_id, employee_id, customer_id, items: list[dict]):
        """Возвращает (ID продажи или None, список сообщений об ошибках)."""
        try:
            return self._service.create_sale(dealership_id, employee_id, customer_id, items), []
        except ValidationError as error:
            return None, error.errors
        except ApplicationError as error:      # в т.ч. InsufficientStockError, IntegrationError
            logger.warning("Продажа не оформлена: %s", error)
            return None, [str(error)]
