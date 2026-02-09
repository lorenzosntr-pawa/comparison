"""SQLAlchemy DeclarativeBase with naming conventions for Alembic autogenerate.

This module provides the foundational Base class for all SQLAlchemy ORM models
in the application. It configures consistent naming conventions for database
constraints, enabling reliable Alembic migration autogeneration.

The naming convention ensures that all indexes, unique constraints, check
constraints, foreign keys, and primary keys follow a predictable pattern,
which is essential for database migrations and schema management.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Naming convention for constraints - enables reliable Alembic autogenerate
# See: https://alembic.sqlalchemy.org/en/latest/naming.html
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models.

    All database models inherit from this class to share the common metadata
    configuration including the naming convention for database constraints.

    Usage:
        class MyModel(Base):
            __tablename__ = "my_table"
            id: Mapped[int] = mapped_column(primary_key=True)
    """

    metadata = MetaData(naming_convention=convention)
