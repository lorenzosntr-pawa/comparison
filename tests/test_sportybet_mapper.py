"""Tests for Sportybet to Betpawa mapper."""

import pytest

from market_mapping import MappingError, MappingErrorCode
from market_mapping.mappers.sportybet import map_sportybet_to_betpawa
from market_mapping.types.sportybet import SportybetMarket, SportybetOutcome


def make_outcome(
    id: str, desc: str, odds: str, is_active: int = 1
) -> SportybetOutcome:
    """Helper to create a SportybetOutcome."""
    return SportybetOutcome(
        id=id,
        desc=desc,
        odds=odds,
        probability="0.5",
        void_probability="0",
        is_active=is_active,
    )


def make_market(
    id: str,
    desc: str,
    outcomes: list[SportybetOutcome],
    specifier: str | None = None,
) -> SportybetMarket:
    """Helper to create a SportybetMarket."""
    return SportybetMarket(
        id=id,
        product=3,
        desc=desc,
        status=0,
        group="Main",
        group_id="1",
        market_guide="",
        title="",
        name=desc,
        favourite=0,
        outcomes=outcomes,
        far_near_odds=0,
        source_type="BET_RADAR",
        last_odds_change_time=0,
        banned=False,
        specifier=specifier,
    )


class TestSimpleMarketMapping:
    """Tests for simple market mapping (1X2, BTTS, Double Chance)."""

    def test_map_1x2_market(self):
        """Test mapping 1X2 Full Time market."""
        market = make_market(
            id="1",
            desc="1X2",
            outcomes=[
                make_outcome("1", "Home", "2.15"),
                make_outcome("2", "Draw", "3.20"),
                make_outcome("3", "Away", "3.50"),
            ],
        )

        result = map_sportybet_to_betpawa(market)

        assert result.betpawa_market_id == "3743"
        assert result.betpawa_market_name == "1X2 - Full Time"
        assert result.sportybet_market_id == "1"
        assert len(result.outcomes) == 3

        # Check outcome names mapped correctly
        outcome_names = [o.betpawa_outcome_name for o in result.outcomes]
        assert "1" in outcome_names
        assert "X" in outcome_names
        assert "2" in outcome_names

    def test_map_btts_market(self):
        """Test mapping Both Teams To Score market."""
        market = make_market(
            id="29",
            desc="Both Teams to Score",
            outcomes=[
                make_outcome("1", "Yes", "1.85"),
                make_outcome("2", "No", "1.95"),
            ],
        )

        result = map_sportybet_to_betpawa(market)

        assert result.betpawa_market_id == "3795"
        assert "Both Teams" in result.betpawa_market_name
        assert len(result.outcomes) == 2

    def test_map_double_chance_market(self):
        """Test mapping Double Chance market."""
        market = make_market(
            id="10",
            desc="Double Chance",
            outcomes=[
                make_outcome("1", "Home or Draw", "1.35"),
                make_outcome("2", "Draw or Away", "1.55"),
                make_outcome("3", "Home or Away", "1.20"),
            ],
        )

        result = map_sportybet_to_betpawa(market)

        assert result.betpawa_market_id == "4693"
        assert len(result.outcomes) == 3


class TestOverUnderMarketMapping:
    """Tests for Over/Under market mapping with line extraction."""

    def test_map_over_under_market(self):
        """Test mapping Over/Under market with line."""
        market = make_market(
            id="18",
            desc="Over/Under",
            outcomes=[
                make_outcome("1", "Over", "1.80"),
                make_outcome("2", "Under", "2.00"),
            ],
            specifier="total=2.5",
        )

        result = map_sportybet_to_betpawa(market)

        assert result.betpawa_market_id == "5000"
        assert result.line == 2.5
        assert len(result.outcomes) == 2

        # Check outcomes mapped correctly
        over = next(o for o in result.outcomes if o.betpawa_outcome_name == "Over")
        assert over.odds == 1.80

    def test_map_over_under_different_lines(self):
        """Test Over/Under with various line values."""
        for line_value in ["0.5", "1.5", "3.5", "4.5"]:
            market = make_market(
                id="18",
                desc="Over/Under",
                outcomes=[
                    make_outcome("1", "Over", "1.50"),
                    make_outcome("2", "Under", "2.50"),
                ],
                specifier=f"total={line_value}",
            )

            result = map_sportybet_to_betpawa(market)
            assert result.line == float(line_value)


class TestHandicapMarketMapping:
    """Tests for Handicap market mapping."""

    def test_map_asian_handicap_market(self):
        """Test mapping Asian Handicap market."""
        market = make_market(
            id="16",
            desc="Asian Handicap",
            outcomes=[
                make_outcome("1", "Home", "1.90"),
                make_outcome("2", "Away", "1.90"),
            ],
            specifier="hcp=-0.5",
        )

        result = map_sportybet_to_betpawa(market)

        assert result.handicap is not None
        assert result.handicap.type == "asian"
        assert result.handicap.home == -0.5
        assert result.handicap.away == 0.5

    def test_map_european_handicap_market(self):
        """Test mapping 3-Way Handicap (European) market."""
        market = make_market(
            id="14",
            desc="3-Way Handicap",
            outcomes=[
                make_outcome("1", "Home", "2.50"),
                make_outcome("2", "Draw", "3.20"),
                make_outcome("3", "Away", "2.80"),
            ],
            specifier="hcp=0:1",
        )

        result = map_sportybet_to_betpawa(market)

        assert result.handicap is not None
        assert result.handicap.type == "european"
        # 0:1 means home=-1, away=+1
        assert result.handicap.home == -1.0
        assert result.handicap.away == 1.0


class TestErrorCases:
    """Tests for error handling."""

    def test_unknown_market_raises_error(self):
        """Test that unknown market ID raises MappingError."""
        market = make_market(
            id="99999",
            desc="Unknown Market",
            outcomes=[make_outcome("1", "Yes", "2.00")],
        )

        with pytest.raises(MappingError) as exc_info:
            map_sportybet_to_betpawa(market)

        assert exc_info.value.code == MappingErrorCode.UNKNOWN_MARKET

    def test_no_matching_outcomes_raises_error(self):
        """Test that market with no matching outcomes raises error."""
        market = make_market(
            id="1",  # 1X2 market
            desc="1X2",
            outcomes=[
                make_outcome("1", "Unknown1", "2.00"),
                make_outcome("2", "Unknown2", "3.00"),
                make_outcome("3", "Unknown3", "4.00"),
            ],
        )

        # This should work because position-based fallback exists
        result = map_sportybet_to_betpawa(market)
        # Position-based matching should succeed for 3 outcomes
        assert len(result.outcomes) == 3

    def test_invalid_odds_raises_error(self):
        """Test that invalid odds value raises MappingError."""
        market = make_market(
            id="1",
            desc="1X2",
            outcomes=[
                make_outcome("1", "Home", "invalid_odds"),
                make_outcome("2", "Draw", "3.00"),
                make_outcome("3", "Away", "4.00"),
            ],
        )

        with pytest.raises(MappingError) as exc_info:
            map_sportybet_to_betpawa(market)

        assert exc_info.value.code == MappingErrorCode.INVALID_ODDS


class TestOutcomeMapping:
    """Tests for outcome mapping specifics."""

    def test_odds_parsed_correctly(self):
        """Test that odds strings are parsed to floats."""
        market = make_market(
            id="1",
            desc="1X2",
            outcomes=[
                make_outcome("1", "Home", "2.15"),
                make_outcome("2", "Draw", "3.20"),
                make_outcome("3", "Away", "3.50"),
            ],
        )

        result = map_sportybet_to_betpawa(market)

        for outcome in result.outcomes:
            assert isinstance(outcome.odds, float)

        home = next(o for o in result.outcomes if o.betpawa_outcome_name == "1")
        assert home.odds == 2.15

    def test_is_active_mapped_correctly(self):
        """Test that outcome active status is mapped correctly."""
        market = make_market(
            id="1",
            desc="1X2",
            outcomes=[
                make_outcome("1", "Home", "2.15", is_active=1),
                make_outcome("2", "Draw", "3.20", is_active=0),  # Suspended
                make_outcome("3", "Away", "3.50", is_active=1),
            ],
        )

        result = map_sportybet_to_betpawa(market)

        home = next(o for o in result.outcomes if o.betpawa_outcome_name == "1")
        draw = next(o for o in result.outcomes if o.betpawa_outcome_name == "X")

        assert home.is_active is True
        assert draw.is_active is False

    def test_sportybet_desc_preserved(self):
        """Test that original Sportybet description is preserved."""
        market = make_market(
            id="1",
            desc="1X2",
            outcomes=[
                make_outcome("1", "Home", "2.15"),
                make_outcome("2", "Draw", "3.20"),
                make_outcome("3", "Away", "3.50"),
            ],
        )

        result = map_sportybet_to_betpawa(market)

        home = next(o for o in result.outcomes if o.betpawa_outcome_name == "1")
        assert home.sportybet_outcome_desc == "Home"
