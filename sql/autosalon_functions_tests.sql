/* ============================================================================
   БД «Сеть автосалонов» — этап 3. Демонстрационные запросы и тесты функций
   Файл: autosalon_functions_tests.sql
   СУБД: Microsoft SQL Server 2019/2022, язык T-SQL
   Автор: Маджитов Азизбек, группа 3ИП-9-24
   Дата: 20.10.2026

   Порядок выполнения: сначала autosalon_functions.sql, затем этот скрипт.
   Тесты склада выполняются в транзакции с откатом (ROLLBACK), поэтому
   данные таблицы Stock не изменяются. Перед изменением остатков наличие
   позиций проверяется (THROW), чтобы тест не «прошёл» на нулевых строках.
   ============================================================================ */


/* ===========================================================================
   ЧАСТЬ 1. ДЕМОНСТРАЦИОННЫЕ ЗАПРОСЫ
   ========================================================================== */

-- 1.1. Скалярная функция в SELECT, WHERE и ORDER BY
SELECT car_id, model_name, year_of_manufacture,
       dbo.fn_CarAge(year_of_manufacture) AS car_age
FROM dbo.Cars
WHERE dbo.fn_CarAge(year_of_manufacture) <= 5
ORDER BY car_age;

-- 1.2. Скалярная функция в вычисляемом столбце
SELECT dbo.fn_CarAge(2020) AS car_age;                       -- 6
SELECT dbo.fn_PriceWithMarkup(1000000, 10) AS price_with_markup; -- 1100000.00

-- 1.3. Inline табличная функция в FROM
SELECT *
FROM dbo.fn_CarsByPrice(500000.00, 2500000.00);

-- 1.4. Inline табличная функция в JOIN (автомобили диапазона и их остатки)
SELECT f.manufacturer_name, f.model_name, f.price,
       d.city, st.car_count
FROM dbo.fn_CarsByPrice(3000000.00, 5000000.00) AS f
INNER JOIN dbo.Stock AS st ON st.car_id = f.car_id
INNER JOIN dbo.Dealerships AS d ON d.dealership_id = st.dealership_id
ORDER BY f.model_name, d.city;

-- 1.5. Inline табличная функция в подзапросе (автомобили, проданные в сентябре)
SELECT car_id, model_name, price
FROM dbo.Cars
WHERE car_id IN
    (SELECT car_id
     FROM dbo.fn_SalesByPeriod('2026-09-01', '2026-09-30'));

-- 1.6. Продажи за период (сентябрь 2026 г.)
SELECT sale_id, sale_date, city, manufacturer_name, model_name,
       quantity, price
FROM dbo.fn_SalesByPeriod('2026-09-01', '2026-09-30')
ORDER BY sale_date, sale_id;

-- 1.7. Многооператорная табличная функция
SELECT *
FROM dbo.fn_StockStatus(5)
ORDER BY city, model_name;

-- 1.8. Представление на основе скалярной функции
SELECT car_id, manufacturer_name, model_name, year_of_manufacture,
       price, car_age
FROM dbo.vw_CarsWithAge
WHERE car_age <= 3;

-- 1.9. Процедура этапа 3, использующая скалярную функцию
EXEC dbo.proc_Cars_GetCatalogWithMarkup @markup_percent = 10;


/* ===========================================================================
   ЧАСТЬ 2. ТЕСТЫ ФУНКЦИЙ (таблица тестирования отчёта, шаг 7)
   ========================================================================== */

PRINT N'Тест 1. fn_CarAge: Year = 2020 (текущий 2026) — ожидается 6';
SELECT dbo.fn_CarAge(2020) AS car_age;

PRINT N'Тест 2. fn_CarAge: Year = NULL — ожидается NULL';
SELECT dbo.fn_CarAge(NULL) AS car_age;

PRINT N'Тест 3. fn_PriceWithMarkup: 1000000 и 10% — ожидается 1100000.00';
SELECT dbo.fn_PriceWithMarkup(1000000, 10) AS price_with_markup;

PRINT N'Тест 4. fn_PriceWithMarkup: цена NULL — ожидается NULL';
SELECT dbo.fn_PriceWithMarkup(NULL, 10) AS price_with_markup;

PRINT N'Тест 5. fn_PriceWithMarkup: процент -1 — ожидается NULL';
SELECT dbo.fn_PriceWithMarkup(100, -1) AS price_with_markup;

PRINT N'Тест 5а. fn_PriceWithMarkup: 90000000 и 20% — ожидается 108000000.00 (проверка диапазона типа)';
SELECT dbo.fn_PriceWithMarkup(90000000, 20) AS price_with_markup;

PRINT N'Тест 6. fn_CarsByPrice: диапазон 90000000-95000000 — ожидается пустая таблица';
SELECT *
FROM dbo.fn_CarsByPrice(90000000.00, 95000000.00);

PRINT N'Тест 7. fn_SalesByPeriod: 2030 год — ожидается пустая таблица';
SELECT *
FROM dbo.fn_SalesByPeriod('2030-01-01', '2030-12-31');

/* --- дополнительные позитивные проверки и контрольные запросы ------------- */

PRINT N'Тест 6а. fn_CarsByPrice: диапазон 3000000-5000000 — ожидается непустая выборка';
SELECT COUNT(*) AS cars_in_range
FROM dbo.fn_CarsByPrice(3000000.00, 5000000.00);
-- контрольный запрос (результаты должны совпадать):
SELECT COUNT(*) AS cars_in_range_control
FROM dbo.Cars
WHERE price BETWEEN 3000000.00 AND 5000000.00;

PRINT N'Тест 6б. fn_CarsByPrice: NULL-параметры и обратный диапазон — ожидается пустая таблица';
SELECT COUNT(*) AS null_params_rows FROM dbo.fn_CarsByPrice(NULL, 1000000.00);
SELECT COUNT(*) AS reversed_range_rows FROM dbo.fn_CarsByPrice(5000000.00, 1000000.00);

PRINT N'Тест 7а. fn_SalesByPeriod: сентябрь 2026 — ожидается непустая выборка';
SELECT COUNT(*) AS sales_in_period
FROM dbo.fn_SalesByPeriod('2026-09-01', '2026-09-30');
-- контрольный запрос:
SELECT COUNT(*) AS sales_in_period_control
FROM dbo.Sales AS s
INNER JOIN dbo.SaleItems AS si ON si.sale_id = s.sale_id
WHERE CAST(s.sale_date AS DATE) BETWEEN '2026-09-01' AND '2026-09-30';

PRINT N'Тесты 8-10. fn_StockStatus: контролируемые остатки (транзакция с откатом)';

-- проверка наличия позиций склада до изменения (car_id = 1 есть во всех
-- трёх салонах по данным этапа 2: 9 шт. в 3 салонах)
IF NOT EXISTS (SELECT 1 FROM dbo.Stock
               WHERE dealership_id = 1 AND car_id = 1)
    THROW 50005, N'Позиция склада (салон 1, автомобиль 1) не найдена — проверьте данные этапа 2.', 1;
IF NOT EXISTS (SELECT 1 FROM dbo.Stock
               WHERE dealership_id = 2 AND car_id = 1)
    THROW 50005, N'Позиция склада (салон 2, автомобиль 1) не найдена — проверьте данные этапа 2.', 1;
IF NOT EXISTS (SELECT 1 FROM dbo.Stock
               WHERE dealership_id = 3 AND car_id = 1)
    THROW 50005, N'Позиция склада (салон 3, автомобиль 1) не найдена — проверьте данные этапа 2.', 1;

BEGIN TRANSACTION;

UPDATE dbo.Stock SET car_count = 0
WHERE dealership_id = 1 AND car_id = 1;   -- «Нет в наличии»

UPDATE dbo.Stock SET car_count = 3
WHERE dealership_id = 2 AND car_id = 1;   -- «Ниже минимума» (3 < 5)

UPDATE dbo.Stock SET car_count = 10
WHERE dealership_id = 3 AND car_id = 1;  -- «Достаточно» (10 >= 5)

SELECT dealership_id, city, model_name, car_count, min_count, status
FROM dbo.fn_StockStatus(5)
WHERE car_id = 1
ORDER BY dealership_id;

ROLLBACK TRANSACTION;  -- исходные остатки восстановлены

-- контроль: после отката значения вернулись к исходным
SELECT dealership_id, car_count
FROM dbo.Stock
WHERE car_id = 1
ORDER BY dealership_id;
