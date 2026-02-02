"""add_platform_timings

Revision ID: f2g8h4i9j0k1
Revises: e1f7g5h8i9j0
Create Date: 2026-01-29 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2g8h4i9j0k1'
down_revision: Union[str, Sequence[str], None] = 'e1f7g5h8i9j0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add platform_timings column to scrape_runs."""
    op.add_column(
        'scrape_runs',
        sa.Column('platform_timings', sa.JSON(), nullable=True)
    )


def downgrade() -> None:
    """Remove platform_timings column from scrape_runs."""
    op.drop_column('scrape_runs', 'platform_timings')
