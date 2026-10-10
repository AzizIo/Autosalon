"""Слой доступа к данным (Data Access Layer): параметризованные запросы sqlite3.

Все пользовательские значения передаются в SQL только через параметры «?»,
поэтому SQL-инъекция невозможна. Модуль удовлетворяет контрактам Repository
из contracts.py.
"""
import logging
import sqlite3
from contextlib import contextmanager

import config
from exceptions import (
    CarInUseError,
    InsufficientStockError,
    IntegrationError,
    ValidationError,
)

DB_PATH = str(config.DB_PATH)
logger = logging.getLogger("autosalon.dal")

_CAR_COLUMNS = (
    "c.car_id, c.model_name, c.price, c.body_type, c.year_of_manufacture, c.color, "
    "c.manufacturer_id, m.manufacturer_name"
)
_CAR_FROM = "FROM Cars c JOIN Manufacturers m ON m.manufacturer_id = c.manufacturer_id"


@contextmanager
def get_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.Error as error:
        logger.error("Не удалось открыть базу данных %s: %s", DB_PATH, error)
        raise IntegrationError(f"Не удалось открыть базу данных: {error}") from error
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_all_cars():
    with get_connection() as conn:
        rows = conn.execute(f"SELECT {_CAR_COLUMNS} {_CAR_FROM} ORDER BY c.model_name").fetchall()
        logger.debug("get_all_cars: получено строк %s", len(rows))
        return rows


def get_car_by_id(car_id: int):
    with get_connection() as conn:
        return conn.execute(
            f"SELECT {_CAR_COLUMNS} {_CAR_FROM} WHERE c.car_id = ?", (car_id,)
        ).fetchone()


def find_cars_by_name(search_text: str):
    with get_connection() as conn:
        rows = conn.execute(
            f"SELECT {_CAR_COLUMNS} {_CAR_FROM} "
            "WHERE c.model_name LIKE ? OR m.manufacturer_name LIKE ? ORDER BY c.model_name",
            (f"%{search_text}%", f"%{search_text}%"),
        ).fetchall()
        logger.debug("find_cars_by_name(%r): найдено %s", search_text, len(rows))
        return rows


def get_all_manufacturers():
    with get_connection() as conn:
        return conn.execute(
            "SELECT manufacturer_id, manufacturer_name, country FROM Manufacturers "
            "ORDER BY manufacturer_name"
        ).fetchall()


def get_stock_by_dealership(dealership_id: int):
    with get_connection() as conn:
        return conn.execute(
            """SELECT c.car_id, c.model_name, s.car_count
               FROM Stock s
               JOIN Cars c ON c.car_id = s.car_id
               WHERE s.dealership_id = ?
               ORDER BY c.model_name""",
            (dealership_id,),
        ).fetchall()


def add_car(model_name: str, price: float, year: int, body_type: str,
            manufacturer_id: int, color: str | None = None) -> int:
    with get_connection() as conn:
        try:
            cursor = conn.execute(
                """INSERT INTO Cars (model_name, price, year_of_manufacture, body_type, color, manufacturer_id)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (model_name, price, year, body_type, color, manufacturer_id),
            )
            conn.commit()
        except sqlite3.IntegrityError as error:
            conn.rollback()
            logger.warning("add_car отклонён базой данных: %s", error)
            raise IntegrationError(f"База данных отклонила добавление автомобиля: {error}") from error
        logger.info("Добавлен автомобиль ID=%s «%s»", cursor.lastrowid, model_name)
        return cursor.lastrowid


def update_car(car_id: int, model_name: str, price: float, year: int,
               body_type: str, manufacturer_id: int, color: str | None) -> bool:
    with get_connection() as conn:
        try:
            cursor = conn.execute(
                """UPDATE Cars
                   SET model_name = ?, price = ?, year_of_manufacture = ?, body_type = ?,
                       color = ?, manufacturer_id = ?
                   WHERE car_id = ?""",
                (model_name, price, year, body_type, color, manufacturer_id, car_id),
            )
            conn.commit()
        except sqlite3.IntegrityError as error:
            conn.rollback()
            logger.warning("update_car отклонён базой данных: %s", error)
            raise IntegrationError(f"База данных отклонила изменение автомобиля: {error}") from error
        logger.info("Изменён автомобиль ID=%s (строк: %s)", car_id, cursor.rowcount)
        return cursor.rowcount > 0


def update_car_price(car_id: int, new_price: float) -> bool:
    with get_connection() as conn:
        cursor = conn.execute("UPDATE Cars SET price = ? WHERE car_id = ?", (new_price, car_id))
        conn.commit()
        return cursor.rowcount > 0


def delete_car(car_id: int) -> bool:
    with get_connection() as conn:
        try:
            cursor = conn.execute("DELETE FROM Cars WHERE car_id = ?", (car_id,))
            conn.commit()
        except sqlite3.IntegrityError as error:
            conn.rollback()
            logger.warning("Удаление автомобиля ID=%s запрещено: %s", car_id, error)
            raise CarInUseError(car_id) from error
        logger.info("Удалён автомобиль ID=%s", car_id)
        return cursor.rowcount > 0


def get_all_dealerships():
    with get_connection() as conn:
        return conn.execute(
            "SELECT dealership_id, address, city FROM Dealerships ORDER BY city, address"
        ).fetchall()


def get_all_employees(dealership_id: int | None = None):
    with get_connection() as conn:
        if dealership_id is None:
            return conn.execute(
                "SELECT employee_id, first_name, last_name, dealership_id "
                "FROM Employees ORDER BY last_name, first_name"
            ).fetchall()
        return conn.execute(
            "SELECT employee_id, first_name, last_name, dealership_id FROM Employees "
            "WHERE dealership_id = ? ORDER BY last_name, first_name",
            (dealership_id,),
        ).fetchall()


def get_all_customers():
    with get_connection() as conn:
        return conn.execute(
            "SELECT customer_id, first_name, last_name FROM Customers "
            "ORDER BY last_name, first_name"
        ).fetchall()


def get_sale_history():
    with get_connection() as conn:
        return conn.execute(
            "SELECT sale_id, sale_date, city, employee_last_name, total_amount "
            "FROM vw_sale_totals ORDER BY sale_date DESC, sale_id DESC"
        ).fetchall()


def create_sale(dealership_id: int, employee_id: int, customer_id: int | None,
                items: list[dict]) -> int:
    """Оформляет продажу одной транзакцией. Остаток списывает триггер базы данных."""
    logger.debug(
        "create_sale: автосалон=%s, сотрудник=%s, клиент=%s, позиций=%s",
        dealership_id, employee_id, customer_id, len(items),
    )
    with get_connection() as conn:
        try:
            if not items:
                raise ValidationError("Добавьте хотя бы один автомобиль в продажу")

            quantities: dict[int, int] = {}
            for item in items:
                quantity = int(item["quantity"])
                if quantity <= 0:
                    raise ValidationError("Количество должно быть больше нуля")
                quantities[item["car_id"]] = quantities.get(item["car_id"], 0) + quantity

            employee = conn.execute(
                "SELECT 1 FROM Employees WHERE employee_id = ? AND dealership_id = ?",
                (employee_id, dealership_id),
            ).fetchone()
            if employee is None:
                raise ValidationError("Выбранный сотрудник не работает в этом автосалоне")

            for car_id, quantity in quantities.items():
                stock = conn.execute(
                    "SELECT car_count FROM Stock WHERE dealership_id = ? AND car_id = ?",
                    (dealership_id, car_id),
                ).fetchone()
                available = stock["car_count"] if stock is not None else 0
                if available < quantity:
                    car = conn.execute(
                        "SELECT model_name FROM Cars WHERE car_id = ?", (car_id,)
                    ).fetchone()
                    raise InsufficientStockError(
                        car_id, available, quantity, car["model_name"] if car else None
                    )

            cursor = conn.execute(
                "INSERT INTO Sales (dealership_id, employee_id, customer_id) VALUES (?, ?, ?)",
                (dealership_id, employee_id, customer_id),
            )
            sale_id = cursor.lastrowid

            price_by_car = {item["car_id"]: item["price"] for item in items}
            for car_id, quantity in quantities.items():
                conn.execute(
                    "INSERT INTO SaleItems (sale_id, car_id, quantity, price) VALUES (?, ?, ?, ?)",
                    (sale_id, car_id, quantity, price_by_car[car_id]),
                )
            conn.commit()
            logger.info("Оформлена продажа ID=%s, позиций: %s", sale_id, len(quantities))
            return sale_id
        except (ValidationError, InsufficientStockError) as error:
            conn.rollback()
            logger.warning("Продажа отклонена: %s", error)
            raise
        except sqlite3.IntegrityError as error:
            conn.rollback()
            logger.error("Продажа отменена базой данных: %s", error)
            raise IntegrationError(f"Продажа отменена: {error}") from error
