"""add storage_alerts

Revision ID: a41eec60ab32
Revises: e4202dfa18d5
Create Date: 2026-02-17 12:14:18.137395

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a41eec60ab32'
down_revision: Union[str, Sequence[str], None] = 'e4202dfa18d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('storage_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('message', sa.String(length=500), nullable=False),
        sa.Column('current_bytes', sa.BigInteger(), nullable=False),
        sa.Column('previous_bytes', sa.BigInteger(), nullable=False),
        sa.Column('growth_percent', sa.Float(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_storage_alerts'))
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('storage_alerts')
