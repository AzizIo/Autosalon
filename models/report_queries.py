"""Параметризованные SQL-наборы данных для вкладки «Отчёты» (те же запросы, что в sql/reports.sql)."""
import logging

from .data_access import get_connection

logger = logging.getLogger("autosalon.reports")


def sales_by_period(start_date: str, end_date: str):
    logger.debug("Отчёт «Продажи за период»: %s — %s", start_date, end_date)
    with get_connection() as conn:
        return conn.execute(
            """SELECT date(s.sale_date) AS sale_day,
                      COUNT(DISTINCT s.sale_id) AS sales_count,
                      SUM(si.quantity) AS cars_sold,
                      ROUND(SUM(si.quantity * si.price), 2) AS revenue
               FROM Sales s
               JOIN SaleItems si ON si.sale_id = s.sale_id
               WHERE date(s.sale_date) BETWEEN date(?) AND date(?)
               GROUP BY date(s.sale_date)
               ORDER BY sale_day""",
            (start_date, end_date),
        ).fetchall()


def cars_by_manufacturer():
    with get_connection() as conn:
        return conn.execute(
            """SELECT m.manufacturer_name AS manufacturer,
                      COUNT(c.car_id) AS cars_count,
                      ROUND(AVG(c.price), 2) AS average_price
               FROM Manufacturers m
               LEFT JOIN Cars c ON c.manufacturer_id = m.manufacturer_id
               GROUP BY m.manufacturer_id, m.manufacturer_name
               ORDER BY m.manufacturer_name"""
        ).fetchall()


def stock_by_dealership(dealership_id: int):
    with get_connection() as conn:
        return conn.execute(
            """SELECT c.model_name, c.body_type, s.car_count,
                      ROUND(c.price * s.car_count, 2) AS stock_value
               FROM Stock s
               JOIN Cars c ON c.car_id = s.car_id
               WHERE s.dealership_id = ?
               ORDER BY s.car_count ASC, c.model_name""",
            (dealership_id,),
        ).fetchall()
