"""
SQLAlchemy 2.0 declarative base.
All ORM models inherit from Base defined here.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Application-wide declarative base for all ORM models."""
    pass
