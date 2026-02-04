"""add_market_group

Revision ID: g3h9i5j0k2l3
Revises: f2g8h4i9j0k1
Create Date: 2026-02-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'g3h9i5j0k2l3'
down_revision: Union[str, Sequence[str], None] = 'f2g8h4i9j0k1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add market_group column to market_odds and competitor_market_odds."""
    op.add_column(
        'market_odds',
        sa.Column('market_group', sa.String(50), nullable=True)
    )
    op.add_column(
        'competitor_market_odds',
        sa.Column('market_group', sa.String(50), nullable=True)
    )


def downgrade() -> None:
    """Remove market_group column from market_odds and competitor_market_odds."""
    op.drop_column('competitor_market_odds', 'market_group')
    op.drop_column('market_odds', 'market_group')
