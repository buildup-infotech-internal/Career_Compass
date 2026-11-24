from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


@lru_cache
def get_engine() -> Engine:
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set in the environment variables.")
    return create_engine(settings.DATABASE_URL, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(autoflush=False, bind=get_engine(), expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def dispose_database() -> None:
    """Dispose a lazily-created engine and clear cached session resources."""
    get_session_factory.cache_clear()
    if get_engine.cache_info().currsize:
        get_engine().dispose()
        get_engine.cache_clear()