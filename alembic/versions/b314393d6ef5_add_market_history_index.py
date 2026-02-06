"""add_market_history_index

Revision ID: b314393d6ef5
Revises: j6k2l8m3n9o4
Create Date: 2026-02-06 13:24:44.686245

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b314393d6ef5'
down_revision: Union[str, Sequence[str], None] = 'j6k2l8m3n9o4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Add composite index on (snapshot_id, betpawa_market_id) to optimize
    market history queries that JOIN odds_snapshots with market_odds.
    """
    op.create_index(
        'idx_market_odds_snapshot_market',
        'market_odds',
        ['snapshot_id', 'betpawa_market_id'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_market_odds_snapshot_market', table_name='market_odds')
