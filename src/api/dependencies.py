"""FastAPI dependencies for database sessions."""

from db.engine import get_db

__all__ = ["get_db"]
