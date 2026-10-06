-- Сводка продаж за период (границы включаются).
SELECT date(s.sale_date) AS sale_day,
       COUNT(DISTINCT s.sale_id) AS sales_count,
       SUM(si.quantity) AS cars_sold,
       ROUND(SUM(si.quantity * si.price), 2) AS revenue
FROM Sales AS s
JOIN SaleItems AS si ON si.sale_id = s.sale_id
WHERE date(s.sale_date) BETWEEN date(:start_date) AND date(:end_date)
GROUP BY date(s.sale_date)
ORDER BY sale_day;

-- Количество автомобилей и средняя цена по производителям.
SELECT m.manufacturer_name AS manufacturer,
       COUNT(c.car_id) AS cars_count,
       ROUND(AVG(c.price), 2) AS average_price
FROM Manufacturers AS m
LEFT JOIN Cars AS c ON c.manufacturer_id = m.manufacturer_id
GROUP BY m.manufacturer_id, m.manufacturer_name
ORDER BY m.manufacturer_name;

-- Стоимость остатков выбранного автосалона.
SELECT c.model_name,
       c.body_type,
       s.car_count,
       ROUND(c.price * s.car_count, 2) AS stock_value
FROM Stock AS s
JOIN Cars AS c ON c.car_id = s.car_id
WHERE s.dealership_id = :dealership_id
ORDER BY s.car_count ASC, c.model_name;
