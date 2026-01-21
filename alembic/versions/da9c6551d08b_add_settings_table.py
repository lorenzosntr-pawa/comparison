"""add settings table

Revision ID: da9c6551d08b
Revises: eadb8195aa4b
Create Date: 2026-01-22 00:12:27.132976

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da9c6551d08b'
down_revision: Union[str, Sequence[str], None] = 'eadb8195aa4b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create settings table
    op.create_table('settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scrape_interval_minutes', sa.Integer(), nullable=False),
        sa.Column('enabled_platforms', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_settings'))
    )

    # Insert default settings row with id=1
    op.execute(
        "INSERT INTO settings (id, scrape_interval_minutes, enabled_platforms) "
        "VALUES (1, 5, '[\"sportybet\", \"betpawa\", \"bet9ja\"]')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Delete the default settings row
    op.execute("DELETE FROM settings WHERE id = 1")

    # Drop the settings table
    op.drop_table('settings')
