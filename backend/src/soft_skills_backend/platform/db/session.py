"""Database engine and session helpers."""

from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from soft_skills_backend.config import Settings


def create_engine_from_settings(settings: Settings) -> Engine:
    """Create an application engine."""

    return create_engine(
        settings.database_url,
        future=True,
        pool_pre_ping=not settings.is_sqlite,
    )


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """Create a configured session factory."""

    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def ping_database(session_factory: sessionmaker[Session]) -> None:
    """Fail if the database cannot service a basic roundtrip."""

    with session_factory() as session:
        session.execute(text("SELECT 1"))
