"""
SOUQ // Unified Database Backend (DuckDB + PostgreSQL)
Provides thread-safe per-path locking, bounded-memory DuckDB sessions,
transparent PostgreSQL connection & SQL parameter translation, and
atomic transaction management for treasury and analytics stores.
"""

import logging
import os
import re
import secrets
import threading
from contextlib import contextmanager
from typing import Any, Callable, Dict, Iterator, List, Optional, Sequence, Tuple
from dotenv import load_dotenv
import duckdb

logger = logging.getLogger("souq.db_backend")
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
_EPHEMERAL_TEST_PEPPER = secrets.token_hex(32)


def load_souq_env() -> None:
    """
    Unified environment loader across SOUQ processes:
    1. Explicit process environment variables (e.g. Koyeb / pytest monkeypatch) take top precedence.
    2. Root `.env` is authoritative for local/swarm config.
    3. `config/.env` provides secondary defaults only for keys absent from root `.env`.
    """
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"), override=False)
    load_dotenv(os.path.join(PROJECT_ROOT, "config", ".env"), override=False)


def get_ephemeral_test_pepper() -> str:
    """Returns a runtime-generated 32-byte hex secret for isolated unit tests (never a static string)."""
    return _EPHEMERAL_TEST_PEPPER


load_souq_env()

_DB_LOCKS: Dict[str, threading.RLock] = {}
_PG_POOLS: Dict[str, Any] = {}
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
    is_default = (target == default_path) or (
        os.path.abspath(target) == os.path.abspath(default_path)
    )
    if is_default and env_url.startswith(("postgres://", "postgresql://")):
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


def _is_transient_pg_error(exc: BaseException) -> bool:
    """Detects dropped SSL/TCP connections (e.g. Neon idle scale-to-zero) that can be safely reconnected."""
    try:
        import psycopg  # type: ignore
        if isinstance(exc, (psycopg.OperationalError, psycopg.InterfaceError)):
            return True
    except ImportError:
        pass
    try:
        import psycopg2  # type: ignore
        if isinstance(exc, (psycopg2.OperationalError, psycopg2.InterfaceError)):
            return True
    except ImportError:
        pass
    return False


class DBConn:
    """Uniform connection wrapper supporting `.execute(sql, params=None)`."""

    def __init__(
        self,
        raw_conn: Any,
        is_postgres: bool = False,
        reconnect_fn: Optional[Callable[[], Any]] = None,
    ):
        self._conn = raw_conn
        self.is_postgres = is_postgres
        self._reconnect_fn = reconnect_fn
        self._tx_started = False

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> DBCursor:
        has_params = params is not None and len(params) > 0
        if self.is_postgres:
            pg_sql = _translate_sql_for_postgres(sql, escape_percent=has_params)
            try:
                cur = self._conn.cursor()
                if has_params:
                    cur.execute(pg_sql, tuple(params))
                else:
                    cur.execute(pg_sql)
                self._tx_started = True
                return DBCursor(cur)
            except Exception as exc:
                if (not self._tx_started) and self._reconnect_fn is not None and _is_transient_pg_error(exc):
                    logger.warning("Transient PostgreSQL disconnect on initial statement (%s); reconnecting once.", exc)
                    self._conn = self._reconnect_fn()
                    cur = self._conn.cursor()
                    if has_params:
                        cur.execute(pg_sql, tuple(params))
                    else:
                        cur.execute(pg_sql)
                    self._tx_started = True
                    return DBCursor(cur)
                raise

        if has_params:
            cur = self._conn.execute(sql, tuple(params))
        else:
            cur = self._conn.execute(sql)
        self._tx_started = True
        return DBCursor(cur)


def _reset_pg_pool(db_target: str) -> None:
    """Closes and evicts a cached PostgreSQL pool after a fatal pool/connection fault."""
    with _LOCK_GUARD:
        old_pool = _PG_POOLS.pop(db_target, None)
    if old_pool is not None:
        try:
            old_pool.close()
        except Exception:
            pass


def _get_pg_pool(db_target: str) -> Optional[Any]:
    """
    Returns a cached psycopg_pool.ConnectionPool configured with connection health checks
    (`check=ConnectionPool.check_connection`), bounded idle lifetime, and TCP keepalives
    so dropped Neon serverless SSL connections self-heal automatically.
    """
    with _LOCK_GUARD:
        if db_target in _PG_POOLS:
            return _PG_POOLS[db_target]
        try:
            from psycopg_pool import ConnectionPool  # type: ignore

            pool = ConnectionPool(
                conninfo=db_target,
                min_size=0,
                max_size=5,
                max_idle=240.0,
                timeout=10.0,
                reconnect_timeout=10.0,
                check=ConnectionPool.check_connection,
                kwargs={
                    "autocommit": False,
                    "connect_timeout": 10,
                    "keepalives": 1,
                    "keepalives_idle": 30,
                    "keepalives_interval": 10,
                    "keepalives_count": 3,
                },
            )
            _PG_POOLS[db_target] = pool
            return pool
        except ImportError:
            _PG_POOLS[db_target] = None
            return None


def _connect_direct_pg(db_target: str) -> Any:
    """Opens an unpooled PostgreSQL connection with a single cold-start retry on OperationalError."""
    last_err: Optional[BaseException] = None
    for attempt in range(2):
        try:
            import psycopg  # type: ignore
            return psycopg.connect(db_target, autocommit=False, connect_timeout=10)
        except ImportError:
            try:
                import psycopg2  # type: ignore
                conn = psycopg2.connect(db_target, connect_timeout=10)
                conn.autocommit = False
                return conn
            except ImportError as exc:
                raise RuntimeError(
                    "PostgreSQL backend requested, but neither 'psycopg' nor 'psycopg2' is installed."
                ) from exc
            except Exception as exc2:
                last_err = exc2
                if attempt == 0 and _is_transient_pg_error(exc2):
                    continue
                raise
        except Exception as exc:
            last_err = exc
            if attempt == 0 and _is_transient_pg_error(exc):
                continue
            raise
    assert last_err is not None
    raise last_err


@contextmanager
def db_transaction(db_target: str, read_only: bool = False) -> Iterator[DBConn]:
    """
    Opens a locked, transactional database session against DuckDB or PostgreSQL.
    Uses health-checked pooled connections for PostgreSQL when psycopg_pool is installed,
    with automatic reconnect-on-OperationalError recovery for Neon SSL idle drops.
    Commits on clean exit (when `not read_only`), rolls back on error, and always returns/closes.
    """
    is_postgres = db_target.startswith(("postgres://", "postgresql://"))

    if is_postgres:
        pool = _get_pg_pool(db_target)
        if pool is not None:
            ctx = None
            conn = None
            for attempt in range(2):
                try:
                    ctx = pool.connection()
                    conn = ctx.__enter__()
                    break
                except Exception as exc:
                    if attempt == 0 and _is_transient_pg_error(exc):
                        logger.warning("PostgreSQL pool checkout failed (%s); resetting pool and retrying.", exc)
                        _reset_pg_pool(db_target)
                        pool = _get_pg_pool(db_target)
                        if pool is None:
                            break
                        continue
                    raise

            if conn is not None and ctx is not None:
                fallback_direct_conn: List[Any] = []

                def _swap_fresh_conn() -> Any:
                    fresh = _connect_direct_pg(db_target)
                    fallback_direct_conn.append(fresh)
                    return fresh

                exc_info: Tuple[Any, Any, Any] = (None, None, None)
                try:
                    db_conn = DBConn(conn, is_postgres=True, reconnect_fn=_swap_fresh_conn)
                    yield db_conn
                    active_conn = db_conn._conn
                    if not read_only:
                        active_conn.commit()
                    else:
                        active_conn.rollback()
                except BaseException as err:
                    import sys
                    exc_info = sys.exc_info()
                    active_conn = fallback_direct_conn[-1] if fallback_direct_conn else conn
                    try:
                        active_conn.rollback()
                    except Exception:
                        pass
                    raise
                finally:
                    for extra in fallback_direct_conn:
                        try:
                            extra.close()
                        except Exception:
                            pass
                    try:
                        ctx.__exit__(*exc_info)
                    except Exception:
                        pass
                return

        conn = _connect_direct_pg(db_target)
        holder = [conn]

        def _reconnect_unpooled() -> Any:
            try:
                holder[0].close()
            except Exception:
                pass
            holder[0] = _connect_direct_pg(db_target)
            return holder[0]

        try:
            yield DBConn(holder[0], is_postgres=True, reconnect_fn=_reconnect_unpooled)
            if not read_only:
                holder[0].commit()
            else:
                holder[0].rollback()
        except Exception:
            try:
                holder[0].rollback()
            except Exception:
                pass
            raise
        finally:
            try:
                holder[0].close()
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
