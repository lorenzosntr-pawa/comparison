"""market_groups_array

Revision ID: h4i0j6k1l4m5
Revises: g3h9i5j0k2l3
Create Date: 2026-02-04 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'h4i0j6k1l4m5'
down_revision: Union[str, Sequence[str], None] = 'g3h9i5j0k2l3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert market_group (string) to market_groups (JSON array).

    Steps:
    1. Add new market_groups column as JSON
    2. Migrate data: convert single string values to arrays
    3. Drop old market_group column
    """
    # market_odds table
    op.add_column(
        'market_odds',
        sa.Column('market_groups', postgresql.JSON(), nullable=True)
    )
    # Migrate data: convert "goals" to ["goals"], NULL stays NULL
    op.execute("""
        UPDATE market_odds
        SET market_groups = jsonb_build_array(market_group)
        WHERE market_group IS NOT NULL
    """)
    op.drop_column('market_odds', 'market_group')

    # competitor_market_odds table
    op.add_column(
        'competitor_market_odds',
        sa.Column('market_groups', postgresql.JSON(), nullable=True)
    )
    # Migrate data: convert "goals" to ["goals"], NULL stays NULL
    op.execute("""
        UPDATE competitor_market_odds
        SET market_groups = jsonb_build_array(market_group)
        WHERE market_group IS NOT NULL
    """)
    op.drop_column('competitor_market_odds', 'market_group')


def downgrade() -> None:
    """Convert market_groups (JSON array) back to market_group (string).

    Takes first element of array as the single value.
    """
    # market_odds table
    op.add_column(
        'market_odds',
        sa.Column('market_group', sa.String(50), nullable=True)
    )
    op.execute("""
        UPDATE market_odds
        SET market_group = market_groups->>0
        WHERE market_groups IS NOT NULL
    """)
    op.drop_column('market_odds', 'market_groups')

    # competitor_market_odds table
    op.add_column(
        'competitor_market_odds',
        sa.Column('market_group', sa.String(50), nullable=True)
    )
    op.execute("""
        UPDATE competitor_market_odds
        SET market_group = market_groups->>0
        WHERE market_groups IS NOT NULL
    """)
    op.drop_column('competitor_market_odds', 'market_groups')
