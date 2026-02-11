"""add_unavailable_at

Revision ID: k7l3m9n5o1p2
Revises: b314393d6ef5
Create Date: 2026-02-11 10:00:00.000000

Adds unavailable_at nullable timestamp column to market_odds and
competitor_market_odds tables for tracking when markets become unavailable
(disappeared from bookmaker). NULL means available, timestamp means
unavailable since that time.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'k7l3m9n5o1p2'
down_revision: Union[str, Sequence[str], None] = 'b314393d6ef5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unavailable_at column to both market tables.

    Nullable TIMESTAMP WITH TIME ZONE column. NULL = available,
    timestamp = unavailable since that time. Existing data defaults
    to NULL (available) - no backfill needed.
    """
    op.add_column(
        'market_odds',
        sa.Column('unavailable_at', sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        'competitor_market_odds',
        sa.Column('unavailable_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    """Remove unavailable_at column from both market tables."""
    op.drop_column('competitor_market_odds', 'unavailable_at')
    op.drop_column('market_odds', 'unavailable_at')
