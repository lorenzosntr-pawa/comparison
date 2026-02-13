"""add_market_mapping_tables

Revision ID: m9n0o1p2q3r4
Revises: l8m4n0o6p2q3
Create Date: 2026-02-13 12:00:00.000000

Creates database schema for market mapping utility (Phase 101):
1. user_market_mappings: User-defined market mappings with JSONB outcome data
2. mapping_audit_log: Audit trail for all mapping changes
3. unmapped_market_log: Discovery log for unmapped markets
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision: str = 'm9n0o1p2q3r4'
down_revision: Union[str, Sequence[str], None] = 'l8m4n0o6p2q3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create market mapping tables with indexes.

    Creates:
    - user_market_mappings: User-defined mappings with platform IDs
    - mapping_audit_log: Audit trail for changes
    - unmapped_market_log: Discovery log for unmapped markets
    """
    # 1. Create user_market_mappings table
    op.create_table(
        'user_market_mappings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('canonical_id', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('betpawa_id', sa.String(length=50), nullable=True),
        sa.Column('sportybet_id', sa.String(length=50), nullable=True),
        sa.Column('bet9ja_key', sa.String(length=50), nullable=True),
        sa.Column('outcome_mapping', JSONB(), nullable=False),
        sa.Column('priority', sa.Integer(), server_default='0', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_market_mappings')),
        sa.UniqueConstraint('canonical_id', name=op.f('uq_user_market_mappings_canonical_id'))
    )

    # Indexes for user_market_mappings
    op.create_index(
        'idx_user_mappings_active',
        'user_market_mappings',
        ['is_active'],
        unique=False,
        postgresql_where=sa.text('is_active = TRUE')
    )
    op.create_index(
        'idx_user_mappings_betpawa',
        'user_market_mappings',
        ['betpawa_id'],
        unique=False,
        postgresql_where=sa.text('betpawa_id IS NOT NULL')
    )
    op.create_index(
        'idx_user_mappings_sportybet',
        'user_market_mappings',
        ['sportybet_id'],
        unique=False,
        postgresql_where=sa.text('sportybet_id IS NOT NULL')
    )
    op.create_index(
        'idx_user_mappings_bet9ja',
        'user_market_mappings',
        ['bet9ja_key'],
        unique=False,
        postgresql_where=sa.text('bet9ja_key IS NOT NULL')
    )

    # 2. Create mapping_audit_log table
    op.create_table(
        'mapping_audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mapping_id', sa.Integer(), nullable=True),
        sa.Column('canonical_id', sa.String(length=100), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('old_value', JSONB(), nullable=True),
        sa.Column('new_value', JSONB(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ['mapping_id'],
            ['user_market_mappings.id'],
            name=op.f('fk_mapping_audit_log_mapping_id_user_market_mappings'),
            ondelete='SET NULL'
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_mapping_audit_log'))
    )

    # Indexes for mapping_audit_log
    op.create_index('idx_audit_log_mapping', 'mapping_audit_log', ['mapping_id'], unique=False)
    op.create_index('idx_audit_log_canonical', 'mapping_audit_log', ['canonical_id'], unique=False)
    op.create_index('idx_audit_log_action', 'mapping_audit_log', ['action'], unique=False)
    op.create_index('idx_audit_log_created', 'mapping_audit_log', ['created_at'], unique=False)

    # 3. Create unmapped_market_log table
    op.create_table(
        'unmapped_market_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('external_market_id', sa.String(length=100), nullable=False),
        sa.Column('market_name', sa.String(length=255), nullable=True),
        sa.Column('sample_outcomes', JSONB(), nullable=True),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('occurrence_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.String(length=20), server_default='NEW', nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_unmapped_market_log')),
        sa.UniqueConstraint('source', 'external_market_id', name='uq_unmapped_source_market')
    )

    # Indexes for unmapped_market_log
    op.create_index('idx_unmapped_source', 'unmapped_market_log', ['source'], unique=False)
    op.create_index('idx_unmapped_status', 'unmapped_market_log', ['status'], unique=False)
    op.create_index('idx_unmapped_occurrences', 'unmapped_market_log', [sa.text('occurrence_count DESC')], unique=False)
    op.create_index('idx_unmapped_last_seen', 'unmapped_market_log', [sa.text('last_seen_at DESC')], unique=False)


def downgrade() -> None:
    """Drop all market mapping tables in reverse order."""
    # Drop unmapped_market_log indexes
    op.drop_index('idx_unmapped_last_seen', table_name='unmapped_market_log')
    op.drop_index('idx_unmapped_occurrences', table_name='unmapped_market_log')
    op.drop_index('idx_unmapped_status', table_name='unmapped_market_log')
    op.drop_index('idx_unmapped_source', table_name='unmapped_market_log')
    op.drop_table('unmapped_market_log')

    # Drop mapping_audit_log indexes
    op.drop_index('idx_audit_log_created', table_name='mapping_audit_log')
    op.drop_index('idx_audit_log_action', table_name='mapping_audit_log')
    op.drop_index('idx_audit_log_canonical', table_name='mapping_audit_log')
    op.drop_index('idx_audit_log_mapping', table_name='mapping_audit_log')
    op.drop_table('mapping_audit_log')

    # Drop user_market_mappings indexes
    op.drop_index('idx_user_mappings_bet9ja', table_name='user_market_mappings')
    op.drop_index('idx_user_mappings_sportybet', table_name='user_market_mappings')
    op.drop_index('idx_user_mappings_betpawa', table_name='user_market_mappings')
    op.drop_index('idx_user_mappings_active', table_name='user_market_mappings')
    op.drop_table('user_market_mappings')
