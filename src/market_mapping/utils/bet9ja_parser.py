"""Bet9ja Key Parser.

Utility for parsing Bet9ja's flattened key format:
S_{MARKET}[@{PARAM}]_{OUTCOME}
"""

import re
from dataclasses import dataclass


# Pre-compiled regex pattern for parsing Bet9ja odds keys
# Groups:
# [1] = Market type (e.g., "1X2", "OUA", "GGNG")
# [2] = Parameter value (optional, e.g., "2.5", "-1")
# [3] = Outcome suffix (e.g., "1", "O", "1H")
BET9JA_KEY_REGEX = re.compile(r"^S_([A-Z0-9_\-]+?)(?:@([^_]+))?_(.+)$")

# Maximum key length to prevent ReDoS attacks
MAX_KEY_LENGTH = 500


@dataclass(frozen=True)
class ParsedBet9jaKey:
    """Parsed Bet9ja key components.

    Attributes:
        market: Market type (e.g., "1X2", "OU", "GGNG").
        param: Parameter value if present (e.g., "2.5", "-1"), None otherwise.
        outcome: Outcome suffix (e.g., "1", "O", "1X").
        full_key: Original full key for traceability.
    """

    market: str
    param: str | None
    outcome: str
    full_key: str


def parse_bet9ja_key(key: str | None) -> ParsedBet9jaKey | None:
    """Parse a Bet9ja odds key into its components.

    Args:
        key: The full Bet9ja key (e.g., "S_1X2_1", "S_OU@2.5_O")

    Returns:
        Parsed key components or None if invalid format.

    Edge cases handled:
    - None/empty keys -> None
    - Keys that are just "S_" or "S__" -> None
    - Keys with leading/trailing whitespace -> trimmed before parsing
    - Extremely long keys (>500 chars) -> None (ReDoS prevention)

    Examples:
        >>> parse_bet9ja_key("S_1X2_1")
        ParsedBet9jaKey(market='1X2', param=None, outcome='1', full_key='S_1X2_1')

        >>> parse_bet9ja_key("S_OU@2.5_O")
        ParsedBet9jaKey(market='OU', param='2.5', outcome='O', full_key='S_OU@2.5_O')

        >>> parse_bet9ja_key("S_1X2HND@-1_1H")
        ParsedBet9jaKey(market='1X2HND', param='-1', outcome='1H', full_key='S_1X2HND@-1_1H')
    """
    # Handle None
    if key is None:
        return None

    # Trim whitespace before processing
    trimmed_key = key.strip()

    # Handle empty after trim
    if trimmed_key == "":
        return None

    # Guard against extremely long keys to prevent ReDoS
    if len(trimmed_key) > MAX_KEY_LENGTH:
        return None

    # Check prefix
    if not trimmed_key.startswith("S_"):
        return None

    # Handle edge case: key is just "S_" or "S__"
    if trimmed_key == "S_" or trimmed_key == "S__":
        return None

    # Minimum valid key is "S_X_Y" (5 chars)
    if len(trimmed_key) < 5:
        return None

    match = BET9JA_KEY_REGEX.match(trimmed_key)
    if not match:
        return None

    # Additional validation: market and outcome should not be empty
    market = match.group(1)
    outcome = match.group(3)

    if not market or market == "" or not outcome or outcome == "":
        return None

    return ParsedBet9jaKey(
        market=market,
        param=match.group(2) or None,
        outcome=outcome,
        full_key=trimmed_key,
    )
