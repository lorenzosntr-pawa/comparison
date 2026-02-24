"""add market level tables

Revision ID: n8o7p0q1r4s5
Revises: a41eec60ab32
Create Date: 2026-02-24 11:42:25.000000

Creates market_odds_current and market_odds_history tables for the new
market-level storage architecture (Phase 106). This enables 95% storage
reduction via market-level change detection instead of snapshot-level.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'n8o7p0q1r4s5'
down_revision: Union[str, Sequence[str], None] = 'a41eec60ab32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create market_odds_current and market_odds_history tables."""
    # Create market_odds_current table
    op.create_table(
        'market_odds_current',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('bookmaker_slug', sa.String(length=20), nullable=False),
        sa.Column('betpawa_market_id', sa.String(length=50), nullable=False),
        sa.Column('betpawa_market_name', sa.String(length=255), nullable=False),
        sa.Column('line', sa.Float(), nullable=True),
        sa.Column('handicap_type', sa.String(length=50), nullable=True),
        sa.Column('handicap_home', sa.Float(), nullable=True),
        sa.Column('handicap_away', sa.Float(), nullable=True),
        sa.Column('outcomes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('market_groups', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('unavailable_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_confirmed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_market_odds_current'))
    )

    # Create unique index with COALESCE for NULL line handling
    # Using raw SQL because Alembic doesn't support expression indexes directly
    op.execute("""
        CREATE UNIQUE INDEX idx_moc_unique
        ON market_odds_current(event_id, bookmaker_slug, betpawa_market_id, COALESCE(line, 0))
    """)

    # Create regular indexes for market_odds_current
    op.create_index('idx_moc_event', 'market_odds_current', ['event_id'])
    op.create_index('idx_moc_bookmaker', 'market_odds_current', ['bookmaker_slug'])
    op.create_index('idx_moc_event_bookmaker', 'market_odds_current', ['event_id', 'bookmaker_slug'])

    # Create market_odds_history parent table with partitioning
    # Using raw SQL because Alembic doesn't support PARTITION BY directly
    op.execute("""
        CREATE TABLE market_odds_history (
            id BIGSERIAL,
            event_id INTEGER NOT NULL,
            bookmaker_slug VARCHAR(20) NOT NULL,
            betpawa_market_id VARCHAR(50) NOT NULL,
            line FLOAT,
            outcomes JSONB NOT NULL,
            captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id, captured_at)
        ) PARTITION BY RANGE (captured_at)
    """)

    # Create monthly partitions
    op.execute("""
        CREATE TABLE market_odds_history_2026_02 PARTITION OF market_odds_history
        FOR VALUES FROM ('2026-02-01') TO ('2026-03-01')
    """)
    op.execute("""
        CREATE TABLE market_odds_history_2026_03 PARTITION OF market_odds_history
        FOR VALUES FROM ('2026-03-01') TO ('2026-04-01')
    """)
    op.execute("""
        CREATE TABLE market_odds_history_2026_04 PARTITION OF market_odds_history
        FOR VALUES FROM ('2026-04-01') TO ('2026-05-01')
    """)

    # Create indexes for market_odds_history
    op.execute("""
        CREATE INDEX idx_moh_event_market_time
        ON market_odds_history(event_id, betpawa_market_id, captured_at DESC)
    """)
    op.execute("""
        CREATE INDEX idx_moh_bookmaker_market
        ON market_odds_history(bookmaker_slug, betpawa_market_id)
    """)


def downgrade() -> None:
    """Drop market_odds_current and market_odds_history tables."""
    # Drop indexes first
    op.execute("DROP INDEX IF EXISTS idx_moh_bookmaker_market")
    op.execute("DROP INDEX IF EXISTS idx_moh_event_market_time")

    # Drop partitioned table (cascades to partitions)
    op.execute("DROP TABLE IF EXISTS market_odds_history CASCADE")

    # Drop market_odds_current
    op.drop_index('idx_moc_event_bookmaker', table_name='market_odds_current')
    op.drop_index('idx_moc_bookmaker', table_name='market_odds_current')
    op.drop_index('idx_moc_event', table_name='market_odds_current')
    op.execute("DROP INDEX IF EXISTS idx_moc_unique")
    op.drop_table('market_odds_current')
