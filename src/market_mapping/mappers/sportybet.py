"""Sportybet to Betpawa Mapper.

Transforms Sportybet markets into Betpawa's format, using Betpawa's
market IDs and naming conventions. This allows Betpawa to work with
competitor data using their native vocabulary.
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
