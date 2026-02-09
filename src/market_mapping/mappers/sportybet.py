"""Sportybet to Betpawa Mapper.

Transforms Sportybet markets into Betpawa's format, using Betpawa's
market IDs and naming conventions. This allows Betpawa to work with
competitor data using their native vocabulary.

Main Entry Point:
    map_sportybet_to_betpawa: Transforms a SportybetMarket to MappedMarket.

Market Types Supported:
    - Simple markets (1X2, Double Chance, BTTS, etc.)
    - Over/Under markets with line values (parsed from specifier)
    - Handicap markets (Asian and European, parsed from specifier)
    - Variant markets (Exact Goals, Winning Margin, etc.)

Error Handling:
    Raises MappingError with specific error codes on failure.
    See MappingErrorCode for available error types.
"""

from market_mapping.mappings import (
    find_by_sportybet_id,
    is_handicap_market,
    is_over_under_market,
    is_variant_market,
)
from market_mapping.types.errors import MappingError, MappingErrorCode
from market_mapping.types.mapped import MappedHandicap, MappedMarket, MappedOutcome
from market_mapping.types.normalized import MarketMapping, OutcomeMapping
from market_mapping.types.sportybet import SportybetMarket, SportybetOutcome
from market_mapping.utils import ParsedHandicap, parse_specifier

# Market IDs that use time-based specifiers (from/to)
# These markets have specifiers like "from=1|to=10" indicating time ranges.
# The specifier just indicates the time range which is implicit in the market,
# so we treat them as simple markets.
TIME_BASED_MARKET_IDS = frozenset(["105"])  # 10 Minutes 1X2


def _map_outcome(
    outcome: SportybetOutcome,
    outcome_mappings: tuple[OutcomeMapping, ...],
    position: int,
) -> MappedOutcome | None:
    """Map a Sportybet outcome to Betpawa format.

    First tries to match by description (case-insensitive), then falls back
    to position-based matching.

    Args:
        outcome: Sportybet outcome to map.
        outcome_mappings: Outcome mappings for this market.
        position: Position of this outcome in the outcomes array (0-indexed).

    Returns:
        MappedOutcome if a mapping is found, None otherwise.

    Raises:
        MappingError: If odds value cannot be parsed.
    """
    # First try to match by Sportybet desc (case-insensitive)
    mapping: OutcomeMapping | None = None
    outcome_desc_lower = outcome.desc.lower() if outcome.desc else ""

    for m in outcome_mappings:
        if m.sportybet_desc and m.sportybet_desc.lower() == outcome_desc_lower:
            mapping = m
            break

    # Fall back to position-based matching
    if mapping is None:
        for m in outcome_mappings:
            if m.position == position:
                mapping = m
                break

    # If no mapping found or no Betpawa name, skip this outcome
    if mapping is None or mapping.betpawa_name is None:
        return None

    # Parse odds
    try:
        odds = float(outcome.odds)
    except (ValueError, TypeError) as e:
        raise MappingError(
            code=MappingErrorCode.INVALID_ODDS,
            message=f"Could not parse odds value: {outcome.odds!r}",
            context={"odds": outcome.odds, "outcome_desc": outcome.desc},
        ) from e

    return MappedOutcome(
        betpawa_outcome_name=mapping.betpawa_name,
        sportybet_outcome_desc=outcome.desc,
        odds=odds,
        is_active=outcome.is_active == 1,
    )


def _map_outcomes(
    market: SportybetMarket,
    mapping: MarketMapping,
) -> tuple[MappedOutcome, ...]:
    """Map all outcomes for a market.

    Args:
        market: Sportybet market containing outcomes.
        mapping: Market mapping with outcome mappings.

    Returns:
        Tuple of mapped outcomes.

    Raises:
        MappingError: If no outcomes could be mapped or if odds parsing fails.
    """
    mapped_outcomes: list[MappedOutcome] = []

    for index, outcome in enumerate(market.outcomes):
        mapped = _map_outcome(outcome, mapping.outcome_mapping, index)
        if mapped is not None:
            mapped_outcomes.append(mapped)

    # If all outcomes failed to map, raise error
    if not mapped_outcomes:
        raise MappingError(
            code=MappingErrorCode.NO_MATCHING_OUTCOMES,
            message=f'No outcomes could be mapped for market "{mapping.name}"',
            context={
                "market_id": market.id,
                "outcome_count": len(market.outcomes),
                "outcome_descs": [o.desc for o in market.outcomes],
            },
        )

    return tuple(mapped_outcomes)


def _map_simple_market(
    market: SportybetMarket,
    mapping: MarketMapping,
) -> MappedMarket:
    """Map a simple market (no line or handicap).

    Args:
        market: Sportybet market to map.
        mapping: Market mapping.

    Returns:
        MappedMarket with outcomes.

    Raises:
        MappingError: If mapping fails.
    """
    outcomes = _map_outcomes(market, mapping)

    return MappedMarket(
        betpawa_market_id=mapping.betpawa_id,  # type: ignore[arg-type]
        betpawa_market_name=mapping.name,
        sportybet_market_id=market.id,
        outcomes=outcomes,
    )


def _map_over_under_market(
    market: SportybetMarket,
    mapping: MarketMapping,
    line: float,
) -> MappedMarket:
    """Map an Over/Under market with a line value.

    Over/Under markets have outcomes like "Over 2.5" and "Under 2.5".
    The line value comes from the specifier (e.g., "total=2.5").

    Args:
        market: Sportybet Over/Under market.
        mapping: Market mapping.
        line: Line value extracted from specifier.

    Returns:
        MappedMarket with line value.

    Raises:
        MappingError: If mapping fails.
    """
    outcomes = _map_outcomes(market, mapping)

    return MappedMarket(
        betpawa_market_id=mapping.betpawa_id,  # type: ignore[arg-type]
        betpawa_market_name=mapping.name,
        sportybet_market_id=market.id,
        line=line,
        outcomes=outcomes,
    )


def _map_handicap_market(
    market: SportybetMarket,
    mapping: MarketMapping,
    hcp: ParsedHandicap,
) -> MappedMarket:
    """Map a Handicap market with handicap values.

    Handicap markets have outcomes like "Home (0:1)" for European or "Home (-0.5)" for Asian.
    The handicap value comes from the specifier (e.g., "hcp=0:1" or "hcp=-0.5").

    Args:
        market: Sportybet Handicap market.
        mapping: Market mapping.
        hcp: Parsed handicap data from specifier.

    Returns:
        MappedMarket with handicap values.

    Raises:
        MappingError: If mapping fails.
    """
    outcomes = _map_outcomes(market, mapping)

    handicap = MappedHandicap(
        type=hcp.type,
        home=hcp.home,
        away=hcp.away,
    )

    return MappedMarket(
        betpawa_market_id=mapping.betpawa_id,  # type: ignore[arg-type]
        betpawa_market_name=mapping.name,
        sportybet_market_id=market.id,
        handicap=handicap,
        outcomes=outcomes,
    )


def map_sportybet_to_betpawa(market: SportybetMarket) -> MappedMarket:
    """Map a Sportybet market to Betpawa format.

    Transforms a Sportybet market to use Betpawa's market IDs and naming conventions.
    Handles simple markets, Over/Under markets with lines, Handicap markets,
    and Variant markets (exact goals, winning margin).

    Args:
        market: Sportybet market to map.

    Returns:
        MappedMarket in Betpawa's format.

    Raises:
        MappingError: If market cannot be mapped. Error codes:
            - UNKNOWN_MARKET: No mapping exists for the market ID
            - UNSUPPORTED_PLATFORM: Mapping exists but betpawa_id is None
            - INVALID_SPECIFIER: Specifier present but unparseable
            - UNKNOWN_PARAM_MARKET: Unrecognized parameterized market type
            - NO_MATCHING_OUTCOMES: All outcomes failed to map
            - INVALID_ODDS: Odds value could not be parsed

    Example:
        >>> from market_mapping.types.sportybet import SportybetMarket
        >>> market = SportybetMarket(...)  # 1X2 market
        >>> mapped = map_sportybet_to_betpawa(market)
        >>> print(mapped.betpawa_market_name)
        '1X2 - FT'
    """
    # Find market mapping
    mapping = find_by_sportybet_id(market.id)

    # No mapping found for this market
    if mapping is None:
        raise MappingError(
            code=MappingErrorCode.UNKNOWN_MARKET,
            message=f"No mapping found for Sportybet market ID: {market.id}",
            context={"market_id": market.id, "market_desc": market.desc},
        )

    # Market doesn't exist on Betpawa
    if mapping.betpawa_id is None:
        raise MappingError(
            code=MappingErrorCode.UNSUPPORTED_PLATFORM,
            message=f'Market "{mapping.name}" exists but is not available on Betpawa',
            context={"market_id": market.id, "canonical_id": mapping.canonical_id},
        )

    # Parse specifier if present
    parsed_specifier = parse_specifier(market.specifier) if market.specifier else None

    # Handle parameterized markets
    if parsed_specifier is not None:
        # Handle Over/Under markets with total specifier
        if is_over_under_market(market.id) and parsed_specifier.total is not None:
            return _map_over_under_market(market, mapping, parsed_specifier.total)

        # Handle Handicap markets with hcp specifier
        if is_handicap_market(market.id) and parsed_specifier.hcp is not None:
            return _map_handicap_market(market, mapping, parsed_specifier.hcp)

        # Handle Variant markets (e.g., Exact Goals)
        # Variant specifiers indicate outcome structure but outcomes still map by desc
        if is_variant_market(market.id) and parsed_specifier.variant is not None:
            # Fall through to simple market mapping
            pass
        elif market.id in TIME_BASED_MARKET_IDS:
            # Time-based markets (e.g., 10 Minutes 1X2) have from/to specifiers
            # These just indicate time range, treat as simple markets
            pass
        else:
            # Unknown parameterized market type
            raise MappingError(
                code=MappingErrorCode.UNKNOWN_PARAM_MARKET,
                message=f"Unrecognized parameterized market type for ID: {market.id}",
                context={"market_id": market.id, "specifier": market.specifier},
            )

    # Simple market (no specifier or variant/time-based) - use standard mapping
    return _map_simple_market(market, mapping)
