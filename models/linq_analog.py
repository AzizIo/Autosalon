"""Запросы SQLAlchemy к данным автосалона (аналог LINQ-запросов)."""
from sqlalchemy import func, select

from .db_context import SessionLocal
from .models import Car, Customer, Manufacturer, Sale, SaleItem, Stock


def run_all():
    with SessionLocal() as db:

        # 1. Простой выбор: автомобили дороже 3 000 000 руб., по возрастанию цены
        expensive_cars = db.scalars(
            select(Car).where(Car.price > 3_000_000).order_by(Car.price)
        ).all()

        # 2. Соединение (Join): автомобили с названиями производителей
        cars_with_manufacturers = db.execute(
            select(Car.model_name, Manufacturer.manufacturer_name)
            .join(Manufacturer, Manufacturer.manufacturer_id == Car.manufacturer_id)
        ).all()

        # 3. Группировка: количество моделей у каждого производителя
        cars_by_manufacturer = db.execute(
            select(Manufacturer.manufacturer_name, func.count(Car.car_id))
            .join(Car, Car.manufacturer_id == Manufacturer.manufacturer_id)
            .group_by(Manufacturer.manufacturer_name)
        ).all()

        # 4. Агрегация: средняя цена автомобиля
        avg_price = db.scalar(select(func.avg(Car.price)))

        # 5. Группировка с фильтром: клиенты, купившие более чем на 5 000 000 руб.
        top_customers = db.execute(
            select(Customer.customer_id, Customer.last_name,
                   func.sum(SaleItem.quantity * SaleItem.price).label("total"))
            .join(Sale, Sale.customer_id == Customer.customer_id)
            .join(SaleItem, SaleItem.sale_id == Sale.sale_id)
            .group_by(Customer.customer_id, Customer.last_name)
            .having(func.sum(SaleItem.quantity * SaleItem.price) > 5_000_000)
        ).all()

        # 6. Paging: постраничная выборка (5 на странице, 2-я страница)
        page = db.scalars(select(Car).order_by(Car.car_id).offset(5).limit(5)).all()

        # 7. Сводка по продажам: сумма и число позиций в каждой продаже
        sale_summary = db.execute(
            select(Sale.sale_id, Sale.sale_date,
                   func.sum(SaleItem.quantity * SaleItem.price).label("total_amount"),
                   func.count(SaleItem.car_id).label("items_count"))
            .join(SaleItem, SaleItem.sale_id == Sale.sale_id)
            .group_by(Sale.sale_id, Sale.sale_date)
        ).all()

        # 8. Остатки конкретного автосалона, по убыванию количества
        stock_in_dealership = db.execute(
            select(Car.model_name, Stock.car_count)
            .join(Car, Car.car_id == Stock.car_id)
            .where(Stock.dealership_id == 1)
            .order_by(Stock.car_count.desc())
        ).all()

        return {
            "expensive_cars": expensive_cars,
            "cars_with_manufacturers": cars_with_manufacturers,
            "cars_by_manufacturer": cars_by_manufacturer,
            "average_price": avg_price,
            "top_customers": top_customers,
            "car_page": page,
            "sale_summary": sale_summary,
            "stock_in_dealership": stock_in_dealership,
        }


if __name__ == "__main__":
    for query_name, result in run_all().items():
        print(f"{query_name}: {result}")
