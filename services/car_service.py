"""Бизнес-логика автомобилей (Business Logic Layer): проверки и правила."""
import logging
from datetime import date

import config
from contracts import CarRepository
from exceptions import ValidationError

logger = logging.getLogger("autosalon.bll.car")


class CarService:
    """Сервис получает слой доступа к данным через конструктор (внедрение зависимости)."""

    def __init__(self, repository: CarRepository):
        self._repo = repository

    # ---------- чтение
    def get_all_cars(self):
        return self._repo.get_all_cars()

    def get_car_by_id(self, car_id: int):
        return self._repo.get_car_by_id(car_id)

    def search_cars(self, text: str):
        if not text or not text.strip():
            return self.get_all_cars()
        return self._repo.find_cars_by_name(text.strip())

    def get_manufacturers(self):
        return self._repo.get_all_manufacturers()

    # ---------- изменение
    def add_car(self, model_name: str, price, year, body_type: str, manufacturer_id,
                color: str | None = None) -> int:
        values = self._validate(model_name, price, year, body_type, manufacturer_id, color)
        logger.debug("Добавление автомобиля: %s", values)
        return self._repo.add_car(**values)

    def update_car(self, car_id: int, model_name: str, price, year, body_type: str,
                   manufacturer_id, color: str | None = None) -> bool:
        values = self._validate(model_name, price, year, body_type, manufacturer_id, color)
        logger.debug("Изменение автомобиля ID=%s: %s", car_id, values)
        return self._repo.update_car(car_id, **values)

    def delete_car(self, car_id: int) -> None:
        logger.debug("Удаление автомобиля ID=%s", car_id)
        self._repo.delete_car(car_id)      # при наличии ссылок слой данных выбросит CarInUseError

    # ---------- проверки
    @staticmethod
    def _validate(model_name, price, year, body_type, manufacturer_id, color) -> dict:
        errors: list[str] = []
        if not model_name or not str(model_name).strip():
            errors.append("Название модели обязательно")

        price_value = None
        try:
            price_value = float(str(price).replace(",", "."))
            if price_value <= 0:
                errors.append("Цена должна быть больше нуля")
        except (ValueError, TypeError):
            errors.append("Цена должна быть числом")

        year_value = None
        try:
            year_value = int(year)
            if year_value < config.MIN_CAR_YEAR or year_value > date.today().year:
                errors.append(
                    f"Год выпуска должен быть от {config.MIN_CAR_YEAR} до {date.today().year}"
                )
        except (ValueError, TypeError):
            errors.append("Год должен быть числом")

        if not body_type or not str(body_type).strip():
            errors.append("Тип кузова обязателен")

        if manufacturer_id is None:
            errors.append("Выберите производителя")

        if errors:
            logger.warning("Проверка данных автомобиля не пройдена: %s", errors)
            raise ValidationError(errors)

        return {
            "model_name": str(model_name).strip(),
            "price": price_value,
            "year": year_value,
            "body_type": str(body_type).strip(),
            "manufacturer_id": int(manufacturer_id),
            "color": (str(color).strip() or None) if color else None,
        }
