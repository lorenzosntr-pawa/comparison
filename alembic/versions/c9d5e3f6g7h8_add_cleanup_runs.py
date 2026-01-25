"""add_cleanup_runs

Revision ID: c9d5e3f6g7h8
Revises: b8c4d2e5f9g3
Create Date: 2026-01-25 03:25:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d5e3f6g7h8'
down_revision: Union[str, Sequence[str], None] = 'b8c4d2e5f9g3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create cleanup_runs table for tracking cleanup execution history."""
    op.create_table(
        'cleanup_runs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('started_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('trigger', sa.String(20), nullable=False),

        # Settings used
        sa.Column('odds_retention_days', sa.Integer(), nullable=False),
        sa.Column('match_retention_days', sa.Integer(), nullable=False),

        # Deletion counts
        sa.Column('odds_deleted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('competitor_odds_deleted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('scrape_runs_deleted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('scrape_batches_deleted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('events_deleted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('competitor_events_deleted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tournaments_deleted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('competitor_tournaments_deleted', sa.Integer(), nullable=False, server_default='0'),

        # Date ranges
        sa.Column('oldest_odds_date', sa.DateTime(), nullable=True),
        sa.Column('oldest_match_date', sa.DateTime(), nullable=True),

        # Status
        sa.Column('status', sa.String(20), nullable=False, server_default='running'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
    )

    # Index for querying recent runs
    op.create_index('idx_cleanup_runs_started', 'cleanup_runs', ['started_at'])


def downgrade() -> None:
    """Drop cleanup_runs table."""
    op.drop_index('idx_cleanup_runs_started', table_name='cleanup_runs')
    op.drop_table('cleanup_runs')
