"""Bookmaker configuration model.

This module defines the Bookmaker model representing betting platforms
tracked by the system (e.g., Betpawa, SportyBet, Bet9ja).
"""

from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base


class Bookmaker(Base):
    """Bookmaker configuration entity.

    Represents a betting platform whose odds are scraped and compared.
    Currently supports Betpawa (reference platform), SportyBet, and Bet9ja.

    Attributes:
        id: Primary key.
        name: Display name (e.g., "SportyBet Nigeria").
        slug: URL-friendly identifier (e.g., "sportybet"). Must be unique.
        is_active: Whether this bookmaker is currently being scraped.
        base_url: Website URL for linking to events.
        logo_url: URL to bookmaker logo for UI display.
        created_at: Timestamp when record was created.
        updated_at: Timestamp of last modification.

    Constraints:
        - name: unique
        - slug: unique
    """

    __tablename__ = "bookmakers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )
