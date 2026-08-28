"""
Database engine, session factory, and FastAPI dependency.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI dependency that yields a SQLAlchemy session and closes it after the request."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
