"""add_history_retention_setting

Revision ID: a7b3c1d4e8f2
Revises: 91f4cbcafaf2
Create Date: 2026-01-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b3c1d4e8f2'
down_revision: Union[str, Sequence[str], None] = '91f4cbcafaf2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add history_retention_days column to settings table."""
    op.add_column(
        'settings',
        sa.Column('history_retention_days', sa.Integer(), nullable=False, server_default='7')
    )


def downgrade() -> None:
    """Remove history_retention_days column from settings table."""
    op.drop_column('settings', 'history_retention_days')
