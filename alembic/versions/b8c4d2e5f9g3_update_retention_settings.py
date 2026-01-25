"""update_retention_settings

Revision ID: b8c4d2e5f9g3
Revises: a7b3c1d4e8f2
Create Date: 2026-01-25 03:14:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8c4d2e5f9g3'
down_revision: Union[str, Sequence[str], None] = 'a7b3c1d4e8f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename history_retention_days to odds_retention_days and add new retention fields."""
    # Rename history_retention_days to odds_retention_days
    op.alter_column(
        'settings',
        'history_retention_days',
        new_column_name='odds_retention_days'
    )

    # Update default from 7 to 30 for existing rows
    op.execute("UPDATE settings SET odds_retention_days = 30 WHERE odds_retention_days = 7")

    # Add match_retention_days column
    op.add_column(
        'settings',
        sa.Column('match_retention_days', sa.Integer(), nullable=False, server_default='30')
    )

    # Add cleanup_frequency_hours column
    op.add_column(
        'settings',
        sa.Column('cleanup_frequency_hours', sa.Integer(), nullable=False, server_default='24')
    )


def downgrade() -> None:
    """Revert to single history_retention_days column."""
    # Drop new columns
    op.drop_column('settings', 'cleanup_frequency_hours')
    op.drop_column('settings', 'match_retention_days')

    # Rename odds_retention_days back to history_retention_days
    op.alter_column(
        'settings',
        'odds_retention_days',
        new_column_name='history_retention_days'
    )

    # Revert default back to 7
    op.execute("UPDATE settings SET history_retention_days = 7 WHERE history_retention_days = 30")
