"""Cleanup service for data retention management."""

import time
from datetime import datetime, timedelta, timezone

import structlog
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas.cleanup import (
    CleanupPreview,
    CleanupResult,
    DataStats,
    PlatformCount,
    TableStats,
)
from src.db.models.competitor import (
    CompetitorEvent,
    CompetitorMarketOdds,
    CompetitorOddsSnapshot,
    CompetitorTournament,
)
from src.db.models.event import Event, EventBookmaker
from src.db.models.odds import MarketOdds, OddsSnapshot
from src.db.models.scrape import ScrapeBatch, ScrapeError, ScrapePhaseLog, ScrapeRun
from src.db.models.sport import Tournament

logger = structlog.get_logger()

BATCH_SIZE = 1000


async def get_table_stats(
    session: AsyncSession,
    model: type,
    date_column: str,
) -> TableStats:
    """Get count and date range for a table."""
    date_attr = getattr(model, date_column)

    count_result = await session.execute(select(func.count(model.id)))
    count = count_result.scalar_one()

    if count == 0:
        return TableStats(count=0)

    oldest_result = await session.execute(select(func.min(date_attr)))
    newest_result = await session.execute(select(func.max(date_attr)))

    return TableStats(
        count=count,
        oldest=oldest_result.scalar_one(),
        newest=newest_result.scalar_one(),
    )


async def get_data_stats(session: AsyncSession) -> DataStats:
    """Get comprehensive data statistics for all tables.

    Returns counts, date ranges, and platform breakdowns.
    """
    log = logger.bind(operation="get_data_stats")
    log.info("Gathering data statistics")

    # Core tables
    odds_stats = await get_table_stats(session, OddsSnapshot, "captured_at")
    competitor_odds_stats = await get_table_stats(
        session, CompetitorOddsSnapshot, "captured_at"
    )
    events_stats = await get_table_stats(session, Event, "kickoff")
    competitor_events_stats = await get_table_stats(session, CompetitorEvent, "kickoff")
    tournaments_stats = await get_table_stats(session, Tournament, "id")  # No date
    competitor_tournaments_stats = await get_table_stats(
        session, CompetitorTournament, "id"
    )
    scrape_runs_stats = await get_table_stats(session, ScrapeRun, "started_at")
    scrape_batches_stats = await get_table_stats(session, ScrapeBatch, "started_at")

    # For tournaments, we don't have dates, so set oldest/newest to None
    tournaments_stats.oldest = None
    tournaments_stats.newest = None
    competitor_tournaments_stats.oldest = None
    competitor_tournaments_stats.newest = None

    # Events by platform (bookmaker)
    events_by_platform_result = await session.execute(
        select(
            EventBookmaker.bookmaker_id,
            func.count(func.distinct(EventBookmaker.event_id)),
        ).group_by(EventBookmaker.bookmaker_id)
    )
    events_by_platform = [
        PlatformCount(platform=f"bookmaker_{row[0]}", count=row[1])
        for row in events_by_platform_result.all()
    ]

    # Competitor events by source
    competitor_by_source_result = await session.execute(
        select(CompetitorEvent.source, func.count(CompetitorEvent.id)).group_by(
            CompetitorEvent.source
        )
    )
    competitor_events_by_source = [
        PlatformCount(platform=row[0], count=row[1])
        for row in competitor_by_source_result.all()
    ]

    log.info(
        "Data statistics gathered",
        odds_count=odds_stats.count,
        events_count=events_stats.count,
    )

    return DataStats(
        odds_snapshots=odds_stats,
        competitor_odds_snapshots=competitor_odds_stats,
        events=events_stats,
        competitor_events=competitor_events_stats,
        tournaments=tournaments_stats,
        competitor_tournaments=competitor_tournaments_stats,
        scrape_runs=scrape_runs_stats,
        scrape_batches=scrape_batches_stats,
        events_by_platform=events_by_platform,
        competitor_events_by_source=competitor_events_by_source,
    )


async def preview_cleanup(
    session: AsyncSession,
    odds_days: int,
    match_days: int,
) -> CleanupPreview:
    """Preview what would be deleted by cleanup.

    Args:
        session: Database session.
        odds_days: Delete odds older than this many days.
        match_days: Delete matches with kickoff older than this many days.

    Returns:
        CleanupPreview with counts of records to be deleted.
    """
    log = logger.bind(operation="preview_cleanup", odds_days=odds_days, match_days=match_days)
    log.info("Calculating cleanup preview")

    now = datetime.now(timezone.utc)
    odds_cutoff = now - timedelta(days=odds_days)
    match_cutoff = now - timedelta(days=match_days)

    # Count odds snapshots to delete
    odds_count_result = await session.execute(
        select(func.count(OddsSnapshot.id)).where(OddsSnapshot.captured_at < odds_cutoff)
    )
    odds_count = odds_count_result.scalar_one()

    # Count competitor odds snapshots
    competitor_odds_count_result = await session.execute(
        select(func.count(CompetitorOddsSnapshot.id)).where(
            CompetitorOddsSnapshot.captured_at < odds_cutoff
        )
    )
    competitor_odds_count = competitor_odds_count_result.scalar_one()

    # Count scrape runs
    scrape_runs_count_result = await session.execute(
        select(func.count(ScrapeRun.id)).where(ScrapeRun.started_at < odds_cutoff)
    )
    scrape_runs_count = scrape_runs_count_result.scalar_one()

    # Count scrape batches (those with all runs to be deleted)
    scrape_batches_count_result = await session.execute(
        select(func.count(ScrapeBatch.id)).where(ScrapeBatch.started_at < odds_cutoff)
    )
    scrape_batches_count = scrape_batches_count_result.scalar_one()

    # Count events by kickoff
    events_count_result = await session.execute(
        select(func.count(Event.id)).where(Event.kickoff < match_cutoff)
    )
    events_count = events_count_result.scalar_one()

    # Count competitor events
    competitor_events_count_result = await session.execute(
        select(func.count(CompetitorEvent.id)).where(
            CompetitorEvent.kickoff < match_cutoff
        )
    )
    competitor_events_count = competitor_events_count_result.scalar_one()

    # Count orphaned tournaments (would have no events after cleanup)
    # Subquery for event IDs that will remain
    remaining_event_ids = select(Event.id).where(Event.kickoff >= match_cutoff)
    orphaned_tournaments_result = await session.execute(
        select(func.count(Tournament.id)).where(
            ~Tournament.id.in_(
                select(func.distinct(Event.tournament_id)).where(
                    Event.kickoff >= match_cutoff
                )
            )
        )
    )
    tournaments_count = orphaned_tournaments_result.scalar_one()

    # Count orphaned competitor tournaments
    orphaned_competitor_tournaments_result = await session.execute(
        select(func.count(CompetitorTournament.id)).where(
            ~CompetitorTournament.id.in_(
                select(func.distinct(CompetitorEvent.tournament_id)).where(
                    CompetitorEvent.kickoff >= match_cutoff
                )
            )
        )
    )
    competitor_tournaments_count = orphaned_competitor_tournaments_result.scalar_one()

    log.info(
        "Cleanup preview calculated",
        odds_count=odds_count,
        events_count=events_count,
        tournaments_count=tournaments_count,
    )

    return CleanupPreview(
        odds_cutoff_date=odds_cutoff,
        match_cutoff_date=match_cutoff,
        odds_snapshots_count=odds_count,
        competitor_odds_snapshots_count=competitor_odds_count,
        scrape_runs_count=scrape_runs_count,
        scrape_batches_count=scrape_batches_count,
        events_count=events_count,
        competitor_events_count=competitor_events_count,
        tournaments_count=tournaments_count,
        competitor_tournaments_count=competitor_tournaments_count,
    )


async def _batch_delete(
    session: AsyncSession,
    model: type,
    condition,
    log: structlog.BoundLogger,
) -> int:
    """Delete records in batches to avoid long locks.

    Returns total number of deleted records.
    """
    total_deleted = 0
    table_name = model.__tablename__

    while True:
        # Select IDs to delete in this batch
        subq = select(model.id).where(condition).limit(BATCH_SIZE)
        result = await session.execute(delete(model).where(model.id.in_(subq)))

        if result.rowcount == 0:
            break

        await session.commit()
        total_deleted += result.rowcount
        log.debug(f"Deleted batch from {table_name}", batch_size=result.rowcount, total=total_deleted)

    return total_deleted


async def execute_cleanup(
    session: AsyncSession,
    odds_days: int,
    match_days: int,
    cleanup_run_id: int | None = None,
) -> CleanupResult:
    """Execute cleanup of old data.

    Deletes data in the correct order to respect foreign keys:
    1. Odds snapshots and their market_odds (by captured_at)
    2. Scrape runs and related tables (by started_at, same cutoff as odds)
    3. Events and event_bookmakers (by kickoff)
    4. Orphaned tournaments

    Args:
        session: Database session.
        odds_days: Delete odds older than this many days.
        match_days: Delete matches with kickoff older than this many days.
        cleanup_run_id: Optional cleanup run ID for logging.

    Returns:
        CleanupResult with counts of deleted records.
    """
    log = logger.bind(
        operation="execute_cleanup",
        odds_days=odds_days,
        match_days=match_days,
        cleanup_run_id=cleanup_run_id,
    )
    log.info("Starting cleanup execution")

    start_time = time.time()
    now = datetime.now(timezone.utc)
    odds_cutoff = now - timedelta(days=odds_days)
    match_cutoff = now - timedelta(days=match_days)

    # Track oldest dates for reporting
    oldest_odds_result = await session.execute(
        select(func.min(OddsSnapshot.captured_at)).where(
            OddsSnapshot.captured_at < odds_cutoff
        )
    )
    oldest_odds_date = oldest_odds_result.scalar_one()

    oldest_match_result = await session.execute(
        select(func.min(Event.kickoff)).where(Event.kickoff < match_cutoff)
    )
    oldest_match_date = oldest_match_result.scalar_one()

    # 1. Delete market_odds for old odds_snapshots
    log.info("Deleting old market_odds")
    old_snapshot_ids = select(OddsSnapshot.id).where(OddsSnapshot.captured_at < odds_cutoff)
    market_odds_deleted = await _batch_delete(
        session, MarketOdds, MarketOdds.snapshot_id.in_(old_snapshot_ids), log
    )

    # 2. Delete old odds_snapshots
    log.info("Deleting old odds_snapshots")
    odds_deleted = await _batch_delete(
        session, OddsSnapshot, OddsSnapshot.captured_at < odds_cutoff, log
    )

    # 3. Delete competitor_market_odds for old competitor_odds_snapshots
    log.info("Deleting old competitor_market_odds")
    old_competitor_snapshot_ids = select(CompetitorOddsSnapshot.id).where(
        CompetitorOddsSnapshot.captured_at < odds_cutoff
    )
    await _batch_delete(
        session,
        CompetitorMarketOdds,
        CompetitorMarketOdds.snapshot_id.in_(old_competitor_snapshot_ids),
        log,
    )

    # 4. Delete old competitor_odds_snapshots
    log.info("Deleting old competitor_odds_snapshots")
    competitor_odds_deleted = await _batch_delete(
        session,
        CompetitorOddsSnapshot,
        CompetitorOddsSnapshot.captured_at < odds_cutoff,
        log,
    )

    # 5. Delete scrape_errors for old runs
    log.info("Deleting old scrape_errors")
    old_run_ids = select(ScrapeRun.id).where(ScrapeRun.started_at < odds_cutoff)
    await _batch_delete(session, ScrapeError, ScrapeError.scrape_run_id.in_(old_run_ids), log)

    # 6. Delete scrape_phase_logs for old runs
    log.info("Deleting old scrape_phase_logs")
    await _batch_delete(
        session, ScrapePhaseLog, ScrapePhaseLog.scrape_run_id.in_(old_run_ids), log
    )

    # 7. Delete old scrape_runs
    log.info("Deleting old scrape_runs")
    scrape_runs_deleted = await _batch_delete(
        session, ScrapeRun, ScrapeRun.started_at < odds_cutoff, log
    )

    # 8. Delete orphaned scrape_batches
    log.info("Deleting orphaned scrape_batches")
    batches_with_runs = select(func.distinct(ScrapeRun.batch_id)).where(
        ScrapeRun.batch_id.is_not(None)
    )
    scrape_batches_deleted = await _batch_delete(
        session,
        ScrapeBatch,
        (ScrapeBatch.started_at < odds_cutoff) & ~ScrapeBatch.id.in_(batches_with_runs),
        log,
    )

    # 9. Delete event_bookmakers for old events
    log.info("Deleting old event_bookmakers")
    old_event_ids = select(Event.id).where(Event.kickoff < match_cutoff)
    await _batch_delete(
        session, EventBookmaker, EventBookmaker.event_id.in_(old_event_ids), log
    )

    # 10. Delete old events
    log.info("Deleting old events")
    events_deleted = await _batch_delete(session, Event, Event.kickoff < match_cutoff, log)

    # 11. Delete old competitor_events (cascades to odds)
    log.info("Deleting old competitor_events")
    competitor_events_deleted = await _batch_delete(
        session, CompetitorEvent, CompetitorEvent.kickoff < match_cutoff, log
    )

    # 12. Delete orphaned tournaments
    log.info("Deleting orphaned tournaments")
    tournaments_with_events = select(func.distinct(Event.tournament_id))
    tournaments_deleted = await _batch_delete(
        session, Tournament, ~Tournament.id.in_(tournaments_with_events), log
    )

    # 13. Delete orphaned competitor_tournaments
    log.info("Deleting orphaned competitor_tournaments")
    competitor_tournaments_with_events = select(
        func.distinct(CompetitorEvent.tournament_id)
    )
    competitor_tournaments_deleted = await _batch_delete(
        session,
        CompetitorTournament,
        ~CompetitorTournament.id.in_(competitor_tournaments_with_events),
        log,
    )

    duration = time.time() - start_time

    log.info(
        "Cleanup execution completed",
        odds_deleted=odds_deleted,
        events_deleted=events_deleted,
        tournaments_deleted=tournaments_deleted,
        duration_seconds=round(duration, 2),
    )

    return CleanupResult(
        odds_deleted=odds_deleted,
        competitor_odds_deleted=competitor_odds_deleted,
        scrape_runs_deleted=scrape_runs_deleted,
        scrape_batches_deleted=scrape_batches_deleted,
        events_deleted=events_deleted,
        competitor_events_deleted=competitor_events_deleted,
        tournaments_deleted=tournaments_deleted,
        competitor_tournaments_deleted=competitor_tournaments_deleted,
        oldest_odds_date=oldest_odds_date,
        oldest_match_date=oldest_match_date,
        duration_seconds=round(duration, 2),
    )
