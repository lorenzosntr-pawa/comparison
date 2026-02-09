"""Tournament discovery service for competitor platforms.

Provides TournamentDiscoveryService for discovering and storing football
tournaments from SportyBet and Bet9ja APIs into the competitor_tournaments
table.

Discovery Flow:
    1. Fetch tournament hierarchy from platform API
    2. Parse country/region and tournament names
    3. Upsert into competitor_tournaments with source tracking
    4. Extract SportRadar IDs where available (SportyBet only)

Usage:
    Called at the start of each scrape cycle to pick up new tournaments
    before event scraping begins. Also available via admin API endpoint.

    service = TournamentDiscoveryService()
    results = await service.discover_all(sportybet_client, bet9ja_client, db)
    # results = {"sportybet": {"new": 5, "updated": 2}, "bet9ja": {...}}

Note:
    Bet9ja tournaments don't have SportRadar IDs at the tournament level.
    Cross-platform tournament matching relies on name similarity and
    country_raw field for future normalization.
"""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.competitor import CompetitorSource, CompetitorTournament
from src.db.models.sport import Sport
from src.scraping.clients.bet9ja import Bet9jaClient
from src.scraping.clients.sportybet import SportyBetClient

log = structlog.get_logger(__name__)


class TournamentDiscoveryService:
    """Discovers and stores competitor tournaments from SportyBet and Bet9ja."""

    async def _get_or_create_football_sport(self, db: AsyncSession) -> int:
        """Get or create the Football sport record.

        Args:
            db: Database session.

        Returns:
            Sport ID for Football.
        """
        result = await db.execute(
            select(Sport).where(Sport.name == "Football")
        )
        sport = result.scalar_one_or_none()

        if sport:
            return sport.id

        # Create Football sport if it doesn't exist
        sport = Sport(name="Football", slug="football")
        db.add(sport)
        await db.flush()
        log.info("Created Football sport", sport_id=sport.id)
        return sport.id

    async def _upsert_tournament(
        self,
        db: AsyncSession,
        source: CompetitorSource,
        external_id: str,
        name: str,
        country_raw: str | None,
        sport_id: int,
        sportradar_id: str | None = None,
    ) -> tuple[int, int]:
        """Upsert a tournament record.

        Args:
            db: Database session.
            source: Source platform (sportybet or bet9ja).
            external_id: Platform-specific tournament ID.
            name: Tournament name.
            country_raw: Raw country name from API.
            sport_id: Sport ID (FK to sports table).
            sportradar_id: SportRadar ID if available.

        Returns:
            Tuple of (new_count, updated_count) - (1, 0) for new, (0, 1) for updated, (0, 0) for unchanged.
        """
        result = await db.execute(
            select(CompetitorTournament).where(
                CompetitorTournament.source == source.value,
                CompetitorTournament.external_id == external_id,
            )
        )
        existing = result.scalar_one_or_none()

        if existing:
            # Check if update needed
            changed = False
            if existing.name != name:
                existing.name = name
                changed = True
            if existing.country_raw != country_raw:
                existing.country_raw = country_raw
                changed = True
            if sportradar_id and existing.sportradar_id != sportradar_id:
                existing.sportradar_id = sportradar_id
                changed = True

            return (0, 1) if changed else (0, 0)
        else:
            # Insert new tournament
            tournament = CompetitorTournament(
                source=source.value,
                sport_id=sport_id,
                name=name,
                country_raw=country_raw,
                external_id=external_id,
                sportradar_id=sportradar_id,
            )
            db.add(tournament)
            return (1, 0)

    async def discover_sportybet_tournaments(
        self,
        client: SportyBetClient,
        db: AsyncSession,
    ) -> tuple[int, int]:
        """Discover all SportyBet football tournaments.

        Args:
            client: SportyBet API client.
            db: Database session.

        Returns:
            Tuple of (new_count, updated_count).
        """
        log.info("Starting SportyBet tournament discovery")

        data = await client.fetch_tournaments()
        sport_id = await self._get_or_create_football_sport(db)

        new_count = 0
        updated_count = 0

        sport_list = data.get("data", {}).get("sportList", [])
        for sport in sport_list:
            if sport.get("id") != "sr:sport:1":  # Football only
                continue

            for category in sport.get("categories", []):
                country_name = category.get("name")

                for tournament in category.get("tournaments", []):
                    sr_id = tournament.get("id", "")  # e.g., "sr:tournament:17"
                    # Extract numeric ID from SportRadar ID
                    sr_id_num = sr_id.replace("sr:tournament:", "") if sr_id.startswith("sr:tournament:") else None

                    new, updated = await self._upsert_tournament(
                        db=db,
                        source=CompetitorSource.SPORTYBET,
                        external_id=sr_id,
                        name=tournament.get("name", ""),
                        country_raw=country_name,
                        sport_id=sport_id,
                        sportradar_id=sr_id_num,
                    )
                    new_count += new
                    updated_count += updated

        await db.commit()
        log.info(
            "Completed SportyBet tournament discovery",
            new_count=new_count,
            updated_count=updated_count,
        )
        return new_count, updated_count

    async def discover_bet9ja_tournaments(
        self,
        client: Bet9jaClient,
        db: AsyncSession,
    ) -> tuple[int, int]:
        """Discover all Bet9ja football tournaments.

        Args:
            client: Bet9ja API client.
            db: Database session.

        Returns:
            Tuple of (new_count, updated_count).
        """
        log.info("Starting Bet9ja tournament discovery")

        data = await client.fetch_sports()
        sport_id = await self._get_or_create_football_sport(db)

        new_count = 0
        updated_count = 0

        # Navigate: D.PAL.1 (Soccer)
        soccer = data.get("D", {}).get("PAL", {}).get("1", {})
        sport_groups = soccer.get("SG", {})

        for sg_id, sg_data in sport_groups.items():
            country_name = sg_data.get("SG_DESC")
            tournaments = sg_data.get("G", {})

            for g_id, g_data in tournaments.items():
                new, updated = await self._upsert_tournament(
                    db=db,
                    source=CompetitorSource.BET9JA,
                    external_id=g_id,
                    name=g_data.get("G_DESC", ""),
                    country_raw=country_name,
                    sport_id=sport_id,
                    sportradar_id=None,  # No SR ID at tournament level for Bet9ja
                )
                new_count += new
                updated_count += updated

        await db.commit()
        log.info(
            "Completed Bet9ja tournament discovery",
            new_count=new_count,
            updated_count=updated_count,
        )
        return new_count, updated_count

    async def discover_all(
        self,
        sportybet_client: SportyBetClient,
        bet9ja_client: Bet9jaClient,
        db: AsyncSession,
    ) -> dict:
        """Discover tournaments from all competitor platforms.

        Args:
            sportybet_client: SportyBet API client.
            bet9ja_client: Bet9ja API client.
            db: Database session.

        Returns:
            Dict with discovery results for each platform:
            {
                "sportybet": {"new": N, "updated": N},
                "bet9ja": {"new": N, "updated": N},
            }
        """
        log.info("Starting tournament discovery for all platforms")

        results: dict = {
            "sportybet": {"new": 0, "updated": 0, "error": None},
            "bet9ja": {"new": 0, "updated": 0, "error": None},
        }

        # Discover SportyBet tournaments
        try:
            new_s, upd_s = await self.discover_sportybet_tournaments(sportybet_client, db)
            results["sportybet"]["new"] = new_s
            results["sportybet"]["updated"] = upd_s
        except Exception as e:
            log.error("SportyBet tournament discovery failed", error=str(e))
            results["sportybet"]["error"] = str(e)

        # Discover Bet9ja tournaments
        try:
            new_b, upd_b = await self.discover_bet9ja_tournaments(bet9ja_client, db)
            results["bet9ja"]["new"] = new_b
            results["bet9ja"]["updated"] = upd_b
        except Exception as e:
            log.error("Bet9ja tournament discovery failed", error=str(e))
            results["bet9ja"]["error"] = str(e)

        log.info("Completed tournament discovery for all platforms", results=results)
        return results
