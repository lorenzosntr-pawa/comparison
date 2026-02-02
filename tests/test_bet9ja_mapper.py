"""Tests for Bet9ja to Betpawa mapper."""

import pytest

from market_mapping import MappingError, MappingErrorCode
from market_mapping.mappers.bet9ja import (
    map_bet9ja_market_to_betpawa,
    map_bet9ja_odds_to_betpawa,
)


class TestSingleMarketMapping:
    """Tests for map_bet9ja_market_to_betpawa function."""

    def test_map_1x2_market(self):
        """Test mapping 1X2 Full Time market."""
        result = map_bet9ja_market_to_betpawa(
            market_key="1X2",
            param=None,
            outcomes={"1": "1.50", "X": "3.20", "2": "2.10"},
        )

        assert result.betpawa_market_id == "3743"
        assert result.betpawa_market_name == "1X2 - Full Time"
        assert result.sportybet_market_id is None  # Bet9ja source
        assert len(result.outcomes) == 3

        # Check outcomes
        outcome_names = [o.betpawa_outcome_name for o in result.outcomes]
        assert "1" in outcome_names
        assert "X" in outcome_names
        assert "2" in outcome_names

    def test_map_btts_market(self):
        """Test mapping Both Teams To Score market."""
        result = map_bet9ja_market_to_betpawa(
            market_key="GGNG",
            param=None,
            outcomes={"Y": "1.85", "N": "1.95"},
        )

        assert result.betpawa_market_id == "3795"
        assert len(result.outcomes) == 2

    def test_map_double_chance_market(self):
        """Test mapping Double Chance market."""
        result = map_bet9ja_market_to_betpawa(
            market_key="DC",
            param=None,
            outcomes={"1X": "1.35", "X2": "1.55", "12": "1.20"},
        )

        assert result.betpawa_market_id == "4693"
        assert len(result.outcomes) == 3


class TestOverUnderMapping:
    """Tests for Over/Under market mapping with line."""

    def test_map_over_under_market(self):
        """Test mapping Over/Under with line parameter."""
        result = map_bet9ja_market_to_betpawa(
            market_key="OU",
            param="2.5",
            outcomes={"O": "1.80", "U": "2.00"},
        )

        assert result.betpawa_market_id == "5000"
        assert result.line == 2.5
        assert len(result.outcomes) == 2

        # Check outcomes
        over = next(o for o in result.outcomes if o.betpawa_outcome_name == "Over")
        assert over.odds == 1.80

    def test_map_over_under_various_lines(self):
        """Test Over/Under with various line values."""
        for line in ["0.5", "1.5", "3.5", "4.5"]:
            result = map_bet9ja_market_to_betpawa(
                market_key="OU",
                param=line,
                outcomes={"O": "1.50", "U": "2.50"},
            )
            assert result.line == float(line)

    def test_map_over_under_missing_param_raises_error(self):
        """Test that O/U without param raises error."""
        with pytest.raises(MappingError) as exc_info:
            map_bet9ja_market_to_betpawa(
                market_key="OU",
                param=None,  # Missing required param
                outcomes={"O": "1.80", "U": "2.00"},
            )

        assert exc_info.value.code == MappingErrorCode.INVALID_SPECIFIER


class TestHandicapMapping:
    """Tests for Handicap market mapping."""

    def test_map_asian_handicap(self):
        """Test mapping Asian Handicap market."""
        result = map_bet9ja_market_to_betpawa(
            market_key="AH",
            param="-0.5",
            outcomes={"1": "1.90", "2": "1.90"},
        )

        assert result.handicap is not None
        assert result.handicap.type == "asian"
        assert result.handicap.home == -0.5
        assert result.handicap.away == 0.5

    def test_map_european_handicap(self):
        """Test mapping 3-Way Handicap (European) market."""
        result = map_bet9ja_market_to_betpawa(
            market_key="1X2HND",
            param="-1",
            outcomes={"1H": "2.50", "XH": "3.20", "2H": "2.80"},
        )

        assert result.handicap is not None
        assert result.handicap.type == "european"
        assert result.handicap.home == -1.0
        assert result.handicap.away == 1.0


class TestBatchMapping:
    """Tests for map_bet9ja_odds_to_betpawa batch function."""

    def test_batch_map_single_market(self):
        """Test batch mapping with a single market's odds."""
        odds = {
            "S_1X2_1": "1.50",
            "S_1X2_X": "3.20",
            "S_1X2_2": "2.10",
        }

        results = map_bet9ja_odds_to_betpawa(odds)

        assert len(results) == 1
        assert results[0].betpawa_market_id == "3743"
        assert len(results[0].outcomes) == 3

    def test_batch_map_multiple_markets(self):
        """Test batch mapping with multiple markets."""
        odds = {
            # 1X2
            "S_1X2_1": "1.50",
            "S_1X2_X": "3.20",
            "S_1X2_2": "2.10",
            # BTTS
            "S_GGNG_Y": "1.85",
            "S_GGNG_N": "1.95",
            # O/U 2.5
            "S_OU@2.5_O": "1.80",
            "S_OU@2.5_U": "2.00",
        }

        results = map_bet9ja_odds_to_betpawa(odds)

        # Should have 3 markets mapped
        assert len(results) == 3

        market_ids = {r.betpawa_market_id for r in results}
        assert "3743" in market_ids  # 1X2
        assert "3795" in market_ids  # BTTS
        assert "5000" in market_ids  # O/U

    def test_batch_map_skips_unknown_markets(self):
        """Test that batch mapping silently skips unknown markets."""
        odds = {
            # Known market
            "S_1X2_1": "1.50",
            "S_1X2_X": "3.20",
            "S_1X2_2": "2.10",
            # Unknown market - should be skipped
            "S_UNKNOWN_1": "2.00",
            "S_UNKNOWN_2": "3.00",
        }

        results = map_bet9ja_odds_to_betpawa(odds)

        # Only the known market should be mapped
        assert len(results) == 1
        assert results[0].betpawa_market_id == "3743"

    def test_batch_map_empty_dict(self):
        """Test batch mapping with empty dict returns empty list."""
        results = map_bet9ja_odds_to_betpawa({})
        assert results == []

    def test_batch_map_skips_invalid_keys(self):
        """Test that batch mapping skips keys that can't be parsed."""
        odds = {
            # Valid keys
            "S_1X2_1": "1.50",
            "S_1X2_X": "3.20",
            "S_1X2_2": "2.10",
            # Invalid keys - should be skipped
            "invalid_key": "2.00",
            "": "3.00",
            "1X2_1": "2.50",  # Missing S_ prefix
        }

        results = map_bet9ja_odds_to_betpawa(odds)

        assert len(results) == 1


class TestErrorCases:
    """Tests for error handling."""

    def test_unknown_market_raises_error(self):
        """Test that unknown market key raises MappingError."""
        with pytest.raises(MappingError) as exc_info:
            map_bet9ja_market_to_betpawa(
                market_key="UNKNOWN",
                param=None,
                outcomes={"1": "2.00"},
            )

        assert exc_info.value.code == MappingErrorCode.UNKNOWN_MARKET

    def test_no_matching_outcomes_raises_error(self):
        """Test that market with no matching outcomes raises error."""
        with pytest.raises(MappingError) as exc_info:
            map_bet9ja_market_to_betpawa(
                market_key="1X2",
                param=None,
                outcomes={"INVALID1": "2.00", "INVALID2": "3.00"},
            )

        assert exc_info.value.code == MappingErrorCode.NO_MATCHING_OUTCOMES

    def test_unrecognized_param_market_raises_error(self):
        """Test that unrecognized parameterized market raises error."""
        # Using a simple market key with a param should raise error
        # because it's not in the O/U or Handicap sets
        with pytest.raises(MappingError) as exc_info:
            map_bet9ja_market_to_betpawa(
                market_key="1X2",  # Simple market, doesn't support params
                param="2.5",  # But param provided
                outcomes={"1": "2.00", "X": "3.00", "2": "2.50"},
            )

        assert exc_info.value.code == MappingErrorCode.UNKNOWN_PARAM_MARKET


class TestOutcomeMapping:
    """Tests for outcome mapping specifics."""

    def test_odds_parsed_correctly(self):
        """Test that odds strings are parsed to floats."""
        result = map_bet9ja_market_to_betpawa(
            market_key="1X2",
            param=None,
            outcomes={"1": "2.15", "X": "3.20", "2": "3.50"},
        )

        for outcome in result.outcomes:
            assert isinstance(outcome.odds, float)

        home = next(o for o in result.outcomes if o.betpawa_outcome_name == "1")
        assert home.odds == 2.15

    def test_is_active_always_true(self):
        """Test that Bet9ja outcomes are always marked active (no inactive info in source)."""
        result = map_bet9ja_market_to_betpawa(
            market_key="1X2",
            param=None,
            outcomes={"1": "2.15", "X": "3.20", "2": "3.50"},
        )

        for outcome in result.outcomes:
            assert outcome.is_active is True

    def test_sportybet_desc_is_none(self):
        """Test that sportybet_outcome_desc is None for Bet9ja source."""
        result = map_bet9ja_market_to_betpawa(
            market_key="1X2",
            param=None,
            outcomes={"1": "2.15", "X": "3.20", "2": "3.50"},
        )

        for outcome in result.outcomes:
            assert outcome.sportybet_outcome_desc is None


class TestComboMarketMapping:
    """Tests for combo markets with O/U line parameter."""

    def test_1x2_over_under_combo(self):
        """Test mapping 1X2OU combo market with line parameter."""
        result = map_bet9ja_market_to_betpawa(
            market_key="1X2OU",
            param="2.5",
            outcomes={
                "1O": "3.50",
                "1U": "2.80",
                "XO": "5.00",
                "XU": "4.20",
                "2O": "4.50",
                "2U": "3.80",
            },
        )

        assert result.betpawa_market_name == "1X2 and Over/Under - Full Time"
        assert result.line == 2.5
        assert len(result.outcomes) == 6

    def test_double_chance_over_under_combo(self):
        """Test mapping DCOU combo market with line parameter."""
        result = map_bet9ja_market_to_betpawa(
            market_key="DCOU",
            param="2.5",
            outcomes={
                "1XO": "1.90",
                "1XU": "1.70",
                "X2O": "2.20",
                "X2U": "1.95",
                "12O": "1.60",
                "12U": "1.50",
            },
        )

        assert result.betpawa_market_name == "Double Chance and Over/Under - Full Time"
        assert result.line == 2.5
        assert len(result.outcomes) == 6

    def test_combo_market_various_lines(self):
        """Test combo markets with various line values."""
        for line in ["1.5", "2.5", "3.5"]:
            result = map_bet9ja_market_to_betpawa(
                market_key="1X2OU",
                param=line,
                outcomes={"1O": "2.00", "1U": "3.00"},
            )
            assert result.line == float(line)

    def test_combo_market_partial_outcomes(self):
        """Test combo market with partial outcome data maps successfully."""
        # Only some outcomes present - should still work
        result = map_bet9ja_market_to_betpawa(
            market_key="1X2OU",
            param="2.5",
            outcomes={
                "1O": "3.50",
                "1U": "2.80",
            },
        )

        assert result.line == 2.5
        assert len(result.outcomes) == 2
