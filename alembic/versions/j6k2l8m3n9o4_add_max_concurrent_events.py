"""add_max_concurrent_events

Revision ID: j6k2l8m3n9o4
Revises: i5j1k7l2m6n8
Create Date: 2026-02-05 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'j6k2l8m3n9o4'
down_revision: Union[str, Sequence[str], None] = 'i5j1k7l2m6n8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add max_concurrent_events column to settings table.

    Controls how many events are scraped in parallel within each batch.
    Default 10: with 3 platforms each, that's up to 30 concurrent HTTP
    requests, well within the connection pool limit.
    """
    op.add_column(
        'settings',
        sa.Column('max_concurrent_events', sa.Integer(), nullable=False, server_default='10')
    )


def downgrade() -> None:
    """Remove max_concurrent_events column from settings table."""
    op.drop_column('settings', 'max_concurrent_events')
