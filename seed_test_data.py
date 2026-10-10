"""Наполняет AutoSalon.db тестовыми данными. Запуск один раз из корня проекта."""
import sqlite3

conn = sqlite3.connect("AutoSalon.db")
conn.execute("PRAGMA foreign_keys = ON")
if conn.execute("SELECT COUNT(*) FROM Cars").fetchone()[0]:
    print("В базе уже есть автомобили, ничего не добавляю.")
    raise SystemExit

conn.executemany(
    "INSERT INTO Manufacturers (manufacturer_id, manufacturer_name, country) VALUES (?, ?, ?)",
    [(1, "Toyota", "Япония"), (2, "BMW", "Германия"), (3, "Kia", "Южная Корея")])
conn.executemany(
    "INSERT INTO Dealerships (dealership_id, address, city, phone_number) VALUES (?, ?, ?, ?)",
    [(1, "ул. Центральная, 1", "Ташкент", "+998900000001"),
     (2, "пр. Навои, 10", "Самарканд", "+998900000002")])
conn.executemany(
    "INSERT INTO Employees (employee_id, first_name, last_name, phone_number, job_title, dealership_id) "
    "VALUES (?, ?, ?, ?, ?, ?)",
    [(1, "Алишер", "Каримов", "+998901111111", "Менеджер", 1),
     (2, "Мадина", "Юсупова", "+998902222222", "Менеджер", 2)])
conn.executemany(
    "INSERT INTO Customers (customer_id, first_name, last_name, email, phone_number) VALUES (?, ?, ?, ?, ?)",
    [(1, "Иван", "Петров", "ivan@example.com", "+998903333333")])
conn.executemany(
    "INSERT INTO Cars (car_id, model_name, price, year_of_manufacture, body_type, color, manufacturer_id) "
    "VALUES (?, ?, ?, ?, ?, ?, ?)",
    [(1, "Camry", 32000, 2023, "Седан", "Белый", 1),
     (2, "X5", 75000, 2024, "Внедорожник", "Чёрный", 2),
     (3, "Rio", 15000, 2022, "Хэтчбек", "Серый", 3)])
conn.executemany(
    "INSERT INTO Stock (dealership_id, car_id, car_count) VALUES (?, ?, ?)",
    [(1, 1, 5), (1, 2, 3), (1, 3, 4), (2, 1, 2)])
conn.commit()
print("Тестовые данные добавлены.")
