"""Sport and Tournament models.

This module defines the Sport and Tournament models for categorizing
events. Sports are top-level categories (Football, Basketball) while
Tournaments represent leagues or competitions within a sport.
"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.event import Event


class Sport(Base):
    """Sport entity representing a category of athletic competition.

    Top-level categorization for events (e.g., Football, Basketball).
    Each sport contains multiple tournaments.

    Attributes:
        id: Primary key.
        name: Display name (e.g., "Football").
        slug: URL-friendly identifier (e.g., "football"). Must be unique.

    Relationships:
        tournaments: Child Tournament entries (one-to-many, cascade delete).

    Constraints:
        - name: unique
        - slug: unique
    """

    __tablename__ = "sports"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True)

    # Relationships
    tournaments: Mapped[list["Tournament"]] = relationship(
        back_populates="sport",
        cascade="all, delete-orphan",
    )


class Tournament(Base):
    """Tournament or league entity within a sport.

    Represents a competition like "English Premier League" or "La Liga".
    Contains events and belongs to a single sport.

    Attributes:
        id: Primary key.
        sport_id: FK to sports table.
        name: Display name (e.g., "English Premier League").
        country: Country where tournament is based (NOT NULL, default "Unknown").
        sportradar_id: Cross-platform matching key (unique, nullable).

    Relationships:
        sport: Parent Sport (many-to-one).
        events: Child Event entries (one-to-many, cascade delete).

    Constraints:
        - sportradar_id: unique (when not null)
        - (sport_id, name, country): composite unique key
    """

    __tablename__ = "tournaments"
    __table_args__ = (
        UniqueConstraint(
            "sport_id", "name", "country", name="uq_tournaments_sport_name_country"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id"))
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(100), nullable=False, default="Unknown")
    sportradar_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )

    # Relationships
    sport: Mapped["Sport"] = relationship(back_populates="tournaments")
    events: Mapped[list["Event"]] = relationship(
        back_populates="tournament",
        cascade="all, delete-orphan",
    )
