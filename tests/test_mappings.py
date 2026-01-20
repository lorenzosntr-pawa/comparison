"""Tests for market mappings registry."""

import pytest

from market_mapping.mappings import (
    HANDICAP_MARKET_IDS,
    MARKET_MAPPINGS,
    OVER_UNDER_MARKET_IDS,
    VARIANT_MARKET_IDS,
    find_by_bet9ja_key,
    find_by_betpawa_id,
    find_by_canonical_id,
    find_by_sportybet_id,
    is_handicap_market,
    is_over_under_market,
    is_variant_market,
)


class TestMarketMappingsRegistry:
    """Tests for MARKET_MAPPINGS registry."""

    def test_market_mappings_not_empty(self):
        """Test that market mappings registry is populated."""
        assert len(MARKET_MAPPINGS) > 0

    def test_market_mappings_count(self):
        """Test that we have 100+ market mappings."""
        assert len(MARKET_MAPPINGS) >= 100

    def test_all_mappings_have_canonical_id(self):
        """Test that all mappings have a canonical_id."""
        for mapping in MARKET_MAPPINGS:
            assert mapping.canonical_id is not None
            assert len(mapping.canonical_id) > 0

    def test_all_mappings_have_name(self):
        """Test that all mappings have a name."""
        for mapping in MARKET_MAPPINGS:
            assert mapping.name is not None
            assert len(mapping.name) > 0


class TestFindBySportybetId:
    """Tests for find_by_sportybet_id function."""

    def test_find_1x2_market(self):
        """Test finding 1X2 Full Time market by Sportybet ID."""
        result = find_by_sportybet_id("1")
        assert result is not None
        assert result.canonical_id == "1x2_ft"
        assert result.name == "1X2 - Full Time"
        assert result.betpawa_id == "3743"

    def test_find_over_under_market(self):
        """Test finding Over/Under market by Sportybet ID."""
        result = find_by_sportybet_id("18")
        assert result is not None
        assert result.canonical_id == "over_under_ft"
        assert "Over/Under" in result.name

    def test_find_double_chance_market(self):
        """Test finding Double Chance market by Sportybet ID."""
        result = find_by_sportybet_id("10")
        assert result is not None
        assert result.canonical_id == "double_chance_ft"

    def test_find_unknown_market_returns_none(self):
        """Test that unknown Sportybet ID returns None."""
        result = find_by_sportybet_id("99999")
        assert result is None

    def test_find_with_none_returns_none(self):
        """Test that None input returns None."""
        result = find_by_sportybet_id(None)
        assert result is None


class TestFindByBetpawaId:
    """Tests for find_by_betpawa_id function."""

    def test_find_1x2_market(self):
        """Test finding 1X2 Full Time market by Betpawa ID."""
        result = find_by_betpawa_id("3743")
        assert result is not None
        assert result.canonical_id == "1x2_ft"
        assert result.sportybet_id == "1"

    def test_find_btts_market(self):
        """Test finding BTTS market by Betpawa ID."""
        result = find_by_betpawa_id("3795")
        assert result is not None
        assert result.canonical_id == "btts_ft"

    def test_find_unknown_market_returns_none(self):
        """Test that unknown Betpawa ID returns None."""
        result = find_by_betpawa_id("99999")
        assert result is None


class TestFindByBet9jaKey:
    """Tests for find_by_bet9ja_key function."""

    def test_find_1x2_market(self):
        """Test finding 1X2 Full Time market by Bet9ja key."""
        result = find_by_bet9ja_key("S_1X2")
        assert result is not None
        assert result.canonical_id == "1x2_ft"
        assert result.betpawa_id == "3743"

    def test_find_over_under_market(self):
        """Test finding Over/Under market by Bet9ja key."""
        result = find_by_bet9ja_key("S_OU")
        assert result is not None
        assert result.canonical_id == "over_under_ft"

    def test_find_btts_market(self):
        """Test finding BTTS market by Bet9ja key."""
        result = find_by_bet9ja_key("S_GGNG")
        assert result is not None
        assert result.canonical_id == "btts_ft"

    def test_find_double_chance_market(self):
        """Test finding Double Chance market by Bet9ja key."""
        result = find_by_bet9ja_key("S_DC")
        assert result is not None
        assert result.canonical_id == "double_chance_ft"

    def test_find_unknown_market_returns_none(self):
        """Test that unknown Bet9ja key returns None."""
        result = find_by_bet9ja_key("S_UNKNOWN")
        assert result is None


class TestFindByCanonicalId:
    """Tests for find_by_canonical_id function."""

    def test_find_by_canonical_id(self):
        """Test finding market by canonical ID."""
        result = find_by_canonical_id("1x2_ft")
        assert result is not None
        assert result.betpawa_id == "3743"
        assert result.sportybet_id == "1"

    def test_find_unknown_canonical_returns_none(self):
        """Test that unknown canonical ID returns None."""
        result = find_by_canonical_id("unknown_market")
        assert result is None


class TestMarketClassifications:
    """Tests for market classification sets and helpers."""

    def test_over_under_market_ids_not_empty(self):
        """Test that Over/Under market IDs set is populated."""
        assert len(OVER_UNDER_MARKET_IDS) > 0

    def test_handicap_market_ids_not_empty(self):
        """Test that Handicap market IDs set is populated."""
        assert len(HANDICAP_MARKET_IDS) > 0

    def test_variant_market_ids_not_empty(self):
        """Test that Variant market IDs set is populated."""
        assert len(VARIANT_MARKET_IDS) > 0

    def test_is_over_under_market(self):
        """Test is_over_under_market helper."""
        assert is_over_under_market("18")  # O/U FT
        assert not is_over_under_market("1")  # 1X2 FT

    def test_is_handicap_market(self):
        """Test is_handicap_market helper."""
        assert is_handicap_market("14")  # 3-Way Handicap
        assert is_handicap_market("16")  # Asian Handicap
        assert not is_handicap_market("1")  # 1X2 FT

    def test_is_variant_market(self):
        """Test is_variant_market helper."""
        # Variant markets have variant specifiers (e.g., Exact Goals, Winning Margin)
        assert is_variant_market("21")  # Exact Goals is a variant market
        assert not is_variant_market("1")  # 1X2 FT


class TestOutcomeMappings:
    """Tests for outcome mappings within market mappings."""

    def test_1x2_outcome_mappings(self):
        """Test that 1X2 has correct outcome mappings."""
        mapping = find_by_sportybet_id("1")
        assert mapping is not None
        assert len(mapping.outcome_mapping) == 3

        # Check home outcome
        home = next(o for o in mapping.outcome_mapping if o.canonical_id == "home")
        assert home.betpawa_name == "1"
        assert home.sportybet_desc == "Home"
        assert home.bet9ja_suffix == "1"

        # Check draw outcome
        draw = next(o for o in mapping.outcome_mapping if o.canonical_id == "draw")
        assert draw.betpawa_name == "X"
        assert draw.sportybet_desc == "Draw"
        assert draw.bet9ja_suffix == "X"

        # Check away outcome
        away = next(o for o in mapping.outcome_mapping if o.canonical_id == "away")
        assert away.betpawa_name == "2"
        assert away.sportybet_desc == "Away"
        assert away.bet9ja_suffix == "2"

    def test_btts_outcome_mappings(self):
        """Test that BTTS has correct outcome mappings."""
        mapping = find_by_sportybet_id("29")
        assert mapping is not None
        assert len(mapping.outcome_mapping) == 2

        # Check Yes outcome
        yes = next(o for o in mapping.outcome_mapping if o.canonical_id == "yes")
        assert yes.betpawa_name == "Yes"
        assert yes.sportybet_desc == "Yes"
        assert yes.bet9ja_suffix == "Y"

    def test_over_under_outcome_mappings(self):
        """Test that Over/Under has correct outcome mappings."""
        mapping = find_by_sportybet_id("18")
        assert mapping is not None
        assert len(mapping.outcome_mapping) == 2

        # Check Over outcome
        over = next(o for o in mapping.outcome_mapping if o.canonical_id == "over")
        assert over.betpawa_name == "Over"
        assert over.bet9ja_suffix == "O"

        # Check Under outcome
        under = next(o for o in mapping.outcome_mapping if o.canonical_id == "under")
        assert under.betpawa_name == "Under"
        assert under.bet9ja_suffix == "U"
