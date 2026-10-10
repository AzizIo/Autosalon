# Интеграция модулей

```text
PyQt6 Views
    ↓
Controllers
    ↓
Services (Business Logic)
    ↓
Data Access (sqlite3)
    ↓
AutoSalon.db (SQLite)
```

`CarRepository` и `SaleService` описаны через `typing.Protocol` как контракты взаимодействия.
Операция продажи проходит через `SaleController` → `SaleService` → `data_access.create_sale()`.
После записи `SaleItems` SQLite-триггер `trg_saleitems_decrease_stock` уменьшает остаток в `Stock`.

## Проверенные сценарии

1. Загрузка каталога автомобилей.
2. Поиск по модели и производителю.
3. Добавление/изменение автомобиля с валидацией.
4. Оформление продажи.
5. Проверка уменьшения остатка.
6. Формирование отчёта.
7. Экспорт отчёта в CSV.
8. Резервное копирование и восстановление базы.
