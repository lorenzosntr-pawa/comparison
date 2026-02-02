"""initial schema

Revision ID: 845263fcf673
Revises:
Create Date: 2026-01-20 12:50:06.778956

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "845263fcf673"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables with partitioned odds_snapshots."""
    # 1. Create sports table
    op.create_table(
        "sports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sports")),
        sa.UniqueConstraint("name", name=op.f("uq_sports_name")),
        sa.UniqueConstraint("slug", name=op.f("uq_sports_slug")),
    )

    # 2. Create tournaments table
    op.create_table(
        "tournaments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sport_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("sportradar_id", sa.String(length=100), nullable=True),
        sa.ForeignKeyConstraint(
            ["sport_id"],
            ["sports.id"],
            name=op.f("fk_tournaments_sport_id_sports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_tournaments")),
        sa.UniqueConstraint("sportradar_id", name=op.f("uq_tournaments_sportradar_id")),
    )

    # 3. Create bookmakers table
    op.create_table(
        "bookmakers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("base_url", sa.String(length=500), nullable=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_bookmakers")),
        sa.UniqueConstraint("name", name=op.f("uq_bookmakers_name")),
        sa.UniqueConstraint("slug", name=op.f("uq_bookmakers_slug")),
    )

    # 4. Create events table
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tournament_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=500), nullable=False),
        sa.Column("home_team", sa.String(length=255), nullable=False),
        sa.Column("away_team", sa.String(length=255), nullable=False),
        sa.Column("kickoff", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sportradar_id", sa.String(length=100), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["tournament_id"],
            ["tournaments.id"],
            name=op.f("fk_events_tournament_id_tournaments"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_events")),
        sa.UniqueConstraint("sportradar_id", name=op.f("uq_events_sportradar_id")),
    )

    # 5. Create event_bookmakers table (links events to bookmakers)
    op.create_table(
        "event_bookmakers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("bookmaker_id", sa.Integer(), nullable=False),
        sa.Column("external_event_id", sa.String(length=100), nullable=False),
        sa.Column("event_url", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["bookmaker_id"],
            ["bookmakers.id"],
            name=op.f("fk_event_bookmakers_bookmaker_id_bookmakers"),
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_event_bookmakers_event_id_events"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_event_bookmakers")),
        sa.UniqueConstraint(
            "event_id", "bookmaker_id", name="uq_event_bookmaker"
        ),
    )

    # 6. Create scrape_runs table
    op.create_table(
        "scrape_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="pending",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("events_scraped", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("events_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("trigger", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scrape_runs")),
    )
    op.create_index(
        "idx_scrape_runs_status", "scrape_runs", ["status"], unique=False
    )
    op.create_index(
        "idx_scrape_runs_started", "scrape_runs", ["started_at"], unique=False
    )

    # 7. Create scrape_errors table
    op.create_table(
        "scrape_errors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scrape_run_id", sa.Integer(), nullable=False),
        sa.Column("bookmaker_id", sa.Integer(), nullable=True),
        sa.Column("event_id", sa.Integer(), nullable=True),
        sa.Column("error_type", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["bookmaker_id"],
            ["bookmakers.id"],
            name=op.f("fk_scrape_errors_bookmaker_id_bookmakers"),
        ),
        sa.ForeignKeyConstraint(
            ["event_id"],
            ["events.id"],
            name=op.f("fk_scrape_errors_event_id_events"),
        ),
        sa.ForeignKeyConstraint(
            ["scrape_run_id"],
            ["scrape_runs.id"],
            name=op.f("fk_scrape_errors_scrape_run_id_scrape_runs"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scrape_errors")),
    )
    op.create_index(
        "idx_scrape_errors_run", "scrape_errors", ["scrape_run_id"], unique=False
    )
    op.create_index(
        "idx_scrape_errors_bookmaker", "scrape_errors", ["bookmaker_id"], unique=False
    )

    # 8. Create odds_snapshots as a PARTITIONED table
    # We use raw SQL because SQLAlchemy doesn't natively support PARTITION BY
    op.execute("""
        CREATE TABLE odds_snapshots (
            id BIGSERIAL,
            event_id INTEGER NOT NULL,
            bookmaker_id INTEGER NOT NULL,
            captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            scrape_run_id INTEGER,
            raw_response JSONB,
            PRIMARY KEY (id, captured_at),
            CONSTRAINT fk_snapshots_event FOREIGN KEY (event_id) REFERENCES events(id),
            CONSTRAINT fk_snapshots_bookmaker FOREIGN KEY (bookmaker_id) REFERENCES bookmakers(id),
            CONSTRAINT fk_snapshots_scrape_run FOREIGN KEY (scrape_run_id) REFERENCES scrape_runs(id)
        ) PARTITION BY RANGE (captured_at)
    """)

    # Create indexes on partitioned table (will propagate to partitions)
    op.execute("CREATE INDEX idx_snapshots_event ON odds_snapshots (event_id)")
    op.execute("CREATE INDEX idx_snapshots_bookmaker ON odds_snapshots (bookmaker_id)")
    op.execute(
        "CREATE INDEX idx_snapshots_event_time ON odds_snapshots (event_id, captured_at DESC)"
    )
    op.execute(
        "CREATE INDEX idx_snapshots_captured_brin ON odds_snapshots "
        "USING BRIN (captured_at) WITH (pages_per_range = 32)"
    )

    # Create default partition for data that doesn't match other partitions
    op.execute(
        "CREATE TABLE odds_snapshots_default PARTITION OF odds_snapshots DEFAULT"
    )


    # Optional: If pg_partman is available, configure it for automatic partition management
    # This is nice-to-have - partitions can also be created manually
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_partman') THEN
                PERFORM partman.create_parent(
                    p_parent_table := 'public.odds_snapshots',
                    p_control := 'captured_at',
                    p_type := 'native',
                    p_interval := 'daily',
                    p_premake := 7
                );
                UPDATE partman.part_config
                SET retention = '30 days', retention_keep_table = false
                WHERE parent_table = 'public.odds_snapshots';
            END IF;
        END $$;
    """)

    # 9. Create market_odds table
    # Note: No FK to odds_snapshots because partitioned tables can't have FKs
    # referencing non-unique columns (id alone isn't unique, only id+captured_at is)
    op.create_table(
        "market_odds",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("snapshot_id", sa.BigInteger(), nullable=False),
        sa.Column("betpawa_market_id", sa.String(length=50), nullable=False),
        sa.Column("betpawa_market_name", sa.String(length=255), nullable=False),
        sa.Column("line", sa.Float(), nullable=True),
        sa.Column("handicap_type", sa.String(length=50), nullable=True),
        sa.Column("handicap_home", sa.Float(), nullable=True),
        sa.Column("handicap_away", sa.Float(), nullable=True),
        sa.Column("outcomes", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_market_odds")),
    )
    op.create_index(
        "idx_market_odds_snapshot", "market_odds", ["snapshot_id"], unique=False
    )
    op.create_index(
        "idx_market_odds_market", "market_odds", ["betpawa_market_id"], unique=False
    )


def downgrade() -> None:
    """Drop all tables in reverse order."""
    # Drop market_odds first (references odds_snapshots)
    op.drop_index("idx_market_odds_market", table_name="market_odds")
    op.drop_index("idx_market_odds_snapshot", table_name="market_odds")
    op.drop_table("market_odds")

    # Drop odds_snapshots partitioned table (drops all partitions too)
    op.execute("DROP TABLE odds_snapshots CASCADE")

    # Drop scrape_errors (references scrape_runs, bookmakers, events)
    op.drop_index("idx_scrape_errors_bookmaker", table_name="scrape_errors")
    op.drop_index("idx_scrape_errors_run", table_name="scrape_errors")
    op.drop_table("scrape_errors")

    # Drop scrape_runs
    op.drop_index("idx_scrape_runs_started", table_name="scrape_runs")
    op.drop_index("idx_scrape_runs_status", table_name="scrape_runs")
    op.drop_table("scrape_runs")

    # Drop event_bookmakers (references events, bookmakers)
    op.drop_table("event_bookmakers")

    # Drop events (references tournaments)
    op.drop_table("events")

    # Drop bookmakers
    op.drop_table("bookmakers")

    # Drop tournaments (references sports)
    op.drop_table("tournaments")

    # Drop sports
    op.drop_table("sports")
