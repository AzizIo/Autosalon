"""ORM-модели SQLAlchemy 2.x (демонстрационный слой; основной доступ к данным — sqlite3 в data_access.py)."""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Dealership(Base):
    __tablename__ = "Dealerships"

    dealership_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(30))
    phone_number: Mapped[str | None] = mapped_column(String(20))

    employees: Mapped[list["Employee"]] = relationship(back_populates="dealership")
    sales: Mapped[list["Sale"]] = relationship(back_populates="dealership")
    stock: Mapped[list["Stock"]] = relationship(back_populates="dealership")


class Employee(Base):
    __tablename__ = "Employees"

    employee_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    phone_number: Mapped[str | None] = mapped_column(String(20), unique=True)
    job_title: Mapped[str] = mapped_column(String(50))
    dealership_id: Mapped[int] = mapped_column(ForeignKey("Dealerships.dealership_id"))

    dealership: Mapped["Dealership"] = relationship(back_populates="employees")
    sales: Mapped[list["Sale"]] = relationship(back_populates="employee")


class Customer(Base):
    __tablename__ = "Customers"

    customer_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(100), unique=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), unique=True)

    sales: Mapped[list["Sale"]] = relationship(back_populates="customer")


class Manufacturer(Base):
    __tablename__ = "Manufacturers"

    manufacturer_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    manufacturer_name: Mapped[str] = mapped_column(String(100), unique=True)
    country: Mapped[str | None] = mapped_column(String(50))

    cars: Mapped[list["Car"]] = relationship(back_populates="manufacturer")


class Car(Base):
    __tablename__ = "Cars"

    car_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_name: Mapped[str] = mapped_column(String(100))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    year_of_manufacture: Mapped[int]
    body_type: Mapped[str] = mapped_column(String(20))
    color: Mapped[str | None] = mapped_column(String(30))
    manufacturer_id: Mapped[int] = mapped_column(ForeignKey("Manufacturers.manufacturer_id"))

    manufacturer: Mapped["Manufacturer"] = relationship(back_populates="cars")
    stock: Mapped[list["Stock"]] = relationship(back_populates="car")
    sale_items: Mapped[list["SaleItem"]] = relationship(back_populates="car")
    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="car")


class Stock(Base):
    __tablename__ = "Stock"

    dealership_id: Mapped[int] = mapped_column(ForeignKey("Dealerships.dealership_id"), primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("Cars.car_id"), primary_key=True)
    car_count: Mapped[int] = mapped_column(default=0)

    dealership: Mapped["Dealership"] = relationship(back_populates="stock")
    car: Mapped["Car"] = relationship(back_populates="stock")


class Sale(Base):
    __tablename__ = "Sales"

    sale_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sale_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    dealership_id: Mapped[int] = mapped_column(ForeignKey("Dealerships.dealership_id"))
    employee_id: Mapped[int] = mapped_column(ForeignKey("Employees.employee_id"))
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("Customers.customer_id"))

    dealership: Mapped["Dealership"] = relationship(back_populates="sales")
    employee: Mapped["Employee"] = relationship(back_populates="sales")
    customer: Mapped[Optional["Customer"]] = relationship(back_populates="sales")
    items: Mapped[list["SaleItem"]] = relationship(back_populates="sale")


class SaleItem(Base):
    __tablename__ = "SaleItems"

    sale_id: Mapped[int] = mapped_column(ForeignKey("Sales.sale_id"), primary_key=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("Cars.car_id"), primary_key=True)
    quantity: Mapped[int]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    sale: Mapped["Sale"] = relationship(back_populates="items")
    car: Mapped["Car"] = relationship(back_populates="sale_items")


class PriceHistory(Base):
    __tablename__ = "PriceHistory"

    history_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    car_id: Mapped[int] = mapped_column(ForeignKey("Cars.car_id"))
    old_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    new_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    car: Mapped["Car"] = relationship(back_populates="price_history")
