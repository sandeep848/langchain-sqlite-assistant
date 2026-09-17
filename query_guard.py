"""Read-only SQL validation and execution utilities."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

FORBIDDEN = {
    "alter", "attach", "create", "delete", "detach", "drop", "insert",
    "pragma", "reindex", "replace", "update", "vacuum",
}


class UnsafeQuery(ValueError):
    """Raised when generated SQL violates the read-only policy."""


def validate_select(sql: str, max_rows: int = 200) -> str:
    normalized = re.sub(r"\s+", " ", sql.strip().rstrip(";"))
    if not normalized:
        raise UnsafeQuery("The query is empty.")
    if ";" in normalized:
        raise UnsafeQuery("Only one SQL statement is allowed.")
    if not re.match(r"(?is)^(select|with)\b", normalized):
        raise UnsafeQuery("Only SELECT or WITH queries are allowed.")
    tokens = set(re.findall(r"[a-z_]+", normalized.lower()))
    blocked = sorted(tokens & FORBIDDEN)
    if blocked:
        raise UnsafeQuery(f"Blocked SQL keyword: {blocked[0]}")
    if not re.search(r"(?is)\blimit\s+\d+\b", normalized):
        normalized += f" LIMIT {max_rows}"
    return normalized


def schema_context(database: str | Path) -> str:
    with sqlite3.connect(f"file:{Path(database).resolve()}?mode=ro", uri=True) as conn:
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        descriptions: list[str] = []
        for (table,) in tables:
            columns = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
            fields = ", ".join(f"{row[1]} {row[2]}" for row in columns)
            descriptions.append(f"{table}({fields})")
        return "\n".join(descriptions)


def execute_read_only(
    database: str | Path, sql: str, max_rows: int = 200
) -> tuple[list[str], list[tuple[Any, ...]], str]:
    safe_sql = validate_select(sql, max_rows=max_rows)
    with sqlite3.connect(f"file:{Path(database).resolve()}?mode=ro", uri=True) as conn:
        cursor = conn.execute(safe_sql)
        rows = cursor.fetchall()
        columns = [item[0] for item in cursor.description or []]
    return columns, rows, safe_sql
