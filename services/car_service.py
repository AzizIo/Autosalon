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
        """Возвращает все автомобили каталога."""
        return self._repo.get_all_cars()

    def get_car_by_id(self, car_id: int):
        """Возвращает автомобиль по идентификатору."""
        return self._repo.get_car_by_id(car_id)

    def search_cars(self, text: str):
        """Ищет автомобили по части названия; пустой запрос возвращает весь каталог."""
        if not text or not text.strip():
            return self.get_all_cars()
        return self._repo.find_cars_by_name(text.strip())

    def get_manufacturers(self):
        """Возвращает список производителей."""
        return self._repo.get_all_manufacturers()

    # ---------- изменение
    def add_car(self, model_name: str, price, year, body_type: str, manufacturer_id,
                color: str | None = None) -> int:
        """Проверяет данные и добавляет автомобиль; возвращает его идентификатор."""
        values = self._validate(model_name, price, year, body_type, manufacturer_id, color)
        logger.debug("Добавление автомобиля: %s", values)
        return self._repo.add_car(**values)

    def update_car(self, car_id: int, model_name: str, price, year, body_type: str,
                   manufacturer_id, color: str | None = None) -> bool:
        """Проверяет данные и обновляет автомобиль."""
        values = self._validate(model_name, price, year, body_type, manufacturer_id, color)
        logger.debug("Изменение автомобиля ID=%s: %s", car_id, values)
        return self._repo.update_car(car_id, **values)

    def delete_car(self, car_id: int) -> None:
        """Удаляет автомобиль; при наличии ссылок слой данных выбросит CarInUseError."""
        logger.debug("Удаление автомобиля ID=%s", car_id)
        self._repo.delete_car(car_id)

    # ---------- проверки
    @classmethod
    def _validate(cls, model_name, price, year, body_type, manufacturer_id, color) -> dict:
        """Проверяет все поля и возвращает нормализованные значения.

        Все найденные ошибки собираются в один ValidationError.
        """
        errors: list[str] = []
        errors += cls._check_text(model_name, "Название модели обязательно")
        price_value, price_errors = cls._parse_price(price)
        year_value, year_errors = cls._parse_year(year)
        errors += price_errors + year_errors
        errors += cls._check_text(body_type, "Тип кузова обязателен")
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

    @staticmethod
    def _check_text(value, message: str) -> list[str]:
        """Возвращает ошибку, если строка пустая или состоит из пробелов."""
        if not value or not str(value).strip():
            return [message]
        return []

    @staticmethod
    def _parse_price(price) -> tuple[float | None, list[str]]:
        """Преобразует цену в число и проверяет, что она положительная."""
        try:
            value = float(str(price).replace(",", "."))
        except (ValueError, TypeError):
            return None, ["Цена должна быть числом"]
        if value <= 0:
            return value, ["Цена должна быть больше нуля"]
        return value, []

    @staticmethod
    def _parse_year(year) -> tuple[int | None, list[str]]:
        """Преобразует год в число и проверяет допустимый диапазон."""
        try:
            value = int(year)
        except (ValueError, TypeError):
            return None, ["Год должен быть числом"]
        current_year = date.today().year
        if value < config.MIN_CAR_YEAR or value > current_year:
            message = f"Год выпуска должен быть от {config.MIN_CAR_YEAR} до {current_year}"
            return value, [message]
        return value, []
