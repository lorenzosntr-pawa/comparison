"""add_scraping_tuning_settings

Revision ID: e1f7g5h8i9j0
Revises: d0e6f4g7h8i9
Create Date: 2026-01-29 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f7g5h8i9j0'
down_revision: Union[str, Sequence[str], None] = 'd0e6f4g7h8i9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add scraping tuning columns to settings table."""
    # Add columns with server_default to populate existing row
    op.add_column(
        'settings',
        sa.Column('betpawa_concurrency', sa.Integer(), nullable=False, server_default='50')
    )
    op.add_column(
        'settings',
        sa.Column('sportybet_concurrency', sa.Integer(), nullable=False, server_default='50')
    )
    op.add_column(
        'settings',
        sa.Column('bet9ja_concurrency', sa.Integer(), nullable=False, server_default='15')
    )
    op.add_column(
        'settings',
        sa.Column('bet9ja_delay_ms', sa.Integer(), nullable=False, server_default='25')
    )
    op.add_column(
        'settings',
        sa.Column('batch_size', sa.Integer(), nullable=False, server_default='50')
    )


def downgrade() -> None:
    """Remove scraping tuning columns from settings table."""
    op.drop_column('settings', 'batch_size')
    op.drop_column('settings', 'bet9ja_delay_ms')
    op.drop_column('settings', 'bet9ja_concurrency')
    op.drop_column('settings', 'sportybet_concurrency')
    op.drop_column('settings', 'betpawa_concurrency')
