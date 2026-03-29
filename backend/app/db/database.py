"""Database engine and session management."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine

from ..config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)


def init_db() -> None:
    """Create database tables if they do not exist."""
    SQLModel.metadata.create_all(engine)
    _run_sqlite_migrations()


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency for database sessions."""
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Context manager used by services that are not FastAPI dependencies."""
    with Session(engine) as session:
        yield session


def _run_sqlite_migrations() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    with engine.begin() as connection:
        _ensure_sqlite_column(connection, "users", "email", "VARCHAR(255)")
        _ensure_sqlite_column(connection, "users", "password_hash", "VARCHAR(255)")
        _ensure_sqlite_column(connection, "users", "nickname", "VARCHAR(255) NOT NULL DEFAULT ''")
        _ensure_sqlite_column(connection, "users", "is_active", "BOOLEAN NOT NULL DEFAULT 1")
        _ensure_sqlite_column(connection, "users", "last_login_at", "DATETIME")
        # SQLite cannot add a column with a non-constant default via ALTER TABLE,
        # so we add the column first and backfill existing rows afterwards.
        _ensure_sqlite_column(connection, "users", "updated_at", "DATETIME")
        connection.exec_driver_sql(
            "UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL"
        )
        connection.exec_driver_sql("UPDATE users SET nickname = '' WHERE nickname IS NULL")
        connection.exec_driver_sql("UPDATE users SET is_active = 1 WHERE is_active IS NULL")
        connection.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users(email)")

        _ensure_sqlite_column(connection, "trip_histories", "city_longitude", "FLOAT")
        _ensure_sqlite_column(connection, "trip_histories", "city_latitude", "FLOAT")


def _ensure_sqlite_column(connection, table_name: str, column_name: str, column_sql: str) -> None:
    table_exists = connection.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,),
    ).fetchone()
    if table_exists is None:
        return

    rows = connection.exec_driver_sql(f"PRAGMA table_info({table_name})").fetchall()
    existing_columns = {str(row[1]) for row in rows}
    if column_name in existing_columns:
        return

    connection.exec_driver_sql(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}")
