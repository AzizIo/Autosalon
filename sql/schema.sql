PRAGMA foreign_keys = ON;

CREATE TABLE Dealerships (
    dealership_id INTEGER NOT NULL PRIMARY KEY,
    address VARCHAR(50) NOT NULL,
    city VARCHAR(30) NOT NULL,
    phone_number VARCHAR(20)
);

CREATE TABLE Manufacturers (
    manufacturer_id INTEGER NOT NULL PRIMARY KEY,
    manufacturer_name VARCHAR(100) NOT NULL UNIQUE,
    country VARCHAR(50)
);

CREATE TABLE Cars (
    car_id INTEGER NOT NULL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL CHECK (price > 0),
    year_of_manufacture INTEGER NOT NULL,
    body_type VARCHAR(20) NOT NULL,
    color VARCHAR(30),
    manufacturer_id INTEGER NOT NULL REFERENCES Manufacturers(manufacturer_id)
);

CREATE TABLE Customers (
    customer_id INTEGER NOT NULL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    phone_number VARCHAR(20) UNIQUE
);

CREATE TABLE Employees (
    employee_id INTEGER NOT NULL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    phone_number VARCHAR(20) UNIQUE,
    job_title VARCHAR(50) NOT NULL,
    dealership_id INTEGER NOT NULL REFERENCES Dealerships(dealership_id)
);

CREATE TABLE Stock (
    dealership_id INTEGER NOT NULL REFERENCES Dealerships(dealership_id),
    car_id INTEGER NOT NULL REFERENCES Cars(car_id),
    car_count INTEGER NOT NULL DEFAULT 0 CHECK (car_count >= 0),
    PRIMARY KEY (dealership_id, car_id)
);

CREATE TABLE Sales (
    sale_id INTEGER NOT NULL PRIMARY KEY,
    sale_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    dealership_id INTEGER NOT NULL REFERENCES Dealerships(dealership_id),
    employee_id INTEGER NOT NULL REFERENCES Employees(employee_id),
    customer_id INTEGER REFERENCES Customers(customer_id)
);

CREATE TABLE SaleItems (
    sale_id INTEGER NOT NULL REFERENCES Sales(sale_id),
    car_id INTEGER NOT NULL REFERENCES Cars(car_id),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price NUMERIC(10, 2) NOT NULL CHECK (price > 0),
    PRIMARY KEY (sale_id, car_id)
);

CREATE TABLE PriceHistory (
    history_id INTEGER NOT NULL PRIMARY KEY,
    car_id INTEGER NOT NULL REFERENCES Cars(car_id),
    old_price NUMERIC(10, 2) NOT NULL,
    new_price NUMERIC(10, 2) NOT NULL,
    changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE VIEW vw_sale_totals AS
SELECT s.sale_id,
       s.sale_date,
       d.city,
       e.last_name AS employee_last_name,
       SUM(si.quantity * si.price) AS total_amount
FROM Sales AS s
JOIN Dealerships AS d ON d.dealership_id = s.dealership_id
JOIN Employees AS e ON e.employee_id = s.employee_id
JOIN SaleItems AS si ON si.sale_id = s.sale_id
GROUP BY s.sale_id, s.sale_date, d.city, e.last_name;

CREATE TRIGGER trg_cars_price_log
AFTER UPDATE OF price ON Cars
WHEN OLD.price <> NEW.price
BEGIN
    INSERT INTO PriceHistory (car_id, old_price, new_price)
    VALUES (OLD.car_id, OLD.price, NEW.price);
END;

CREATE TRIGGER trg_saleitems_decrease_stock
AFTER INSERT ON SaleItems
BEGIN
    UPDATE Stock
    SET car_count = car_count - NEW.quantity
    WHERE car_id = NEW.car_id
      AND dealership_id = (SELECT dealership_id FROM Sales WHERE sale_id = NEW.sale_id);
END;

CREATE TRIGGER trg_saleitems_restore_stock
AFTER DELETE ON SaleItems
BEGIN
    UPDATE Stock
    SET car_count = car_count + OLD.quantity
    WHERE car_id = OLD.car_id
      AND dealership_id = (SELECT dealership_id FROM Sales WHERE sale_id = OLD.sale_id);
END;
