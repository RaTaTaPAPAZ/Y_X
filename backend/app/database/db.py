import os
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

DEFAULT_SQLITE_URL = os.getenv("SQLITE_DATABASE_URL", "sqlite:///./yakamy.db")
CONFIGURED_DATABASE_URL = os.getenv("DATABASE_URL") or DEFAULT_SQLITE_URL
ALLOW_DB_FALLBACK = os.getenv("DB_FALLBACK_TO_SQLITE", "true").lower() in {"1", "true", "yes", "on"}

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False)
engine: Engine | None = None
_DATABASE_STATE: dict[str, Any] = {
    "configured_url": CONFIGURED_DATABASE_URL,
    "active_url": None,
    "fallback_used": False,
    "last_error": None,
}


def _engine_kwargs(url: str) -> dict[str, Any]:
    kwargs: dict[str, Any] = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return kwargs


def _build_engine(url: str) -> Engine:
    return create_engine(url, **_engine_kwargs(url))


def _can_connect(candidate: Engine) -> None:
    with candidate.connect() as connection:
        connection.execute(text("SELECT 1"))


def _activate_engine(url: str, fallback_used: bool) -> Engine:
    global engine
    engine = _build_engine(url)
    SessionLocal.configure(bind=engine)
    _DATABASE_STATE["active_url"] = url
    _DATABASE_STATE["fallback_used"] = fallback_used
    _DATABASE_STATE["last_error"] = None
    return engine


def ensure_database_ready() -> Engine:
    global engine
    if engine is not None:
        return engine

    try:
        preferred_engine = _build_engine(CONFIGURED_DATABASE_URL)
        _can_connect(preferred_engine)
        return _activate_engine(CONFIGURED_DATABASE_URL, fallback_used=False)
    except SQLAlchemyError as exc:
        _DATABASE_STATE["last_error"] = str(exc)
        if not ALLOW_DB_FALLBACK or CONFIGURED_DATABASE_URL == DEFAULT_SQLITE_URL:
            raise

    fallback_engine = _build_engine(DEFAULT_SQLITE_URL)
    _can_connect(fallback_engine)
    return _activate_engine(DEFAULT_SQLITE_URL, fallback_used=True)


def get_database_state() -> dict[str, Any]:
    ensure_database_ready()
    return dict(_DATABASE_STATE)


def get_db() -> Generator:
    ensure_database_ready()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
