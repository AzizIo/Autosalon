/* ============================================================================
   БД «Сеть автосалонов» — этап 3. Разработка пользовательских функций
   Файл: autosalon_functions.sql
   СУБД: Microsoft SQL Server 2019/2022, язык T-SQL
   Автор: Маджитов Азизбек, группа 3ИП-9-24
   Дата: 20.10.2026

   Состав:
     1. dbo.fn_CarAge          — скалярная функция (возраст автомобиля)
     2. dbo.fn_PriceWithMarkup — скалярная функция (цена с наценкой)
     3. dbo.fn_CarsByPrice     — inline табличная функция (автомобили по цене)
     4. dbo.fn_SalesByPeriod   — inline табличная функция (продажи за период)
     5. dbo.fn_StockStatus     — многооператорная табличная функция
                                 (остатки и статусы складских позиций)
     6. dbo.vw_CarsWithAge     — представление на основе fn_CarAge
     7. dbo.proc_Cars_GetCatalogWithMarkup — процедура этапа 3, использующая
        скалярную функцию fn_PriceWithMarkup

   Скрипт опирается на схему этапа 1 (autosalon_schema.sql):
     Cars(car_id, model_name, price, year_of_manufacture, body_type,
          color, manufacturer_id)
     Manufacturers(manufacturer_id, manufacturer_name, country)
     Dealerships(dealership_id, address, city, phone_number)
     Stock(dealership_id, car_id, car_count)
     Sales(sale_id, sale_date, dealership_id, employee_id, customer_id)
     SaleItems(sale_id, car_id, quantity, price)

   Все объекты создаются через CREATE OR ALTER — скрипт можно выполнять
   повторно без предварительного удаления объектов.
   ============================================================================ */


-- ============================================================================
-- 1. Скалярная функция: возраст автомобиля
-- Назначение: возвращает возраст автомобиля в годах относительно текущего года.
-- Параметры: @year INT — год выпуска автомобиля.
-- Результат: INT — возраст; NULL, если год NULL, меньше 1900 или больше
--            текущего года.
-- Пример: SELECT dbo.fn_CarAge(2020);  -- 6 (при текущем 2026 годе)
-- ============================================================================
CREATE OR ALTER FUNCTION dbo.fn_CarAge (@year INT)
RETURNS INT
AS
BEGIN
    DECLARE @result INT;

    IF @year IS NULL OR @year < 1900 OR @year > YEAR(GETDATE())
        SET @result = NULL;
    ELSE
        SET @result = YEAR(GETDATE()) - @year;

    RETURN @result;
END;
GO


-- ============================================================================
-- 2. Скалярная функция: цена с наценкой
-- Назначение: рассчитывает цену автомобиля с наценкой в процентах.
-- Параметры: @price NUMERIC(10,2) — исходная цена;
--            @markup_percent NUMERIC(5,2) — процент наценки.
-- Результат: NUMERIC(12,2) — цена с наценкой; NULL при NULL-параметрах,
--            неположительной цене или отрицательном проценте. Возвращаемый тип
--            шире входного, чтобы наценка не переполняла результат.
-- Пример: SELECT dbo.fn_PriceWithMarkup(1000000, 10);  -- 1100000.00
-- ============================================================================
CREATE OR ALTER FUNCTION dbo.fn_PriceWithMarkup
    (@price NUMERIC(10, 2), @markup_percent NUMERIC(5, 2))
RETURNS NUMERIC(12, 2)
AS
BEGIN
    DECLARE @result NUMERIC(12, 2);

    IF @price IS NULL OR @markup_percent IS NULL
       OR @price <= 0 OR @markup_percent < 0
        SET @result = NULL;
    ELSE
        SET @result = ROUND(@price * (1 + @markup_percent / 100.0), 2);

    RETURN @result;
END;
GO


-- ============================================================================
-- 3. Inline табличная функция: автомобили в диапазоне цен
-- Назначение: возвращает автомобили, цена которых входит в заданный диапазон.
-- Параметры: @price_min NUMERIC(10,2), @price_max NUMERIC(10,2).
-- Результат: таблица (car_id, manufacturer_name, model_name, body_type,
--            year_of_manufacture, price); пустая таблица, если параметры NULL
--            или @price_min > @price_max.
-- Пример: SELECT * FROM dbo.fn_CarsByPrice(500000, 2500000);
-- ============================================================================
CREATE OR ALTER FUNCTION dbo.fn_CarsByPrice
    (@price_min NUMERIC(10, 2), @price_max NUMERIC(10, 2))
RETURNS TABLE
AS
RETURN
    SELECT c.car_id,
           m.manufacturer_name,
           c.model_name,
           c.body_type,
           c.year_of_manufacture,
           c.price
    FROM dbo.Cars AS c
    INNER JOIN dbo.Manufacturers AS m
        ON m.manufacturer_id = c.manufacturer_id
    WHERE @price_min IS NOT NULL
      AND @price_max IS NOT NULL
      AND @price_min <= @price_max
      AND c.price BETWEEN @price_min AND @price_max;
GO


-- ============================================================================
-- 4. Inline табличная функция: продажи за период
-- Назначение: возвращает продажи за период с городом, моделью и суммой.
-- Параметры: @date_from DATE, @date_to DATE.
-- Результат: таблица (sale_id, sale_date, city, car_id, manufacturer_name,
--            model_name, quantity, price); пустая таблица, если параметры NULL
--            или @date_from > @date_to.
-- Пример: SELECT * FROM dbo.fn_SalesByPeriod('2026-09-01', '2026-09-30');
-- ============================================================================
CREATE OR ALTER FUNCTION dbo.fn_SalesByPeriod
    (@date_from DATE, @date_to DATE)
RETURNS TABLE
AS
RETURN
    SELECT s.sale_id,
           CAST(s.sale_date AS DATE) AS sale_date,
           d.city,
           si.car_id,
           m.manufacturer_name,
           c.model_name,
           si.quantity,
           si.price
    FROM dbo.Sales AS s
    INNER JOIN dbo.Dealerships AS d ON d.dealership_id = s.dealership_id
    INNER JOIN dbo.SaleItems AS si ON si.sale_id = s.sale_id
    INNER JOIN dbo.Cars AS c ON c.car_id = si.car_id
    INNER JOIN dbo.Manufacturers AS m ON m.manufacturer_id = c.manufacturer_id
    WHERE @date_from IS NOT NULL
      AND @date_to IS NOT NULL
      AND @date_from <= @date_to
      AND CAST(s.sale_date AS DATE) BETWEEN @date_from AND @date_to;
GO


-- ============================================================================
-- 5. Многооператорная табличная функция: статусы складских позиций
-- Назначение: возвращает остатки по салонам и автомобилям со статусом.
-- Параметры: @min_count INT = 5 — порог минимального остатка (в таблице Stock
--            этапа 1 нет столбца минимума, поэтому порог передаётся параметром).
-- Результат: таблица (dealership_id, city, car_id, model_name, car_count,
--            min_count, status), где status:
--            car_count <= 0              — «Нет в наличии»;
--            car_count <  @min_count     — «Ниже минимума»;
--            иначе                       — «Достаточно».
-- Пример: SELECT * FROM dbo.fn_StockStatus(5);
-- ============================================================================
CREATE OR ALTER FUNCTION dbo.fn_StockStatus (@min_count INT = 5)
RETURNS @result TABLE
(
    dealership_id INT           NOT NULL,
    city          VARCHAR(30)  NOT NULL,
    car_id        INT          NOT NULL,
    model_name    VARCHAR(100) NOT NULL,
    car_count     INT          NOT NULL,
    min_count     INT          NOT NULL,
    status        NVARCHAR(50) NOT NULL
)
AS
BEGIN
    -- операция 1: нормализация порога (NULL/отрицательное значение)
    IF @min_count IS NULL OR @min_count < 0
        SET @min_count = 5;

    -- операция 2: заполнение таблицы-результата
    INSERT INTO @result
        (dealership_id, city, car_id, model_name,
         car_count, min_count, status)
    SELECT st.dealership_id,
           d.city,
           st.car_id,
           c.model_name,
           st.car_count,
           @min_count,
           CASE
               WHEN st.car_count <= 0 THEN N'Нет в наличии'
               WHEN st.car_count < @min_count THEN N'Ниже минимума'
               ELSE N'Достаточно'
           END
    FROM dbo.Stock AS st
    INNER JOIN dbo.Dealerships AS d ON d.dealership_id = st.dealership_id
    INNER JOIN dbo.Cars AS c ON c.car_id = st.car_id
    ORDER BY d.city, c.model_name;

    RETURN;
END;
GO


-- ============================================================================
-- 6. Представление на основе скалярной функции
-- Назначение: возраст автомобиля доступен в выборках без повтора выражения.
-- ============================================================================
CREATE OR ALTER VIEW dbo.vw_CarsWithAge
AS
SELECT c.car_id,
       m.manufacturer_name,
       c.model_name,
       c.year_of_manufacture,
       c.price,
       dbo.fn_CarAge(c.year_of_manufacture) AS car_age
FROM dbo.Cars AS c
INNER JOIN dbo.Manufacturers AS m
    ON m.manufacturer_id = c.manufacturer_id;
GO


-- ============================================================================
-- 7. Процедура этапа 3, использующая скалярную функцию
-- Назначение: каталог автомобилей с ценой и ценой с наценкой; формула наценки
--            сосредоточена в fn_PriceWithMarkup и не дублируется в коде.
-- Параметры: @markup_percent NUMERIC(5,2) — процент наценки (>= 0).
-- ============================================================================
CREATE OR ALTER PROCEDURE dbo.proc_Cars_GetCatalogWithMarkup
    @markup_percent NUMERIC(5, 2)
AS
BEGIN
    SET NOCOUNT ON;

    IF @markup_percent IS NULL OR @markup_percent < 0
        THROW 50006, N'Процент наценки задан некорректно.', 1;

    SELECT c.car_id,
           m.manufacturer_name,
           c.model_name,
           c.price,
           dbo.fn_PriceWithMarkup(c.price, @markup_percent) AS price_with_markup
    FROM dbo.Cars AS c
    INNER JOIN dbo.Manufacturers AS m
        ON m.manufacturer_id = c.manufacturer_id
    ORDER BY c.price;
END;
GO
