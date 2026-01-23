"""add_competitor_tables_and_scrape_batches

Revision ID: 91f4cbcafaf2
Revises: 9c38b765eafa
Create Date: 2026-01-23 15:35:13.586040

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91f4cbcafaf2'
down_revision: Union[str, Sequence[str], None] = '9c38b765eafa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add scrape batches and competitor tables for Phase 13.

    Creates:
    - scrape_batches: Groups multiple scrape runs by batch
    - scrape_runs.batch_id: FK to scrape_batches
    - competitor_tournaments: Tournaments from SportyBet/Bet9ja
    - competitor_events: Events from competitors with SR ID linkage
    - competitor_odds_snapshots: Point-in-time odds capture
    - competitor_market_odds: Individual market odds
    """
    # 1. Create scrape_batches table
    op.create_table(
        'scrape_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('trigger', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_scrape_batches'))
    )
    op.create_index('idx_scrape_batches_started', 'scrape_batches', ['started_at'], unique=False)

    # 2. Add batch_id column to scrape_runs
    op.add_column(
        'scrape_runs',
        sa.Column('batch_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        op.f('fk_scrape_runs_batch_id_scrape_batches'),
        'scrape_runs',
        'scrape_batches',
        ['batch_id'],
        ['id']
    )

    # 3. Create competitor_tournaments table
    op.create_table(
        'competitor_tournaments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('sport_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('country_raw', sa.String(length=100), nullable=True),
        sa.Column('country_iso', sa.String(length=3), nullable=True),
        sa.Column('external_id', sa.String(length=100), nullable=False),
        sa.Column('sportradar_id', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['sport_id'],
            ['sports.id'],
            name=op.f('fk_competitor_tournaments_sport_id_sports')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_competitor_tournaments')),
        sa.UniqueConstraint('source', 'external_id', name='uq_competitor_tournaments_source_external')
    )
    op.create_index('idx_competitor_tournaments_source', 'competitor_tournaments', ['source'], unique=False)
    op.create_index('idx_competitor_tournaments_sport', 'competitor_tournaments', ['sport_id'], unique=False)
    op.create_index(
        'idx_competitor_tournaments_sr_id',
        'competitor_tournaments',
        ['sportradar_id'],
        unique=False,
        postgresql_where=sa.text('sportradar_id IS NOT NULL')
    )

    # 4. Create competitor_events table
    op.create_table(
        'competitor_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('tournament_id', sa.Integer(), nullable=False),
        sa.Column('betpawa_event_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('home_team', sa.String(length=255), nullable=False),
        sa.Column('away_team', sa.String(length=255), nullable=False),
        sa.Column('kickoff', sa.DateTime(), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=False),
        sa.Column('sportradar_id', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ['tournament_id'],
            ['competitor_tournaments.id'],
            name=op.f('fk_competitor_events_tournament_id_competitor_tournaments')
        ),
        sa.ForeignKeyConstraint(
            ['betpawa_event_id'],
            ['events.id'],
            name=op.f('fk_competitor_events_betpawa_event_id_events')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_competitor_events')),
        sa.UniqueConstraint('source', 'external_id', name='uq_competitor_events_source_external')
    )
    op.create_index('idx_competitor_events_source', 'competitor_events', ['source'], unique=False)
    op.create_index('idx_competitor_events_tournament', 'competitor_events', ['tournament_id'], unique=False)
    op.create_index('idx_competitor_events_sr_id', 'competitor_events', ['sportradar_id'], unique=False)
    op.create_index(
        'idx_competitor_events_betpawa',
        'competitor_events',
        ['betpawa_event_id'],
        unique=False,
        postgresql_where=sa.text('betpawa_event_id IS NOT NULL')
    )
    op.create_index('idx_competitor_events_kickoff', 'competitor_events', ['kickoff'], unique=False)

    # 5. Create competitor_odds_snapshots table
    op.create_table(
        'competitor_odds_snapshots',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('competitor_event_id', sa.Integer(), nullable=False),
        sa.Column('captured_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('scrape_run_id', sa.Integer(), nullable=True),
        sa.Column('raw_response', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ['competitor_event_id'],
            ['competitor_events.id'],
            name=op.f('fk_competitor_odds_snapshots_competitor_event_id_competitor_events')
        ),
        sa.ForeignKeyConstraint(
            ['scrape_run_id'],
            ['scrape_runs.id'],
            name=op.f('fk_competitor_odds_snapshots_scrape_run_id_scrape_runs')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_competitor_odds_snapshots'))
    )
    op.create_index('idx_competitor_odds_snapshots_event', 'competitor_odds_snapshots', ['competitor_event_id'], unique=False)
    op.create_index('idx_competitor_odds_snapshots_captured', 'competitor_odds_snapshots', ['captured_at'], unique=False)

    # 6. Create competitor_market_odds table
    op.create_table(
        'competitor_market_odds',
        sa.Column('id', sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column('snapshot_id', sa.BigInteger(), nullable=False),
        sa.Column('betpawa_market_id', sa.String(length=50), nullable=False),
        sa.Column('betpawa_market_name', sa.String(length=255), nullable=False),
        sa.Column('line', sa.Float(), nullable=True),
        sa.Column('handicap_type', sa.String(length=50), nullable=True),
        sa.Column('handicap_home', sa.Float(), nullable=True),
        sa.Column('handicap_away', sa.Float(), nullable=True),
        sa.Column('outcomes', sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(
            ['snapshot_id'],
            ['competitor_odds_snapshots.id'],
            name=op.f('fk_competitor_market_odds_snapshot_id_competitor_odds_snapshots')
        ),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_competitor_market_odds'))
    )
    op.create_index('idx_competitor_market_odds_snapshot', 'competitor_market_odds', ['snapshot_id'], unique=False)
    op.create_index('idx_competitor_market_odds_market', 'competitor_market_odds', ['betpawa_market_id'], unique=False)


def downgrade() -> None:
    """Drop all Phase 13 tables in reverse order."""
    # Drop competitor_market_odds
    op.drop_index('idx_competitor_market_odds_market', table_name='competitor_market_odds')
    op.drop_index('idx_competitor_market_odds_snapshot', table_name='competitor_market_odds')
    op.drop_table('competitor_market_odds')

    # Drop competitor_odds_snapshots
    op.drop_index('idx_competitor_odds_snapshots_captured', table_name='competitor_odds_snapshots')
    op.drop_index('idx_competitor_odds_snapshots_event', table_name='competitor_odds_snapshots')
    op.drop_table('competitor_odds_snapshots')

    # Drop competitor_events
    op.drop_index('idx_competitor_events_kickoff', table_name='competitor_events')
    op.drop_index('idx_competitor_events_betpawa', table_name='competitor_events')
    op.drop_index('idx_competitor_events_sr_id', table_name='competitor_events')
    op.drop_index('idx_competitor_events_tournament', table_name='competitor_events')
    op.drop_index('idx_competitor_events_source', table_name='competitor_events')
    op.drop_table('competitor_events')

    # Drop competitor_tournaments
    op.drop_index('idx_competitor_tournaments_sr_id', table_name='competitor_tournaments')
    op.drop_index('idx_competitor_tournaments_sport', table_name='competitor_tournaments')
    op.drop_index('idx_competitor_tournaments_source', table_name='competitor_tournaments')
    op.drop_table('competitor_tournaments')

    # Drop batch_id from scrape_runs
    op.drop_constraint(
        op.f('fk_scrape_runs_batch_id_scrape_batches'),
        'scrape_runs',
        type_='foreignkey'
    )
    op.drop_column('scrape_runs', 'batch_id')

    # Drop scrape_batches
    op.drop_index('idx_scrape_batches_started', table_name='scrape_batches')
    op.drop_table('scrape_batches')
