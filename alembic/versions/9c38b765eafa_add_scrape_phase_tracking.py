"""add_scrape_phase_tracking

Revision ID: 9c38b765eafa
Revises: da9c6551d08b
Create Date: 2026-01-22 01:11:49.794909

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c38b765eafa'
down_revision: Union[str, Sequence[str], None] = 'da9c6551d08b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add scrape phase tracking infrastructure.

    - Add phase tracking columns to scrape_runs table
    - Create scrape_phase_logs table for audit trail
    """
    # Add new columns to scrape_runs (all nullable for backward compatibility)
    op.add_column(
        'scrape_runs',
        sa.Column('current_phase', sa.String(length=30), nullable=True)
    )
    op.add_column(
        'scrape_runs',
        sa.Column('current_platform', sa.String(length=20), nullable=True)
    )
    op.add_column(
        'scrape_runs',
        sa.Column('platform_status', sa.JSON(), nullable=True)
    )

    # Create scrape_phase_logs table for detailed phase audit trail
    op.create_table(
        'scrape_phase_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scrape_run_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=True),
        sa.Column('phase', sa.String(length=30), nullable=False),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('events_processed', sa.Integer(), nullable=True),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ['scrape_run_id'],
            ['scrape_runs.id'],
            name=op.f('fk_scrape_phase_logs_scrape_run_id_scrape_runs')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_scrape_phase_logs'))
    )

    # Create index for efficient queries by scrape_run_id
    op.create_index(
        'idx_scrape_phase_logs_run_id',
        'scrape_phase_logs',
        ['scrape_run_id'],
        unique=False
    )


def downgrade() -> None:
    """Remove scrape phase tracking infrastructure."""
    # Drop scrape_phase_logs table and index
    op.drop_index('idx_scrape_phase_logs_run_id', table_name='scrape_phase_logs')
    op.drop_table('scrape_phase_logs')

    # Remove columns from scrape_runs
    op.drop_column('scrape_runs', 'platform_status')
    op.drop_column('scrape_runs', 'current_platform')
    op.drop_column('scrape_runs', 'current_phase')
