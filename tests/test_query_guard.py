from pathlib import Path
import sqlite3

import pytest

from query_guard import UnsafeQuery, execute_read_only, validate_select


def test_adds_limit():
    assert validate_select("SELECT * FROM students", 25).endswith("LIMIT 25")


@pytest.mark.parametrize("sql", [
    "DROP TABLE students",
    "UPDATE students SET marks = 0",
    "SELECT * FROM students; DELETE FROM students",
    "PRAGMA table_info(students)",
])
def test_rejects_unsafe_sql(sql):
    with pytest.raises(UnsafeQuery):
        validate_select(sql)


def test_executes_read_only(tmp_path: Path):
    database = tmp_path / "sample.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE scores(name TEXT, marks INTEGER)")
        connection.execute("INSERT INTO scores VALUES ('A', 98)")
    columns, rows, sql = execute_read_only(database, "SELECT name, marks FROM scores")
    assert columns == ["name", "marks"]
    assert rows == [("A", 98)]
    assert "LIMIT" in sql
