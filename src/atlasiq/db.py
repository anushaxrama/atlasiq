from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import psycopg
from psycopg.rows import dict_row

from .config import DATABASE_URL, ROOT


@contextmanager
def connection() -> Iterator[psycopg.Connection[dict[str, Any]]]:
    with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
        conn.execute("SET statement_timeout='30s'")
        yield conn


def bootstrap() -> None:
    with connection() as conn:
        conn.execute((ROOT / "src/atlasiq/schema.sql").read_text())


def query(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    with connection() as conn:
        conn.execute("SET TRANSACTION READ ONLY")
        return list(conn.execute(sql, params or {}).fetchall())
