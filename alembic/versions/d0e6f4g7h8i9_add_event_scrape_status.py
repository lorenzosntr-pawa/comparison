"""add_event_scrape_status

Revision ID: d0e6f4g7h8i9
Revises: c9d5e3f6g7h8
Create Date: 2026-01-29 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd0e6f4g7h8i9'
down_revision: Union[str, Sequence[str], None] = 'c9d5e3f6g7h8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create event_scrape_status table for per-event scrape tracking."""
    op.create_table(
        'event_scrape_status',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('scrape_run_id', sa.Integer(), sa.ForeignKey('scrape_runs.id'), nullable=False),
        sa.Column('sportradar_id', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('platforms_requested', sa.JSON(), nullable=False),
        sa.Column('platforms_scraped', sa.JSON(), nullable=False),
        sa.Column('platforms_failed', sa.JSON(), nullable=False),
        sa.Column('timing_ms', sa.Integer(), nullable=False),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )

    # Indexes for efficient querying
    op.create_index('idx_event_scrape_status_run', 'event_scrape_status', ['scrape_run_id'])
    op.create_index('idx_event_scrape_status_sr_id', 'event_scrape_status', ['sportradar_id'])


def downgrade() -> None:
    """Drop event_scrape_status table."""
    op.drop_index('idx_event_scrape_status_sr_id', table_name='event_scrape_status')
    op.drop_index('idx_event_scrape_status_run', table_name='event_scrape_status')
    op.drop_table('event_scrape_status')
