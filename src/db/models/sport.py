"""Sport and Tournament models."""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base

if TYPE_CHECKING:
    from src.db.models.event import Event


class Sport(Base):
    """Sport entity (e.g., Football, Basketball)."""

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
    """Tournament/League entity (e.g., English Premier League)."""

    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(primary_key=True)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.id"))
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sportradar_id: Mapped[str | None] = mapped_column(
        String(100), unique=True, nullable=True
    )

    # Relationships
    sport: Mapped["Sport"] = relationship(back_populates="tournaments")
    events: Mapped[list["Event"]] = relationship(
        back_populates="tournament",
        cascade="all, delete-orphan",
    )
