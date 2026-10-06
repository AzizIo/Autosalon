"""Бизнес-логика продаж (Business Logic Layer)."""
import logging

from contracts import SaleRepository
from exceptions import ValidationError

logger = logging.getLogger("autosalon.bll.sale")


class SaleService:
    def __init__(self, repository: SaleRepository):
        self._repo = repository

    # ---------- справочники и история
    def get_sale_history(self):
        return self._repo.get_sale_history()

    def get_dealerships(self):
        return self._repo.get_all_dealerships()

    def get_employees(self, dealership_id: int | None):
        return self._repo.get_all_employees(dealership_id)

    def get_customers(self):
        return self._repo.get_all_customers()

    def search_cars(self, text: str):
        if not text or not text.strip():
            return self._repo.get_all_cars()
        return self._repo.find_cars_by_name(text.strip())

    # ---------- оформление продажи
    def create_sale(self, dealership_id, employee_id, customer_id, items: list[dict]) -> int:
        self._validate(dealership_id, employee_id, items)
        logger.debug(
            "Начало оформления продажи: автосалон=%s, позиций=%s", dealership_id, len(items)
        )
        sale_id = self._repo.create_sale(dealership_id, employee_id, customer_id, items)
        logger.debug("Продажа оформлена: ID=%s", sale_id)
        return sale_id

    @staticmethod
    def _validate(dealership_id, employee_id, items: list[dict]) -> None:
        errors: list[str] = []
        if dealership_id is None:
            errors.append("Выберите автосалон")
        if employee_id is None:
            errors.append("Выберите сотрудника")
        if not items:
            errors.append("Добавьте хотя бы один автомобиль в продажу")
        for item in items:
            try:
                if int(item.get("quantity", 0)) <= 0:
                    raise ValueError
            except (ValueError, TypeError):
                errors.append(
                    f"Количество для «{item.get('model_name', '?')}» должно быть больше нуля"
                )
        if errors:
            logger.warning("Проверка продажи не пройдена: %s", errors)
            raise ValidationError(errors)
