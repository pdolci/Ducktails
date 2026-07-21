"""Tiny idempotent schema migrations for SQLite.

SQLAlchemy's ``create_all()`` creates missing *tables* but never alters existing
ones, so a column added to a model after a database already exists (e.g.
``ingredients.group``) is silently absent and every query on it fails with
``no such column``. This app has no Alembic setup, so we bridge the gap with a
minimal, additive-only migration: on startup, for each known column, add it with
``ALTER TABLE ... ADD COLUMN`` if it is missing. Safe to run on every boot.

Only additive column changes are handled here — that covers the changes this app
has needed. Anything more complex would warrant a real migration tool.
"""
from sqlalchemy import inspect, text

from app.extensions import db

# table -> list of (column_name, column_type_sql) that must exist.
_REQUIRED_COLUMNS = {
    "ingredients": [
        ("group", "VARCHAR(120)"),
    ],
}


def ensure_schema():
    """Add any missing columns to existing tables (idempotent)."""
    inspector = inspect(db.engine)
    existing_tables = set(inspector.get_table_names())

    for table, columns in _REQUIRED_COLUMNS.items():
        if table not in existing_tables:
            continue  # create_all() will build it fresh, with all columns
        present = {col["name"] for col in inspector.get_columns(table)}
        for name, col_type in columns:
            if name in present:
                continue
            # Quote the column name — several (e.g. "group") are SQL keywords.
            db.session.execute(
                text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {col_type}')
            )
            db.session.commit()
            print(f"[migrations] added {table}.{name}")
