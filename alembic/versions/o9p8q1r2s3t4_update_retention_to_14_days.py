"""update_retention_to_14_days

Revision ID: o9p8q1r2s3t4
Revises: n8o7p0q1r4s5
Create Date: 2026-02-24 15:30:00.000000

Update retention settings from 30 days to 14 days. Part of v2.9 migration
to reduce storage usage after switching to efficient market-level storage.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'o9p8q1r2s3t4'
down_revision: Union[str, Sequence[str], None] = 'n8o7p0q1r4s5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update retention settings to 14 days."""
    op.execute(
        "UPDATE settings SET odds_retention_days = 14, match_retention_days = 14 WHERE id = 1"
    )


def downgrade() -> None:
    """Revert retention settings to 30 days."""
    op.execute(
        "UPDATE settings SET odds_retention_days = 30, match_retention_days = 30 WHERE id = 1"
    )
