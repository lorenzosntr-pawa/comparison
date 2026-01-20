"""Bet9ja to Betpawa Mapper.

Transforms Bet9ja markets into Betpawa's format, using Betpawa's
market IDs and naming conventions. This allows Betpawa to work with
competitor data using their native vocabulary.

Bet9ja uses a flattened key-value format for odds:
  {"S_1X2_1": "1.50", "S_1X2_X": "3.20", "S_1X2_2": "2.10"}

Keys are parsed to extract market type, param (for O/U, handicaps), and outcome suffix.
This mapper groups outcomes by market, then maps each market to Betpawa format.
"""

from dataclasses import dataclass

from market_mapping.mappings import find_by_bet9ja_key
from market_mapping.types.errors import MappingError, MappingErrorCode
from market_mapping.types.mapped import MappedHandicap, MappedMarket, MappedOutcome
from market_mapping.types.normalized import MarketMapping, OutcomeMapping
from market_mapping.utils import ParsedBet9jaKey, ParsedHandicap, parse_bet9ja_key


# Bet9ja Over/Under market keys
# Keys for markets that use Over/Under lines with a total parameter.
# Format: S_{KEY}@{line}_{O|U}
BET9JA_OVER_UNDER_KEYS = frozenset([
    # Full Time
    "OU",  # Over/Under - Full Time
    # First Half
    "OU1T",  # Over/Under - First Half
    # Second Half
    "OU2T",  # Over/Under - Second Half
    # Home/Away variants
    "HAOU",  # Home/Away Over/Under - Full Time
    "HA1HOU",  # Home/Away Over/Under - First Half
    "HA2HOU",  # Home/Away Over/Under - Second Half
    # Corner O/U
    "OUCORNERS",  # Total Corners Over/Under - Full Time
    "OUCORNERS1T",  # Total Corners Over/Under - First Half
    "CORNERSHOMEOU",  # Home Team Corners Over/Under - Full Time
    "CORNERSAWAYOU",  # Away Team Corners Over/Under - Full Time
    # Booking O/U
    "OUBOOK",  # Total Bookings Over/Under - Full Time
    "OUBOOK1T",  # Total Bookings Over/Under - First Half
    "OUBOOKHOME",  # Home Team Bookings Over/Under - Full Time
    "OUBOOKAWAY",  # Away Team Bookings Over/Under - Full Time
    # HT/FT Combo O/U
    "HTFTOU",  # Half Time/Full Time and Over/Under
])

# Bet9ja Handicap market keys
# Keys for markets that use handicap values.
# Asian: S_{KEY}@{value}_{1|2} - 2-way market
# European: S_{KEY}@{value}_{1H|XH|2H} - 3-way market
BET9JA_HANDICAP_KEYS = frozenset([
    # Asian Handicap
    "AH",  # Asian Handicap - Full Time
    "AH1T",  # Asian Handicap - First Half
    "AH2T",  # Asian Handicap - Second Half
    # European Handicap (3-way)
    "1X2HND",  # 3-Way Handicap - Full Time
    "1X2HNDHT",  # 3-Way Handicap - First Half (HT = Half Time)
    "1X2HND2TN",  # 3-Way Handicap - Second Half
    # Corner Handicap
    "AHCORNERS",  # Corner Asian Handicap - Full Time
    "AHCORNERS1T",  # Corner Asian Handicap - First Half
])


@dataclass
class GroupedBet9jaMarket:
    """Grouped Bet9ja market with outcomes.

    Groups all outcomes for a single market/param combination.

    Attributes:
        market_key: The market key (e.g., "S_1X2", "S_OU")
        param: Optional parameter (e.g., "2.5" for O/U line)
        outcomes: Dict of outcome_suffix -> odds_string
    """

    market_key: str
    param: str | None
    outcomes: dict[str, str]


def _group_by_market(odds: dict[str, str]) -> list[GroupedBet9jaMarket]:
    """Group Bet9ja odds by market and parameter.

    Takes a flat dict of odds like {"S_1X2_1": "1.50", "S_1X2_X": "3.20"}
    and groups them into markets with their outcomes.

    Args:
        odds: Flat dict of Bet9ja odds (key -> odds_string)

    Returns:
        List of GroupedBet9jaMarket, one per unique market/param combination.
    """
    # Group by (market_key, param) tuple
    groups: dict[tuple[str, str | None], dict[str, str]] = {}

    for key, odds_str in odds.items():
        parsed = parse_bet9ja_key(key)
        if parsed is None:
            # Skip keys that can't be parsed
            continue

        group_key = (parsed.market, parsed.param)
        if group_key not in groups:
            groups[group_key] = {}
        groups[group_key][parsed.outcome] = odds_str

    # Convert to list of GroupedBet9jaMarket
    return [
        GroupedBet9jaMarket(
            market_key=market_key,
            param=param,
            outcomes=outcomes,
        )
        for (market_key, param), outcomes in groups.items()
    ]


def _match_outcome(
    outcome_suffix: str,
    odds_str: str,
    outcome_mappings: tuple[OutcomeMapping, ...],
    source_key: str,
) -> MappedOutcome | None:
    """Match a Bet9ja outcome suffix to its mapping and create a MappedOutcome.

    Args:
        outcome_suffix: The outcome suffix from the Bet9ja key (e.g., "1", "X", "O")
        odds_str: The odds value as a string
        outcome_mappings: Outcome mappings for this market
        source_key: The full source key for traceability

    Returns:
        MappedOutcome if a mapping is found and odds are valid, None otherwise.
    """
    # Find mapping by bet9ja_suffix (exact match - Bet9ja keys are uppercase)
    mapping: OutcomeMapping | None = None
    for m in outcome_mappings:
        if m.bet9ja_suffix == outcome_suffix:
            mapping = m
            break

    # No mapping found or no Betpawa name
    if mapping is None or mapping.betpawa_name is None:
        return None

    # Parse odds
    try:
        odds = float(odds_str)
    except (ValueError, TypeError):
        return None

    return MappedOutcome(
        betpawa_outcome_name=mapping.betpawa_name,
        sportybet_outcome_desc=None,  # Bet9ja source, not Sportybet
        odds=odds,
        is_active=True,  # Bet9ja doesn't provide isActive, assume true if present
    )
