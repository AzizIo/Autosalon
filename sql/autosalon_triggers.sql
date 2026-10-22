/* ============================================================================
   БД «Сеть автосалонов» — этап 4. Разработка триггеров
   Файл: autosalon_triggers.sql
   СУБД: Microsoft SQL Server 2019/2022, язык T-SQL
   Автор: Маджитов Азизбек, группа 3ИП-9-24
   Дата: 22.10.2026

   Состав:
     1. dbo.AuditLog                — таблица аудита изменений
     2. dbo.trg_Cars_Audit          — AFTER INSERT/UPDATE/DELETE, аудит таблицы Cars
     3. dbo.trg_Stock_Audit         — AFTER UPDATE, аудит остатков Stock
     4. dbo.trg_SaleItems_CheckStock — AFTER INSERT, контроль бизнес-правила
                                      «нельзя продать больше, чем есть на складе»
     5. dbo.trg_Cars_InsteadDelete  — INSTEAD OF DELETE, защита истории продаж

   Скрипт опирается на схему этапа 1 (autosalon_schema.sql):
     Cars(car_id, model_name, price, year_of_manufacture, body_type, color,
          manufacturer_id)
     Stock(dealership_id, car_id, car_count)
     Sales(sale_id, sale_date, dealership_id, employee_id, customer_id)
     SaleItems(sale_id, car_id, quantity, price)
     PriceHistory(history_id, car_id, old_price, new_price, changed_at)

   Все триггеры обрабатывают многострочные операции (работают с множествами
   inserted/deleted, без курсоров). Триггеры создаются через CREATE OR ALTER —
   скрипт можно выполнять повторно.
   ============================================================================ */


-- ============================================================================
-- 1. Таблица аудита
-- Назначение: единый журнал изменений ключевых таблиц базы данных.
-- Поля: table_name — таблица, operation — INSERT/UPDATE/DELETE, row_id —
--       идентификатор строки, old_value/new_value — строка до/после изменения,
--       changed_by — пользователь СУБД (SYSTEM_USER), changed_at — время.
-- ============================================================================
CREATE TABLE dbo.AuditLog (
    audit_id   INT           IDENTITY(1, 1) NOT NULL PRIMARY KEY,
    table_name NVARCHAR(100) NOT NULL,      -- таблица, над которой выполнена операция
    operation  NVARCHAR(10)  NOT NULL,      -- INSERT / UPDATE / DELETE
    row_id     NVARCHAR(50)  NOT NULL,      -- идентификатор изменённой строки
    old_value  NVARCHAR(MAX) NULL,          -- строка до изменения
    new_value  NVARCHAR(MAX) NULL,          -- строка после изменения
    changed_by NVARCHAR(100) NOT NULL DEFAULT SYSTEM_USER,
    changed_at DATETIME2      NOT NULL DEFAULT GETDATE()
);
GO


-- ============================================================================
-- 2. AFTER-триггер аудита таблицы Cars (INSERT / UPDATE / DELETE)
-- Назначение: протоколирует добавление, изменение и удаление автомобилей.
-- Многострочность: одна строка аудита на каждую строку inserted/deleted.
-- ============================================================================
CREATE OR ALTER TRIGGER dbo.trg_Cars_Audit
ON dbo.Cars
AFTER INSERT, UPDATE, DELETE
AS
BEGIN
    SET NOCOUNT ON;

    -- UPDATE: есть и inserted (новые значения), и deleted (старые значения)
    IF EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        INSERT INTO dbo.AuditLog (table_name, operation, row_id, old_value, new_value)
        SELECT N'Cars', N'UPDATE', CAST(d.car_id AS NVARCHAR(50)),
               CONCAT(N'модель: ', d.model_name, N'; цена: ', d.price),
               CONCAT(N'модель: ', i.model_name, N'; цена: ', i.price)
        FROM deleted AS d
        INNER JOIN inserted AS i ON i.car_id = d.car_id;

    -- INSERT: есть только inserted
    IF EXISTS (SELECT 1 FROM inserted) AND NOT EXISTS (SELECT 1 FROM deleted)
        INSERT INTO dbo.AuditLog (table_name, operation, row_id, new_value)
        SELECT N'Cars', N'INSERT', CAST(car_id AS NVARCHAR(50)),
               CONCAT(N'модель: ', model_name, N'; цена: ', price)
        FROM inserted;

    -- DELETE: есть только deleted
    IF NOT EXISTS (SELECT 1 FROM inserted) AND EXISTS (SELECT 1 FROM deleted)
        INSERT INTO dbo.AuditLog (table_name, operation, row_id, old_value)
        SELECT N'Cars', N'DELETE', CAST(car_id AS NVARCHAR(50)),
               CONCAT(N'модель: ', model_name, N'; цена: ', price)
        FROM deleted;
END;
GO


-- ============================================================================
-- 3. AFTER-триггер аудита таблицы Stock (UPDATE)
-- Назначение: протоколирует изменение складских остатков (продажа,
--            поступление, перемещение между салонами).
-- ============================================================================
CREATE OR ALTER TRIGGER dbo.trg_Stock_Audit
ON dbo.Stock
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.AuditLog (table_name, operation, row_id, old_value, new_value)
    SELECT N'Stock', N'UPDATE',
           CONCAT(N'салон ', d.dealership_id, N', автомобиль ', d.car_id),
           CONCAT(N'остаток: ', d.car_count),
           CONCAT(N'остаток: ', i.car_count)
    FROM deleted AS d
    INNER JOIN inserted AS i
        ON i.dealership_id = d.dealership_id
       AND i.car_id = d.car_id;
END;
GO


-- ============================================================================
-- 4. Триггер контроля бизнес-правила: «нельзя продать автомобилей больше,
--    чем есть на складе салона»
-- Назначение: при добавлении позиций продажи проверяет, что суммарное
--            количество по каждой модели в салоне не превышает остатка.
--            Правило нельзя выразить ограничением CHECK, так как оно зависит
--            от текущего остатка в другой таблице (Stock).
--            При нарушении — ROLLBACK и THROW 50021.
-- Многострочность: количество суммируется по всем строкам вставки.
-- ============================================================================
CREATE OR ALTER TRIGGER dbo.trg_SaleItems_CheckStock
ON dbo.SaleItems
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (
        SELECT 1
        FROM inserted AS i
        INNER JOIN dbo.Sales AS s ON s.sale_id = i.sale_id
        LEFT JOIN dbo.Stock AS st
            ON st.dealership_id = s.dealership_id
           AND st.car_id = i.car_id
        GROUP BY s.dealership_id, i.car_id, st.car_count
        HAVING SUM(i.quantity) > ISNULL(st.car_count, 0)   -- нет позиции склада = остаток 0
    )
    BEGIN
        ROLLBACK TRANSACTION;
        THROW 50021, N'Нельзя оформить продажу: автомобилей на складе салона недостаточно.', 1;
    END;
END;
GO

-- выполнять этот триггер раньше триггера списания остатков (этап 1),
-- чтобы проверка шла по остатку до продажи
BEGIN TRY
    EXEC sp_settriggerorder
         @triggername   = N'dbo.trg_SaleItems_CheckStock',
         @order         = N'FIRST',
         @statementtype = N'INSERT';
END TRY
BEGIN CATCH
    PRINT N'Порядок триггеров не изменён (слот FIRST занят другим триггером).';
END CATCH;
GO


-- ============================================================================
-- 5. INSTEAD OF-триггер: защита истории продаж при удалении автомобиля
-- Назначение: замещает операцию DELETE по справочнику автомобилей:
--            - автомобиль с продажами удалить нельзя (THROW 50022);
--            - автомобиль, числящийся на складе, удалить нельзя (THROW 50023);
--            - иначе удаляются строки PriceHistory и сам автомобиль
--              (компенсация отсутствия ON DELETE CASCADE).
-- ============================================================================
CREATE OR ALTER TRIGGER dbo.trg_Cars_InsteadDelete
ON dbo.Cars
INSTEAD OF DELETE
AS
BEGIN
    SET NOCOUNT ON;

    IF EXISTS (SELECT 1
               FROM deleted AS d
               INNER JOIN dbo.SaleItems AS si ON si.car_id = d.car_id)
    BEGIN
        ROLLBACK TRANSACTION;
        THROW 50022, N'Нельзя удалить автомобиль, у которого есть продажи.', 1;
        RETURN;
    END;

    IF EXISTS (SELECT 1
               FROM deleted AS d
               INNER JOIN dbo.Stock AS st ON st.car_id = d.car_id)
    BEGIN
        ROLLBACK TRANSACTION;
        THROW 50023, N'Нельзя удалить автомобиль, который числится на складе салонов.', 1;
        RETURN;
    END;

    -- автомобилей без продаж и остатков: очистка истории цен и удаление
    DELETE ph
    FROM dbo.PriceHistory AS ph
    INNER JOIN deleted AS d ON ph.car_id = d.car_id;

    DELETE c
    FROM dbo.Cars AS c
    INNER JOIN deleted AS d ON d.car_id = c.car_id;
END;
GO
