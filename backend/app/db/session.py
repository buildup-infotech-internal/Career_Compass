from functools import lru_cache
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

from collections.abc import Generator

@lru_cache()
def get_engine():
    if not settings.DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set in the environment variables.")
    return create_engine(settings.DATABASE_URL, pool_pre_ping=True)


@lru_cache()
def get_session_factory():
    return sessionmaker(autoflush=False, bind=get_engine(), expire_on_commit=False)

def get_db() -> Generator[Session, None, None]:
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()