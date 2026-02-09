"""FastAPI dependencies for database sessions.

This module re-exports the get_db dependency from the database engine
module for convenient importing in route handlers.

The get_db dependency provides an async database session that is
automatically committed or rolled back based on request outcome.
"""

from db.engine import get_db

__all__ = ["get_db"]
