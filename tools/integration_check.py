"""Сквозная проверка интеграции модулей без графического интерфейса.

Запуск из папки проекта:  python tools/integration_check.py
Проверяет цепочку Controller → Service → Data Access → SQLite на временной базе данных.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from logging_config import setup_logging
from models import data_access
from models.database_init import ensure_database


def main() -> int:
    setup_logging()
    tmp = Path(tempfile.mkdtemp()) / "check.db"
    data_access.DB_PATH = str(tmp)
    ensure_database(tmp)

    from composition import build_controllers
    c = build_controllers()

    cars = c["car_controller"].get_all_cars()
    print(f"[1] Автомобилей в каталоге: {len(cars)}")

    car_id, errors = c["car_controller"].add_car("Тест Седан", "2 500 000".replace(" ", ""), "2024", "Седан", 1, None)
    print(f"[2] Добавление корректного автомобиля: ID={car_id}, ошибки={errors}")

    _, errors = c["car_controller"].add_car("", "-5", "1800", "", None)
    print(f"[3] Добавление некорректного автомобиля: ошибок {len(errors)}")
    for e in errors:
        print("      -", e)

    before = {r["car_id"]: r["car_count"] for r in c["stock_controller"].get_stock(1)}
    item = {"car_id": 1, "model_name": "Toyota Camry", "quantity": 2, "price": 3250000.0}
    sale_id, errors = c["sale_controller"].create_sale(1, 1, 1, [item])
    after = {r["car_id"]: r["car_count"] for r in c["stock_controller"].get_stock(1)}
    print(f"[4] Продажа 2 шт.: sale_id={sale_id}, остаток {before[1]} -> {after[1]}, ошибки={errors}")

    big = dict(item, quantity=999)
    sale_id2, errors = c["sale_controller"].create_sale(1, 1, None, [big])
    print(f"[5] Продажа 999 шт.: sale_id={sale_id2}, ошибки={errors}")

    sale_id3, errors = c["sale_controller"].create_sale(1, 3, None, [item])   # сотрудник 3 работает в другом салоне
    print(f"[6] Сотрудник из другого автосалона: sale_id={sale_id3}, ошибки={errors}")

    ok, message = c["car_controller"].delete_car(1)
    print(f"[7] Удаление автомобиля с продажами: ok={ok}, сообщение={message}")

    ok, message = c["car_controller"].delete_car(car_id)
    print(f"[8] Удаление нового автомобиля без ссылок: ok={ok}")

    rep = c["report_controller"].sales_by_period("2000-01-01", "2100-01-01")
    print(f"[9] Отчёт продаж: строк={len(rep)}, выручка={rep[0]['revenue'] if rep else None}")

    backup = tmp.parent / "copy.db"
    path, error = c["backup_controller"].create_backup(str(backup))
    print(f"[10] Резервная копия: {path is not None}, ошибка={error}")
    ok, error = c["backup_controller"].restore_backup(str(backup))
    print(f"[11] Восстановление: {ok}, ошибка={error}")

    ok = (before[1] - after[1] == 2 and sale_id and not sale_id2 and not sale_id3)
    print("\nИТОГ:", "сквозной сценарий пройден" if ok else "ЕСТЬ ОШИБКИ")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
