"""add storage_samples

Revision ID: e4202dfa18d5
Revises: m9n5o1p7q3r9
Create Date: 2026-02-17 11:57:55.692246

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4202dfa18d5'
down_revision: Union[str, Sequence[str], None] = 'm9n5o1p7q3r9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create storage_samples table for tracking database size over time."""
    op.create_table('storage_samples',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sampled_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('total_bytes', sa.BigInteger(), nullable=False),
        sa.Column('table_sizes', sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_storage_samples'))
    )


def downgrade() -> None:
    """Drop storage_samples table."""
    op.drop_table('storage_samples')
