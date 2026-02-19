"""add_risk_alerts_table_and_settings

Revision ID: 29e638af388e
Revises: a41eec60ab32
Create Date: 2026-02-19 11:57:23.231052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '29e638af388e'
down_revision: Union[str, Sequence[str], None] = 'a41eec60ab32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create risk_alerts table
    op.create_table('risk_alerts',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('bookmaker_slug', sa.String(length=50), nullable=False),
        sa.Column('market_id', sa.String(length=50), nullable=False),
        sa.Column('market_name', sa.String(length=255), nullable=False),
        sa.Column('line', sa.Float(), nullable=True),
        sa.Column('outcome_name', sa.String(length=100), nullable=True),
        sa.Column('alert_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('change_percent', sa.Float(), nullable=False),
        sa.Column('old_value', sa.Float(), nullable=True),
        sa.Column('new_value', sa.Float(), nullable=True),
        sa.Column('competitor_direction', sa.String(length=100), nullable=True),
        sa.Column('detected_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('event_kickoff', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], name=op.f('fk_risk_alerts_event_id_events')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_risk_alerts'))
    )

    # Create indexes for risk_alerts
    op.create_index('idx_risk_alerts_event', 'risk_alerts', ['event_id', 'status'], unique=False)
    op.create_index('idx_risk_alerts_kickoff', 'risk_alerts', ['event_kickoff'], unique=False)
    op.create_index('idx_risk_alerts_status_detected', 'risk_alerts', ['status', 'detected_at'], unique=False)

    # Add alert configuration columns to settings
    op.add_column('settings', sa.Column('alert_enabled', sa.Boolean(), server_default='true', nullable=False))
    op.add_column('settings', sa.Column('alert_threshold_warning', sa.Float(), server_default='7.0', nullable=False))
    op.add_column('settings', sa.Column('alert_threshold_elevated', sa.Float(), server_default='10.0', nullable=False))
    op.add_column('settings', sa.Column('alert_threshold_critical', sa.Float(), server_default='15.0', nullable=False))
    op.add_column('settings', sa.Column('alert_retention_days', sa.Integer(), server_default='7', nullable=False))
    op.add_column('settings', sa.Column('alert_lookback_minutes', sa.Integer(), server_default='60', nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove alert configuration columns from settings
    op.drop_column('settings', 'alert_lookback_minutes')
    op.drop_column('settings', 'alert_retention_days')
    op.drop_column('settings', 'alert_threshold_critical')
    op.drop_column('settings', 'alert_threshold_elevated')
    op.drop_column('settings', 'alert_threshold_warning')
    op.drop_column('settings', 'alert_enabled')

    # Drop risk_alerts table and indexes
    op.drop_index('idx_risk_alerts_status_detected', table_name='risk_alerts')
    op.drop_index('idx_risk_alerts_kickoff', table_name='risk_alerts')
    op.drop_index('idx_risk_alerts_event', table_name='risk_alerts')
    op.drop_table('risk_alerts')
