"""Пользовательские исключения приложения «Автосалон».

Иерархия:
    ApplicationError            — базовое исключение приложения
    ├── ValidationError         — некорректные данные от пользователя (хранит список сообщений)
    ├── InsufficientStockError  — в автосалоне недостаточно автомобилей для продажи
    ├── CarInUseError           — автомобиль нельзя удалить: на него есть ссылки
    └── IntegrationError        — сбой взаимодействия модулей: база данных, файлы, резервные копии
"""


class ApplicationError(Exception):
    """Базовое исключение. Текст сообщения можно показывать пользователю."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


class ValidationError(ApplicationError):
    """Данные не прошли проверку. В errors — все найденные ошибки."""

    def __init__(self, errors: list[str] | str):
        if isinstance(errors, str):
            errors = [errors]
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


class InsufficientStockError(ApplicationError):
    """В выбранном автосалоне нет нужного количества автомобилей."""

    def __init__(self, car_id: int, available: int, requested: int, car_name: str | None = None):
        self.car_id = car_id
        self.available = available
        self.requested = requested
        title = f"«{car_name}»" if car_name else f"ID {car_id}"
        super().__init__(
            f"Недостаточно остатка для автомобиля {title}: "
            f"доступно {available}, запрошено {requested}"
        )


class CarInUseError(ApplicationError):
    """Автомобиль нельзя удалить: на него есть ссылки в остатках, продажах или истории цен."""

    def __init__(self, car_id: int | None = None):
        self.car_id = car_id
        super().__init__(
            "Нельзя удалить автомобиль: на него есть ссылки в остатках, продажах "
            "или истории изменения цены."
        )


class IntegrationError(ApplicationError):
    """Ошибка взаимодействия модулей: база данных, файловая система, резервные копии."""
