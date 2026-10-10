import sqlite3
import pytest
from models import data_access


def query(db, sql, params=()):
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def car_title(row):
    for key in ("model_name", "car_name"):
        try:
            return row[key]
        except (KeyError, IndexError, TypeError):
            continue
    raise AssertionError("в строке автомобиля нет model_name/car_name")


def pick_stock(db):
    """Автосалон, сотрудник и автомобиль, которого есть на складе."""
    rows = query(db, """
        SELECT s.dealership_id, s.car_id, s.car_count, c.price, e.employee_id
        FROM Stock s
        JOIN Cars c ON c.car_id = s.car_id
        JOIN Employees e ON e.dealership_id = s.dealership_id
        WHERE s.car_count > 0 LIMIT 1""")
    assert rows, "в тестовой базе нет остатков (запусти seed_test_data.py)"
    return rows[0]


def stock_count(db, dealership_id, car_id):
    return query(db, "SELECT car_count FROM Stock WHERE dealership_id=? AND car_id=?",
                 (dealership_id, car_id))[0]["car_count"]


def test_catalog_is_loaded(test_db):
    cars = data_access.get_all_cars()
    assert len(cars) >= 1
    assert all(car_title(row) for row in cars)


def test_search_by_name(test_db):
    cars = data_access.get_all_cars()
    term = car_title(cars[0])[:3]
    assert data_access.find_cars_by_name(term)


def test_sale_decreases_stock(test_db):
    st = pick_stock(test_db)
    before = st["car_count"]
    sale_id = data_access.create_sale(
        st["dealership_id"], st["employee_id"], None,
        [{"car_id": st["car_id"], "quantity": 1, "price": st["price"]}])
    assert sale_id > 0
    assert stock_count(test_db, st["dealership_id"], st["car_id"]) == before - 1


def test_sale_rejects_excess_stock(test_db):
    st = pick_stock(test_db)
    before = st["car_count"]
    with pytest.raises(Exception):
        data_access.create_sale(
            st["dealership_id"], st["employee_id"], None,
            [{"car_id": st["car_id"], "quantity": before + 1, "price": st["price"]}])
    assert stock_count(test_db, st["dealership_id"], st["car_id"]) == before
