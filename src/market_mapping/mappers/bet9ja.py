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


def _map_simple_market(
    grouped: GroupedBet9jaMarket,
    mapping: MarketMapping,
) -> MappedMarket:
    """Map a simple Bet9ja market (no line or handicap).

    Args:
        grouped: Grouped Bet9ja market with outcomes.
        mapping: Market mapping.

    Returns:
        MappedMarket with outcomes.

    Raises:
        MappingError: If no outcomes could be mapped.
    """
    mapped_outcomes: list[MappedOutcome] = []

    for outcome_suffix, odds_str in grouped.outcomes.items():
        source_key = f"S_{grouped.market_key}_{outcome_suffix}"
        mapped = _match_outcome(outcome_suffix, odds_str, mapping.outcome_mapping, source_key)
        if mapped is not None:
            mapped_outcomes.append(mapped)

    # If all outcomes failed to map, raise error
    if not mapped_outcomes:
        raise MappingError(
            code=MappingErrorCode.NO_MATCHING_OUTCOMES,
            message=f'No outcomes could be mapped for market "{mapping.name}"',
            context={
                "market_key": grouped.market_key,
                "outcome_suffixes": list(grouped.outcomes.keys()),
            },
        )

    return MappedMarket(
        betpawa_market_id=mapping.betpawa_id,  # type: ignore[arg-type]
        betpawa_market_name=mapping.name,
        sportybet_market_id=None,  # Bet9ja source, not Sportybet
        outcomes=tuple(mapped_outcomes),
    )


def _map_over_under_market(
    grouped: GroupedBet9jaMarket,
    mapping: MarketMapping,
) -> MappedMarket:
    """Map a Bet9ja Over/Under market with a line value.

    Over/Under markets have outcomes "O" (Over) and "U" (Under).
    The line value comes from the parameter (e.g., "S_OU@2.5_O" has line=2.5).

    Args:
        grouped: Grouped Bet9ja market with outcomes and param.
        mapping: Market mapping.

    Returns:
        MappedMarket with line value.

    Raises:
        MappingError: If line cannot be parsed or no outcomes map.
    """
    # Parse line from parameter
    if grouped.param is None:
        raise MappingError(
            code=MappingErrorCode.INVALID_SPECIFIER,
            message="Over/Under market missing line parameter",
            context={"market_key": grouped.market_key},
        )

    try:
        line = float(grouped.param)
    except ValueError as e:
        raise MappingError(
            code=MappingErrorCode.INVALID_SPECIFIER,
            message=f"Could not parse line value from param: {grouped.param}",
            context={"market_key": grouped.market_key, "param": grouped.param},
        ) from e

    # Map outcomes
    mapped_outcomes: list[MappedOutcome] = []

    for outcome_suffix, odds_str in grouped.outcomes.items():
        source_key = f"S_{grouped.market_key}@{grouped.param}_{outcome_suffix}"
        mapped = _match_outcome(outcome_suffix, odds_str, mapping.outcome_mapping, source_key)
        if mapped is not None:
            mapped_outcomes.append(mapped)

    # If all outcomes failed to map, raise error
    if not mapped_outcomes:
        raise MappingError(
            code=MappingErrorCode.NO_MATCHING_OUTCOMES,
            message=f'No outcomes could be mapped for Over/Under market "{mapping.name}"',
            context={
                "market_key": grouped.market_key,
                "line": line,
                "outcome_suffixes": list(grouped.outcomes.keys()),
            },
        )

    return MappedMarket(
        betpawa_market_id=mapping.betpawa_id,  # type: ignore[arg-type]
        betpawa_market_name=mapping.name,
        sportybet_market_id=None,  # Bet9ja source, not Sportybet
        line=line,
        outcomes=tuple(mapped_outcomes),
    )


def _map_handicap_market(
    grouped: GroupedBet9jaMarket,
    mapping: MarketMapping,
) -> MappedMarket:
    """Map a Bet9ja Handicap market with handicap values.

    Handicap markets have different formats:
    - Asian (2-way): outcomes "1" and "2", param is single value (e.g., "0.5", "-0.5")
    - European (3-way): outcomes "1H", "XH", "2H", param can be integer (e.g., "-1", "2")

    Args:
        grouped: Grouped Bet9ja market with outcomes and param.
        mapping: Market mapping.

    Returns:
        MappedMarket with handicap values.

    Raises:
        MappingError: If handicap cannot be parsed or no outcomes map.
    """
    # Parse handicap from parameter
    if grouped.param is None:
        raise MappingError(
            code=MappingErrorCode.INVALID_SPECIFIER,
            message="Handicap market missing handicap parameter",
            context={"market_key": grouped.market_key},
        )

    try:
        hcp_value = float(grouped.param)
    except ValueError as e:
        raise MappingError(
            code=MappingErrorCode.INVALID_SPECIFIER,
            message=f"Could not parse handicap value from param: {grouped.param}",
            context={"market_key": grouped.market_key, "param": grouped.param},
        ) from e

    # Determine if European (3-way) or Asian (2-way) based on market key
    is_european = "1X2HND" in grouped.market_key

    hcp = ParsedHandicap(
        type="european" if is_european else "asian",
        home=hcp_value,
        away=-hcp_value,
        raw=grouped.param,
    )

    # Map outcomes
    mapped_outcomes: list[MappedOutcome] = []

    for outcome_suffix, odds_str in grouped.outcomes.items():
        source_key = f"S_{grouped.market_key}@{grouped.param}_{outcome_suffix}"
        mapped = _match_outcome(outcome_suffix, odds_str, mapping.outcome_mapping, source_key)
        if mapped is not None:
            mapped_outcomes.append(mapped)

    # If all outcomes failed to map, raise error
    if not mapped_outcomes:
        raise MappingError(
            code=MappingErrorCode.NO_MATCHING_OUTCOMES,
            message=f'No outcomes could be mapped for Handicap market "{mapping.name}"',
            context={
                "market_key": grouped.market_key,
                "handicap": hcp_value,
                "outcome_suffixes": list(grouped.outcomes.keys()),
            },
        )

    handicap = MappedHandicap(
        type=hcp.type,
        home=hcp.home,
        away=hcp.away,
    )

    return MappedMarket(
        betpawa_market_id=mapping.betpawa_id,  # type: ignore[arg-type]
        betpawa_market_name=mapping.name,
        sportybet_market_id=None,  # Bet9ja source, not Sportybet
        handicap=handicap,
        outcomes=tuple(mapped_outcomes),
    )


def _map_bet9ja_market(
    grouped: GroupedBet9jaMarket,
    mapping: MarketMapping,
) -> MappedMarket:
    """Map a single grouped Bet9ja market to Betpawa format.

    Routes to the appropriate handler based on market type.

    Args:
        grouped: Grouped Bet9ja market with outcomes.
        mapping: Market mapping.

    Returns:
        MappedMarket in Betpawa format.

    Raises:
        MappingError: If mapping fails.
    """
    # Route to Over/Under handler
    if grouped.market_key in BET9JA_OVER_UNDER_KEYS:
        return _map_over_under_market(grouped, mapping)

    # Route to Handicap handler
    if grouped.market_key in BET9JA_HANDICAP_KEYS:
        return _map_handicap_market(grouped, mapping)

    # Simple market (no param) or unknown parameterized market
    if grouped.param is not None:
        # Unknown parameterized market type
        raise MappingError(
            code=MappingErrorCode.UNKNOWN_PARAM_MARKET,
            message=f"Unrecognized parameterized market type: {grouped.market_key}",
            context={
                "market_key": grouped.market_key,
                "param": grouped.param,
            },
        )

    return _map_simple_market(grouped, mapping)


def map_bet9ja_market_to_betpawa(
    market_key: str,
    param: str | None,
    outcomes: dict[str, str],
) -> MappedMarket:
    """Map a single Bet9ja market to Betpawa format.

    Args:
        market_key: The market key (e.g., "1X2", "OU")
        param: Optional parameter (e.g., "2.5" for O/U line)
        outcomes: Dict of outcome_suffix -> odds_string

    Returns:
        MappedMarket in Betpawa format.

    Raises:
        MappingError: If market cannot be mapped. Error codes:
            - UNKNOWN_MARKET: No mapping exists for the market key
            - UNSUPPORTED_PLATFORM: Mapping exists but betpawa_id is None
            - INVALID_SPECIFIER: Specifier present but unparseable
            - UNKNOWN_PARAM_MARKET: Unrecognized parameterized market type
            - NO_MATCHING_OUTCOMES: All outcomes failed to map
    """
    # Build the lookup key (just the prefix, not the full key)
    # find_by_bet9ja_key expects "S_1X2", not "S_1X2_1"
    lookup_key = f"S_{market_key}"

    # Find market mapping
    mapping = find_by_bet9ja_key(lookup_key)

    if mapping is None:
        raise MappingError(
            code=MappingErrorCode.UNKNOWN_MARKET,
            message=f"No mapping found for Bet9ja market key: {market_key}",
            context={"market_key": market_key, "param": param},
        )

    # Market doesn't have bet9jaKey assigned
    if mapping.bet9ja_key is None:
        raise MappingError(
            code=MappingErrorCode.UNKNOWN_MARKET,
            message=f'Market "{mapping.name}" has no bet9ja_key mapping',
            context={"market_key": market_key, "canonical_id": mapping.canonical_id},
        )

    # Market doesn't exist on Betpawa
    if mapping.betpawa_id is None:
        raise MappingError(
            code=MappingErrorCode.UNSUPPORTED_PLATFORM,
            message=f'Market "{mapping.name}" exists but is not available on Betpawa',
            context={"market_key": market_key, "canonical_id": mapping.canonical_id},
        )

    # Create grouped market and delegate to internal mapper
    grouped = GroupedBet9jaMarket(
        market_key=market_key,
        param=param,
        outcomes=outcomes,
    )

    return _map_bet9ja_market(grouped, mapping)


def map_bet9ja_odds_to_betpawa(
    odds: dict[str, str],
) -> list[MappedMarket]:
    """Map all Bet9ja odds to Betpawa format.

    Takes the full Bet9ja odds dict and returns all successfully mapped markets.
    Failures are silently skipped (for batch processing use cases).

    Args:
        odds: Full Bet9ja odds dict with keys like "S_1X2_1"

    Returns:
        List of successfully mapped markets (skips unmappable markets).

    Example:
        >>> odds = {
        ...     "S_1X2_1": "1.50",
        ...     "S_1X2_X": "3.20",
        ...     "S_1X2_2": "2.10",
        ...     "S_OU@2.5_O": "1.80",
        ...     "S_OU@2.5_U": "2.00",
        ... }
        >>> mapped = map_bet9ja_odds_to_betpawa(odds)
        >>> len(mapped)  # 2 markets: 1X2 and O/U 2.5
        2
    """
    # Group by market
    grouped_markets = _group_by_market(odds)

    # Map each grouped market
    results: list[MappedMarket] = []

    for grouped in grouped_markets:
        # Build the lookup key (just the prefix)
        # find_by_bet9ja_key expects "S_1X2", not "S_1X2_1"
        lookup_key = f"S_{grouped.market_key}"

        # Find market mapping
        mapping = find_by_bet9ja_key(lookup_key)

        # Skip if no mapping, no bet9ja_key, or no betpawa_id
        if mapping is None:
            continue
        if mapping.bet9ja_key is None:
            continue
        if mapping.betpawa_id is None:
            continue

        # Try to map, skip on failure
        try:
            mapped = _map_bet9ja_market(grouped, mapping)
            results.append(mapped)
        except MappingError:
            # Skip failed mappings in batch mode
            continue

    return results
