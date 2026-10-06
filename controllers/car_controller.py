"""Контроллер автомобилей: связывает окна PyQt6 с сервисом и переводит исключения в сообщения."""
import logging

from contracts import CarServiceContract
from exceptions import ApplicationError, ValidationError

logger = logging.getLogger("autosalon.controller.car")


class CarController:
    def __init__(self, service: CarServiceContract):
        self._service = service

    def get_all_cars(self):
        return self._service.get_all_cars()

    def get_car_by_id(self, car_id: int):
        return self._service.get_car_by_id(car_id)

    def search_cars(self, text: str):
        return self._service.search_cars(text)

    def get_manufacturers(self):
        return self._service.get_manufacturers()

    def add_car(self, model_name: str, price, year, body_type: str, manufacturer_id,
                color: str | None = None):
        """Возвращает (ID нового автомобиля или None, список сообщений об ошибках)."""
        try:
            return self._service.add_car(model_name, price, year, body_type, manufacturer_id, color), []
        except ValidationError as error:
            return None, error.errors
        except ApplicationError as error:
            logger.error("Не удалось добавить автомобиль: %s", error)
            return None, [str(error)]

    def update_car(self, car_id: int, model_name: str, price, year, body_type: str,
                   manufacturer_id, color: str | None = None):
        """Возвращает (признак успеха, список сообщений об ошибках)."""
        try:
            return self._service.update_car(
                car_id, model_name, price, year, body_type, manufacturer_id, color
            ), []
        except ValidationError as error:
            return False, error.errors
        except ApplicationError as error:
            logger.error("Не удалось изменить автомобиль ID=%s: %s", car_id, error)
            return False, [str(error)]

    def delete_car(self, car_id: int):
        """Возвращает (признак успеха, сообщение для пользователя или None)."""
        try:
            self._service.delete_car(car_id)
            return True, None
        except ApplicationError as error:
            return False, str(error)
