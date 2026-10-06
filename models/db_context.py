"""Подключение SQLAlchemy (демонстрационный ORM-модуль).

Схему создаёт sql/schema.sql (см. database_init.py): именно в ней заданы CHECK-ограничения
и триггеры, поэтому Base.metadata.create_all() здесь намеренно не вызывается.
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

import config

engine = create_engine(f"sqlite:///{config.DB_PATH}", echo=False)


@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine)
