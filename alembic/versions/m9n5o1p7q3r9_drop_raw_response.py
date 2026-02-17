"""drop_raw_response

Revision ID: m9n5o1p7q3r9
Revises: l8m4n0o6p2q3
Create Date: 2026-02-17 10:00:00.000000

Drops raw_response columns from odds_snapshots and competitor_odds_snapshots
tables to reclaim 33GB of storage (53% of database). Phase 100 investigation
confirmed these columns are unused - no API endpoints or features read them
after scraping completes.

Storage impact:
- odds_snapshots.raw_response: ~23 GB
- competitor_odds_snapshots.raw_response: ~10 GB

Note: Space will be reclaimed gradually by PostgreSQL autovacuum.
Do NOT run VACUUM FULL - it requires exclusive table lock and would
block all operations.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'm9n5o1p7q3r9'
down_revision: Union[str, Sequence[str], None] = 'l8m4n0o6p2q3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop raw_response columns from both snapshot tables.

    This is a non-blocking operation that marks the columns as dropped.
    Actual space reclamation happens via autovacuum or manual VACUUM.
    """
    op.drop_column('odds_snapshots', 'raw_response')
    op.drop_column('competitor_odds_snapshots', 'raw_response')


def downgrade() -> None:
    """Add raw_response columns back to both snapshot tables.

    Note: Data cannot be recovered - columns will be NULL after downgrade.
    """
    op.add_column(
        'competitor_odds_snapshots',
        sa.Column('raw_response', sa.JSON(), nullable=True)
    )
    op.add_column(
        'odds_snapshots',
        sa.Column('raw_response', sa.JSON(), nullable=True)
    )
