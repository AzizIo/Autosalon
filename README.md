# Автосалон

Настольное приложение учёта автомобилей, остатков по автосалонам и продаж.
Python 3.11+, PyQt6, SQLite (sqlite3), SQLAlchemy 2.x (демонстрационный ORM-слой).

## Запуск

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows;  macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

При первом запуске база `AutoSalon.db` создаётся автоматически из `sql/schema.sql`
и тестовых данных `sql/seed.sql`. Журнал работы пишется в `logs/autosalon.log`.

Сквозная проверка без интерфейса: `python tools/integration_check.py`

## Архитектура

```
views/        окна PyQt6 (представление)
controllers/  передают действия пользователя сервисам, переводят исключения в сообщения
services/     бизнес-логика: проверки и правила
models/       доступ к данным (sqlite3), отчётные запросы, резервные копии, ORM
sql/          schema.sql, seed.sql, reports.sql
contracts.py  контракты взаимодействия модулей (typing.Protocol)
exceptions.py пользовательские исключения
composition.py сборка зависимостей
```

Цепочка вызовов: `MainWindow → Controller → Service → data_access → SQLite`.
