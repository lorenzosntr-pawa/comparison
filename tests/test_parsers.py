"""Tests for parser utilities."""

import pytest

from market_mapping.utils import (
    ParsedBet9jaKey,
    ParsedHandicap,
    ParsedSpecifier,
    parse_bet9ja_key,
    parse_specifier,
)


class TestParseSpecifier:
    """Tests for parse_specifier function."""

    def test_parse_total_specifier(self):
        """Test parsing total/line specifier for Over/Under markets."""
        result = parse_specifier("total=2.5")
        assert result is not None
        assert result.total == 2.5
        assert result.hcp is None
        assert result.raw == "total=2.5"

    def test_parse_compound_specifier(self):
        """Test parsing compound specifier with multiple parts."""
        result = parse_specifier("minsnr=10|total=1.5")
        assert result is not None
        assert result.total == 1.5
        assert result.raw == "minsnr=10|total=1.5"

    def test_parse_european_handicap(self):
        """Test parsing European handicap (X:Y format)."""
        result = parse_specifier("hcp=0:1")
        assert result is not None
        assert result.hcp is not None
        assert result.hcp.type == "european"
        assert result.hcp.home == -1.0  # 0 - 1 = -1
        assert result.hcp.away == 1.0   # 1 - 0 = +1

    def test_parse_asian_handicap(self):
        """Test parsing Asian handicap (single value format)."""
        result = parse_specifier("hcp=-0.5")
        assert result is not None
        assert result.hcp is not None
        assert result.hcp.type == "asian"
        assert result.hcp.home == -0.5
        assert result.hcp.away == 0.5

    def test_parse_variant_specifier(self):
        """Test parsing variant specifier."""
        result = parse_specifier("variant=sr:exact_goals:2+")
        assert result is not None
        assert result.variant == "sr:exact_goals:2+"

    def test_parse_goalnr_specifier(self):
        """Test parsing goal number specifier."""
        result = parse_specifier("goalnr=1")
        assert result is not None
        assert result.goalnr == 1

    def test_parse_empty_specifier(self):
        """Test that empty specifier returns None."""
        assert parse_specifier("") is None
        assert parse_specifier(None) is None
        assert parse_specifier("   ") is None

    def test_parse_invalid_total_ignored(self):
        """Test that invalid total value is ignored."""
        result = parse_specifier("total=abc")
        assert result is not None
        assert result.total is None

    def test_parse_missing_value_skipped(self):
        """Test that key=value pairs with missing value are skipped."""
        result = parse_specifier("total=|hcp=-0.5")
        assert result is not None
        assert result.total is None  # Skipped because empty
        assert result.hcp is not None  # Still parsed

    def test_parse_very_long_specifier_rejected(self):
        """Test that extremely long specifiers are rejected (ReDoS prevention)."""
        long_spec = "a" * 2000
        assert parse_specifier(long_spec) is None


class TestParseBet9jaKey:
    """Tests for parse_bet9ja_key function."""

    def test_parse_simple_key(self):
        """Test parsing simple 1X2 key."""
        result = parse_bet9ja_key("S_1X2_1")
        assert result is not None
        assert result.market == "1X2"
        assert result.param is None
        assert result.outcome == "1"
        assert result.full_key == "S_1X2_1"

    def test_parse_over_under_key(self):
        """Test parsing Over/Under key with parameter."""
        result = parse_bet9ja_key("S_OU@2.5_O")
        assert result is not None
        assert result.market == "OU"
        assert result.param == "2.5"
        assert result.outcome == "O"

    def test_parse_handicap_key(self):
        """Test parsing handicap key."""
        result = parse_bet9ja_key("S_1X2HND@-1_1H")
        assert result is not None
        assert result.market == "1X2HND"
        assert result.param == "-1"
        assert result.outcome == "1H"

    def test_parse_draw_outcome(self):
        """Test parsing key with X (draw) outcome."""
        result = parse_bet9ja_key("S_1X2_X")
        assert result is not None
        assert result.outcome == "X"

    def test_parse_btts_key(self):
        """Test parsing BTTS (GG/NG) key."""
        result = parse_bet9ja_key("S_GGNG_Y")
        assert result is not None
        assert result.market == "GGNG"
        assert result.outcome == "Y"

    def test_parse_empty_key(self):
        """Test that empty key returns None."""
        assert parse_bet9ja_key("") is None
        assert parse_bet9ja_key(None) is None
        assert parse_bet9ja_key("   ") is None

    def test_parse_invalid_prefix(self):
        """Test that key without S_ prefix returns None."""
        assert parse_bet9ja_key("1X2_1") is None
        assert parse_bet9ja_key("X_1X2_1") is None

    def test_parse_malformed_key(self):
        """Test that malformed keys return None."""
        assert parse_bet9ja_key("S_") is None
        assert parse_bet9ja_key("S__") is None
        assert parse_bet9ja_key("S_1X2") is None  # Missing outcome

    def test_parse_very_long_key_rejected(self):
        """Test that extremely long keys are rejected (ReDoS prevention)."""
        long_key = "S_" + "A" * 600 + "_1"
        assert parse_bet9ja_key(long_key) is None

    def test_parse_whitespace_trimmed(self):
        """Test that whitespace is trimmed before parsing."""
        result = parse_bet9ja_key("  S_1X2_1  ")
        assert result is not None
        assert result.market == "1X2"


class TestParsedHandicap:
    """Tests for ParsedHandicap dataclass."""

    def test_european_handicap_values(self):
        """Test European handicap calculation."""
        # 0:1 means away starts with +1 goal
        result = parse_specifier("hcp=0:1")
        assert result is not None
        assert result.hcp is not None
        assert result.hcp.home == -1.0
        assert result.hcp.away == 1.0

        # 2:0 means home starts with +2 goals
        result = parse_specifier("hcp=2:0")
        assert result is not None
        assert result.hcp is not None
        assert result.hcp.home == 2.0
        assert result.hcp.away == -2.0

    def test_asian_handicap_values(self):
        """Test Asian handicap calculation."""
        # -0.5 means home has -0.5 handicap
        result = parse_specifier("hcp=-0.5")
        assert result is not None
        assert result.hcp is not None
        assert result.hcp.home == -0.5
        assert result.hcp.away == 0.5

        # +1.5 means home has +1.5 handicap
        result = parse_specifier("hcp=1.5")
        assert result is not None
        assert result.hcp is not None
        assert result.hcp.home == 1.5
        assert result.hcp.away == -1.5

    def test_handicap_invalid_format(self):
        """Test that invalid handicap formats are rejected."""
        # Invalid European (extra colon)
        result = parse_specifier("hcp=0:1:2")
        assert result is not None
        assert result.hcp is None

        # Empty handicap
        result = parse_specifier("hcp=")
        assert result is not None
        assert result.hcp is None

        # Non-numeric
        result = parse_specifier("hcp=abc")
        assert result is not None
        assert result.hcp is None
