"""SQLAlchemy ORM base and engine management.

Provides a shared ``Base`` for ORM models and helper functions to create /
retrieve a SQLAlchemy ``Engine`` that points at the same SQLite file used by
the legacy ``sqlite3`` connection in ``database.py``.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""
    pass


_engine: Engine | None = None
_SessionFactory: sessionmaker | None = None


def init_orm(db_path: str | Path, *, shared_conn: sqlite3.Connection | None = None) -> Engine:
    """Initialise the SQLAlchemy engine for *db_path*.

    Creates the engine, registers a listener that enables WAL mode and foreign
    keys on every new connection, and returns the engine.  Safe to call
    multiple times — subsequent calls return the existing engine.

    When *shared_conn* is provided the engine re-uses that raw ``sqlite3``
    connection (via ``StaticPool``) so that ORM writes go through the **same**
    connection as the legacy ``sqlite3`` code.  This avoids SQLite file-level
    lock contention between the two connection holders.
    """
    global _engine, _SessionFactory

    if _engine is not None:
        return _engine

    db_path = Path(db_path)

    if shared_conn is not None:
        url = "sqlite://"  # pseudo-URL; the real connection is supplied
        _engine = create_engine(
            url,
            creator=lambda: shared_conn,
            poolclass=StaticPool,
            echo=False,
            future=True,
        )
        # No event listener needed — WAL / foreign-key pragmas are already
        # set on *shared_conn* by ``init_db`` in ``database.py``.
    else:
        url = f"sqlite:///{db_path}"
        logger.info(f"Creating SQLAlchemy engine: {url}")

        _engine = create_engine(url, echo=False, future=True)

        # Per-connection pragmas (WAL, foreign keys, busy timeout).
        @event.listens_for(_engine, "connect")
        def _set_sqlite_pragmas(dbapi_conn, connection_record):  # noqa: ANN001
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    _SessionFactory = sessionmaker(bind=_engine, future=True)
    return _engine


def get_engine() -> Engine:
    """Return the current engine (raises if ``init_orm`` has not been called)."""
    if _engine is None:
        raise RuntimeError("ORM engine not initialised. Call init_orm first.")
    return _engine


def get_session() -> Session:
    """Return a new ``Session`` bound to the current engine."""
    if _SessionFactory is None:
        raise RuntimeError("ORM engine not initialised. Call init_orm first.")
    return _SessionFactory()
