"""
SOUQ // Unified Database Backend (DuckDB + PostgreSQL)
Provides thread-safe per-path locking, bounded-memory DuckDB sessions,
transparent PostgreSQL connection & SQL parameter translation, and
atomic transaction management for treasury and analytics stores.
"""

import os
import re
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple
import duckdb

_DB_LOCKS: Dict[str, threading.RLock] = {}
_LOCK_GUARD = threading.Lock()
_DOUBLE_TYPE_RE = re.compile(r"\bDOUBLE\b(?!\s+PRECISION)", re.IGNORECASE)


def get_db_lock(db_path: str) -> threading.RLock:
    """Returns a canonical re-entrant lock per database path or connection URI."""
    raw = (db_path or "").strip()
    if raw.startswith(("postgres://", "postgresql://")) or raw == ":memory:":
        canonical = raw
    else:
        canonical = os.path.abspath(raw)
    with _LOCK_GUARD:
        lock = _DB_LOCKS.get(canonical)
        if lock is None:
            lock = threading.RLock()
            _DB_LOCKS[canonical] = lock
        return lock


def ensure_parent_dir(path: str) -> None:
    """Creates parent directories for local file DB paths when a directory component exists."""
    if not path or path == ":memory:" or path.startswith(("postgres://", "postgresql://")):
        return
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def resolve_db_target(
    db_path: str,
    default_path: str = "data/souq_treasury_lake.duckdb",
) -> Tuple[str, bool]:
    """
    Resolves (target, is_postgres).
    Explicit local/test paths stay local DuckDB even when DATABASE_URL is configured;
    only explicit Postgres URLs or the default DB path route to DATABASE_URL.
    """
    target = (db_path or default_path).strip()
    if target.startswith(("postgres://", "postgresql://")):
        return target, True
    env_url = os.getenv("DATABASE_URL", "").strip()
    if target == default_path and env_url.startswith(("postgres://", "postgresql://")):
        return env_url, True
    return target, False


def _translate_non_literal_segment(segment: str, escape_percent: bool) -> str:
    """Translates `?` placeholders and `DOUBLE` types outside SQL string literals/comments."""
    if escape_percent:
        segment = segment.replace("%", "%%")
    segment = segment.replace("?", "%s")
    segment = _DOUBLE_TYPE_RE.sub("DOUBLE PRECISION", segment)
    return segment


def _translate_sql_for_postgres(sql: str, escape_percent: bool = False) -> str:
    """
    Translates DuckDB-style SQL (`?` placeholders, `DOUBLE` column type) into
    PostgreSQL-compatible SQL without altering string literals, quoted identifiers,
    or SQL comments.
    """
    out: List[str] = []
    plain_buf: List[str] = []
    n = len(sql)
    i = 0

    def flush_plain() -> None:
        if plain_buf:
            out.append(_translate_non_literal_segment("".join(plain_buf), escape_percent))
            plain_buf.clear()

    while i < n:
        ch = sql[i]

        # Single-quoted string literal ('...')
        if ch == "'":
            flush_plain()
            j = i + 1
            while j < n:
                if sql[j] == "'":
                    if j + 1 < n and sql[j + 1] == "'":
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            lit = sql[i:j]
            out.append(lit.replace("%", "%%") if escape_percent else lit)
            i = j
            continue

        # Double-quoted identifier ("...")
        if ch == '"':
            flush_plain()
            j = i + 1
            while j < n:
                if sql[j] == '"':
                    if j + 1 < n and sql[j + 1] == '"':
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            ident = sql[i:j]
            out.append(ident.replace("%", "%%") if escape_percent else ident)
            i = j
            continue

        # Line comment (-- ...)
        if ch == "-" and i + 1 < n and sql[i + 1] == "-":
            flush_plain()
            j = sql.find("\n", i)
            j = n if j == -1 else j + 1
            comment = sql[i:j]
            out.append(comment.replace("%", "%%") if escape_percent else comment)
            i = j
            continue

        # Block comment (/* ... */)
        if ch == "/" and i + 1 < n and sql[i + 1] == "*":
            flush_plain()
            j = sql.find("*/", i + 2)
            j = n if j == -1 else j + 2
            comment = sql[i:j]
            out.append(comment.replace("%", "%%") if escape_percent else comment)
            i = j
            continue

        plain_buf.append(ch)
        i += 1

    flush_plain()
    return "".join(out)


class DBCursor:
    """Uniform cursor wrapper across DuckDB and PostgreSQL."""

    def __init__(self, cursor: Any):
        self._cursor = cursor

    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        return self._cursor.fetchone()

    def fetchall(self) -> List[Tuple[Any, ...]]:
        return self._cursor.fetchall()

    @property
    def rowcount(self) -> int:
        return getattr(self._cursor, "rowcount", -1)

    @property
    def description(self) -> Any:
        return getattr(self._cursor, "description", None)


class DBConn:
    """Uniform connection wrapper supporting `.execute(sql, params=None)`."""

    def __init__(self, raw_conn: Any, is_postgres: bool = False):
        self._conn = raw_conn
        self.is_postgres = is_postgres

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> DBCursor:
        has_params = params is not None and len(params) > 0
        if self.is_postgres:
            pg_sql = _translate_sql_for_postgres(sql, escape_percent=has_params)
            cur = self._conn.cursor()
            if has_params:
                cur.execute(pg_sql, tuple(params))
            else:
                cur.execute(pg_sql)
            return DBCursor(cur)

        if has_params:
            cur = self._conn.execute(sql, tuple(params))
        else:
            cur = self._conn.execute(sql)
        return DBCursor(cur)


@contextmanager
def db_transaction(db_target: str, read_only: bool = False) -> Iterator[DBConn]:
    """
    Opens a locked, transactional database session against DuckDB or PostgreSQL.
    Commits on clean exit (when `not read_only`), rolls back on error, and always closes.
    """
    is_postgres = db_target.startswith(("postgres://", "postgresql://"))

    if is_postgres:
        try:
            import psycopg  # type: ignore
            conn = psycopg.connect(db_target, autocommit=False)
        except ImportError:
            try:
                import psycopg2  # type: ignore
                conn = psycopg2.connect(db_target)
                conn.autocommit = False
            except ImportError as exc:
                raise RuntimeError(
                    "PostgreSQL backend requested, but neither 'psycopg' nor 'psycopg2' is installed."
                ) from exc

        try:
            yield DBConn(conn, is_postgres=True)
            if not read_only:
                conn.commit()
            else:
                conn.rollback()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                conn.close()
            except Exception:
                pass
        return

    if db_target != ":memory:":
        ensure_parent_dir(db_target)

    lock = get_db_lock(db_target)
    with lock:
        con = duckdb.connect(db_target)
        try:
            con.execute("SET memory_limit='96MB';")
            con.execute("SET threads=1;")
            if not read_only:
                con.execute("BEGIN TRANSACTION;")
            yield DBConn(con, is_postgres=False)
            if not read_only:
                con.execute("COMMIT;")
        except Exception:
            if not read_only:
                try:
                    con.execute("ROLLBACK;")
                except Exception:
                    pass
            raise
        finally:
            try:
                con.close()
            except Exception:
                pass
