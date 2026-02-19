"""add_competitor_odds_to_alerts

Add competitor_old_value and competitor_new_value columns to risk_alerts table
for displaying competitor odds in direction disagreement alerts.

Revision ID: c4d5e6f7g8h9
Revises: 29e638af388e
Create Date: 2026-02-19 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7g8h9'
down_revision: Union[str, Sequence[str], None] = '29e638af388e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add competitor odds columns to risk_alerts."""
    op.add_column('risk_alerts', sa.Column('competitor_old_value', sa.Float(), nullable=True))
    op.add_column('risk_alerts', sa.Column('competitor_new_value', sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove competitor odds columns from risk_alerts."""
    op.drop_column('risk_alerts', 'competitor_new_value')
    op.drop_column('risk_alerts', 'competitor_old_value')
