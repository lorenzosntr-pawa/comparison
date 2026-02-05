"""add_last_confirmed_at

Revision ID: i5j1k7l2m6n8
Revises: h4i0j6k1l4m5
Create Date: 2026-02-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i5j1k7l2m6n8'
down_revision: Union[str, Sequence[str], None] = 'h4i0j6k1l4m5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add last_confirmed_at column to snapshot tables.

    Records when a snapshot was last confirmed as current (odds unchanged)
    during a scrape cycle. Nullable — existing rows don't need a value.
    """
    op.add_column(
        'odds_snapshots',
        sa.Column('last_confirmed_at', sa.DateTime(), nullable=True)
    )
    op.add_column(
        'competitor_odds_snapshots',
        sa.Column('last_confirmed_at', sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    """Remove last_confirmed_at column from snapshot tables."""
    op.drop_column('competitor_odds_snapshots', 'last_confirmed_at')
    op.drop_column('odds_snapshots', 'last_confirmed_at')
