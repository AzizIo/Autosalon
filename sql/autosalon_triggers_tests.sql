/* ============================================================================
   БД «Сеть автосалонов» — этап 4. Демонстрационные запросы и тесты триггеров
   Файл: autosalon_triggers_tests.sql
   СУБД: Microsoft SQL Server 2019/2022, язык T-SQL
   Автор: Маджитов Азизбек, группа 3ИП-9-24
   Дата: 22.10.2026

   Порядок выполнения: сначала autosalon_triggers.sql, затем этот скрипт.
   Тесты создают собственные контролируемые данные (тестовые автомобили,
   продажи, остатки) и выполняются в транзакциях с откатом (ROLLBACK),
   поэтому данные этапов 1–3 не изменяются. Идентификаторы (car_id, sale_id)
   создаются автоматически (IDENTITY) и запоминаются в переменные.
   ============================================================================ */


/* ===========================================================================
   ЧАСТЬ 1. АУДИТ ТАБЛИЦЫ CARS (триггер trg_Cars_Audit)
   ========================================================================== */

-- 1.1. INSERT нового автомобиля (Geely, manufacturer_id = 6 по данным этапа 2)
INSERT INTO dbo.Cars
    (model_name, price, year_of_manufacture, body_type, color, manufacturer_id)
VALUES
    ('Coolray', 2500000.00, 2024, 'Кроссовер', NULL, 6);

PRINT N'Аудит INSERT — последняя запись:';
SELECT TOP 1 table_name, operation, row_id, new_value, changed_by, changed_at
FROM dbo.AuditLog
WHERE table_name = N'Cars' AND operation = N'INSERT'
ORDER BY audit_id DESC;

-- 1.2. UPDATE цены (однострочная операция); заодно сработает триггер этапа 1
--      trg_cars_price_log (запись в PriceHistory)
UPDATE dbo.Cars
SET price = 2600000.00
WHERE model_name = 'Coolray';

PRINT N'Аудит UPDATE — последняя запись:';
SELECT TOP 1 table_name, operation, row_id, old_value, new_value, changed_at
FROM dbo.AuditLog
WHERE table_name = N'Cars' AND operation = N'UPDATE'
ORDER BY audit_id DESC;

-- 1.3. Многострочный UPDATE (car_id 1 и 2 существуют по данным этапа 1):
--      одна команда — по одной строке аудита на каждый автомобиль.
--      Значение цены не меняется (price = price), но триггер срабатывает.
UPDATE dbo.Cars
SET price = price
WHERE car_id IN (1, 2);

PRINT N'Аудит многострочного UPDATE (должно быть 2 строки):';
SELECT table_name, operation, row_id, old_value, new_value, changed_at
FROM dbo.AuditLog
WHERE table_name = N'Cars' AND operation = N'UPDATE'
ORDER BY audit_id DESC;


/* ===========================================================================
   ЧАСТЬ 2. АУДИТ СКЛАДА (триггер trg_Stock_Audit)
   ========================================================================== */

BEGIN TRANSACTION;

-- подготовка: тестовый автомобиль с позицией склада в салоне 1
INSERT INTO dbo.Cars
    (model_name, price, year_of_manufacture, body_type, color, manufacturer_id)
VALUES
    ('TestCar1', 1000000.00, 2024, 'Седан', NULL, 6);
DECLARE @c1 INT = SCOPE_IDENTITY();

INSERT INTO dbo.Stock (dealership_id, car_id, car_count)
VALUES (1, @c1, 5);

-- изменение остатка — срабатывает аудит склада
UPDATE dbo.Stock
SET car_count = 6
WHERE dealership_id = 1 AND car_id = @c1;

PRINT N'Аудит остатков (до отката транзакции):';
SELECT table_name, operation, row_id, old_value, new_value, changed_at
FROM dbo.AuditLog
WHERE table_name = N'Stock'
ORDER BY audit_id DESC;

ROLLBACK TRANSACTION;  -- тестовый автомобиль и остаток удалены


/* ===========================================================================
   ЧАСТЬ 3. КОНТРОЛЬ БИЗНЕС-ПРАВИЛА (trg_SaleItems_CheckStock)
   «нельзя продать автомобилей больше, чем есть на складе салона»
   ========================================================================== */

-- Тест 3.1. Отрицательный сценарий: продажа 999 шт. при остатке 10 —
--           ожидается ошибка 50021 и откат всей операции
BEGIN TRANSACTION;

INSERT INTO dbo.Cars
    (model_name, price, year_of_manufacture, body_type, color, manufacturer_id)
VALUES
    ('TestCar2', 1000000.00, 2024, 'Седан', NULL, 6);
DECLARE @c2 INT = SCOPE_IDENTITY();

INSERT INTO dbo.Stock (dealership_id, car_id, car_count)
VALUES (1, @c2, 10);

INSERT INTO dbo.Sales (sale_date, dealership_id, employee_id, customer_id)
VALUES (GETDATE(), 1, 1, 1);
DECLARE @sale_id INT = SCOPE_IDENTITY();

BEGIN TRY
    INSERT INTO dbo.SaleItems (sale_id, car_id, quantity, price)
    VALUES (@sale_id, @c2, 999, 100000.00);
    PRINT N'ОШИБКА ТЕСТА: вставка прошла, триггер не сработал!';
END TRY
BEGIN CATCH
    PRINT N'Ожидаемая ошибка: ' + CAST(ERROR_NUMBER() AS NVARCHAR(10))
          + N' — ' + ERROR_MESSAGE();
    IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
END CATCH;

-- контроль: позиция продажи не добавлена
SELECT COUNT(*) AS saleitems_rows
FROM dbo.SaleItems
WHERE sale_id = @sale_id;                 -- ожидается 0 (операция откатилась)

-- Тест 3.2. Позитивный сценарий: продажа 2 шт. при остатке 10 — вставка
--           проходит (внутри транзакции, потом откат)
BEGIN TRANSACTION;

INSERT INTO dbo.Cars
    (model_name, price, year_of_manufacture, body_type, color, manufacturer_id)
VALUES
    ('TestCar3', 1000000.00, 2024, 'Седан', NULL, 6);
DECLARE @c3 INT = SCOPE_IDENTITY();

INSERT INTO dbo.Stock (dealership_id, car_id, car_count)
VALUES (1, @c3, 10);

INSERT INTO dbo.Sales (sale_date, dealership_id, employee_id, customer_id)
VALUES (GETDATE(), 1, 1, 1);
SET @sale_id = SCOPE_IDENTITY();

INSERT INTO dbo.SaleItems (sale_id, car_id, quantity, price)
VALUES (@sale_id, @c3, 2, 100000.00);

PRINT N'Корректная продажа прошла, позиция:';
SELECT sale_id, car_id, quantity, price
FROM dbo.SaleItems
WHERE sale_id = @sale_id;

ROLLBACK TRANSACTION;  -- продажа и тестовый автомобиль удалены

-- Тест 3.3. Многострочная вставка: одна команда добавляет две позиции —
--           обе корректны, вставка проходит (потом откат)
BEGIN TRANSACTION;

INSERT INTO dbo.Cars
    (model_name, price, year_of_manufacture, body_type, color, manufacturer_id)
VALUES
    ('TestCar4', 1000000.00, 2024, 'Седан', NULL, 6);
DECLARE @c4 INT = SCOPE_IDENTITY();

INSERT INTO dbo.Cars
    (model_name, price, year_of_manufacture, body_type, color, manufacturer_id)
VALUES
    ('TestCar5', 1000000.00, 2024, 'Седан', NULL, 6);
DECLARE @c5 INT = SCOPE_IDENTITY();

INSERT INTO dbo.Stock (dealership_id, car_id, car_count)
VALUES (1, @c4, 10), (1, @c5, 10);

INSERT INTO dbo.Sales (sale_date, dealership_id, employee_id, customer_id)
VALUES (GETDATE(), 1, 1, 1);
SET @sale_id = SCOPE_IDENTITY();

INSERT INTO dbo.SaleItems (sale_id, car_id, quantity, price)
VALUES (@sale_id, @c4, 1, 100000.00),
       (@sale_id, @c5, 1, 100000.00);

PRINT N'Многострочная вставка прошла:';
SELECT car_id, quantity
FROM dbo.SaleItems
WHERE sale_id = @sale_id;                 -- ожидается 2 строки

ROLLBACK TRANSACTION;  -- тестовые данные удалены


/* ===========================================================================
   ЧАСТЬ 4. INSTEAD OF-ТРИГГЕР (trg_Cars_InsteadDelete)
   ========================================================================== */

-- Тест 4.1. Отрицательный сценарий: удаление автомобиля с продажами —
--           ожидается ошибка 50022, строка сохранена
DECLARE @car_with_sales INT =
    (SELECT TOP 1 si.car_id
     FROM dbo.SaleItems AS si
     GROUP BY si.car_id
     ORDER BY COUNT(*) DESC);
PRINT N'Автомобиль с продажами: car_id = ' + CAST(@car_with_sales AS NVARCHAR(10));

BEGIN TRY
    DELETE FROM dbo.Cars WHERE car_id = @car_with_sales;
    PRINT N'ОШИБКА ТЕСТА: удаление прошло, триггер не сработал!';
END TRY
BEGIN CATCH
    PRINT N'Ожидаемая ошибка: ' + CAST(ERROR_NUMBER() AS NVARCHAR(10))
          + N' — ' + ERROR_MESSAGE();
END CATCH;

-- контроль: автомобиль на месте
SELECT car_id, model_name
FROM dbo.Cars
WHERE car_id = @car_with_sales;           -- строка сохранена

-- Тест 4.2. Позитивный сценарий: удаление автомобиля без продаж и остатков —
--           Coolray из части 1: удаляются PriceHistory и Cars
DELETE FROM dbo.Cars
WHERE model_name = 'Coolray';

PRINT N'Coolray удалён, последние строки аудита:';
SELECT table_name, operation, row_id, old_value, changed_at
FROM dbo.AuditLog
WHERE table_name = N'Cars'
ORDER BY audit_id DESC;


/* ===========================================================================
   ЧАСТЬ 5. ИТОГОВАЯ СВОДКА АУДИТА
   ========================================================================== */

SELECT table_name, operation, COUNT(*) AS rows_logged
FROM dbo.AuditLog
GROUP BY table_name, operation
ORDER BY table_name, operation;
