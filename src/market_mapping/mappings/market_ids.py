"""Market ID Mapping Table.

Static lookup table mapping between Betpawa, Sportybet, and Bet9ja market IDs.
Based on analysis from .planning/phases/01-market-structure-analysis/field-mappings.md
and market-inventory.md.
"""

from ..types.normalized import MarketMapping, OutcomeMapping

# Core football market mappings
#
# These mappings cover the essential markets that exist on all/multiple platforms.
# Each mapping includes:
# - canonical_id: Internal identifier for the market
# - name: Human-readable name
# - betpawa_id: Betpawa's marketType.id
# - sportybet_id: Sportybet's market.id
# - bet9ja_key: Bet9ja's market key prefix
# - outcome_mapping: How outcomes map between platforms

MARKET_MAPPINGS: tuple[MarketMapping, ...] = (
    # === Full Time Markets ===

    MarketMapping(
        canonical_id="1x2_ft",
        name="1X2 - Full Time",
        betpawa_id="3743",
        sportybet_id="1",
        bet9ja_key="S_1X2",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="draw", betpawa_name="X", sportybet_desc="Draw", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="double_chance_ft",
        name="Double Chance - Full Time",
        betpawa_id="4693",
        sportybet_id="10",
        bet9ja_key="S_DC",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home_draw", betpawa_name="1X", sportybet_desc="Home or Draw", bet9ja_suffix="1X", position=0),
            OutcomeMapping(canonical_id="draw_away", betpawa_name="X2", sportybet_desc="Draw or Away", bet9ja_suffix="X2", position=1),
            OutcomeMapping(canonical_id="home_away", betpawa_name="12", sportybet_desc="Home or Away", bet9ja_suffix="12", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="btts_ft",
        name="Both Teams To Score - Full Time",
        betpawa_id="3795",
        sportybet_id="29",
        bet9ja_key="S_GGNG",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="over_under_ft",
        name="Over/Under - Full Time",
        betpawa_id="5000",
        sportybet_id="18",
        bet9ja_key="S_OU",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="O", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="U", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="htft",
        name="Half Time/Full Time",
        betpawa_id="4706",
        sportybet_id="47",
        bet9ja_key="S_HTFT",
        outcome_mapping=(
            OutcomeMapping(canonical_id="1_1", betpawa_name="1/1", sportybet_desc="Home/Home", bet9ja_suffix="1/1", position=0),
            OutcomeMapping(canonical_id="1_x", betpawa_name="1/X", sportybet_desc="Home/Draw", bet9ja_suffix="1/X", position=1),
            OutcomeMapping(canonical_id="1_2", betpawa_name="1/2", sportybet_desc="Home/Away", bet9ja_suffix="1/2", position=2),
            OutcomeMapping(canonical_id="x_1", betpawa_name="X/1", sportybet_desc="Draw/Home", bet9ja_suffix="X/1", position=3),
            OutcomeMapping(canonical_id="x_x", betpawa_name="X/X", sportybet_desc="Draw/Draw", bet9ja_suffix="X/X", position=4),
            OutcomeMapping(canonical_id="x_2", betpawa_name="X/2", sportybet_desc="Draw/Away", bet9ja_suffix="X/2", position=5),
            OutcomeMapping(canonical_id="2_1", betpawa_name="2/1", sportybet_desc="Away/Home", bet9ja_suffix="2/1", position=6),
            OutcomeMapping(canonical_id="2_x", betpawa_name="2/X", sportybet_desc="Away/Draw", bet9ja_suffix="2/X", position=7),
            OutcomeMapping(canonical_id="2_2", betpawa_name="2/2", sportybet_desc="Away/Away", bet9ja_suffix="2/2", position=8),
        ),
    ),

    MarketMapping(
        canonical_id="handicap_3way_ft",
        name="3-Way Handicap - Full Time",
        betpawa_id="4724",
        sportybet_id="14",
        bet9ja_key="S_1X2HND",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1H", position=0),
            OutcomeMapping(canonical_id="draw", betpawa_name="X", sportybet_desc="Draw", bet9ja_suffix="XH", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2H", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="asian_handicap_ft",
        name="Asian Handicap - Full Time",
        betpawa_id="3774",
        sportybet_id="16",
        bet9ja_key="S_AH",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="draw_no_bet_ft",
        name="Draw No Bet - Full Time",
        betpawa_id="4703",
        sportybet_id="11",
        bet9ja_key="S_DNB",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="correct_score_ft",
        name="Correct Score - Full Time",
        betpawa_id="4429",
        sportybet_id="45",
        bet9ja_key="S_CSFT",
        outcome_mapping=(
            # Complete correct score outcomes - all scores available on platforms
            # Row 0: 0-X scores
            OutcomeMapping(canonical_id="0_0", betpawa_name="0-0", sportybet_desc="0:0", bet9ja_suffix="0:0", position=0),
            OutcomeMapping(canonical_id="0_1", betpawa_name="0-1", sportybet_desc="0:1", bet9ja_suffix="0:1", position=1),
            OutcomeMapping(canonical_id="0_2", betpawa_name="0-2", sportybet_desc="0:2", bet9ja_suffix="0:2", position=2),
            OutcomeMapping(canonical_id="0_3", betpawa_name="0-3", sportybet_desc="0:3", bet9ja_suffix="0:3", position=3),
            OutcomeMapping(canonical_id="0_4", betpawa_name="0-4", sportybet_desc="0:4", bet9ja_suffix="0:4", position=4),
            OutcomeMapping(canonical_id="0_5", betpawa_name="0-5", sportybet_desc=None, bet9ja_suffix=None, position=5),
            OutcomeMapping(canonical_id="0_6", betpawa_name="0-6", sportybet_desc=None, bet9ja_suffix=None, position=6),
            # Row 1: 1-X scores
            OutcomeMapping(canonical_id="1_0", betpawa_name="1-0", sportybet_desc="1:0", bet9ja_suffix="1:0", position=7),
            OutcomeMapping(canonical_id="1_1", betpawa_name="1-1", sportybet_desc="1:1", bet9ja_suffix="1:1", position=8),
            OutcomeMapping(canonical_id="1_2", betpawa_name="1-2", sportybet_desc="1:2", bet9ja_suffix="1:2", position=9),
            OutcomeMapping(canonical_id="1_3", betpawa_name="1-3", sportybet_desc="1:3", bet9ja_suffix="1:3", position=10),
            OutcomeMapping(canonical_id="1_4", betpawa_name="1-4", sportybet_desc="1:4", bet9ja_suffix="1:4", position=11),
            OutcomeMapping(canonical_id="1_5", betpawa_name="1-5", sportybet_desc=None, bet9ja_suffix=None, position=12),
            # Row 2: 2-X scores
            OutcomeMapping(canonical_id="2_0", betpawa_name="2-0", sportybet_desc="2:0", bet9ja_suffix="2:0", position=13),
            OutcomeMapping(canonical_id="2_1", betpawa_name="2-1", sportybet_desc="2:1", bet9ja_suffix="2:1", position=14),
            OutcomeMapping(canonical_id="2_2", betpawa_name="2-2", sportybet_desc="2:2", bet9ja_suffix="2:2", position=15),
            OutcomeMapping(canonical_id="2_3", betpawa_name="2-3", sportybet_desc="2:3", bet9ja_suffix="2:3", position=16),
            OutcomeMapping(canonical_id="2_4", betpawa_name="2-4", sportybet_desc="2:4", bet9ja_suffix="2:4", position=17),
            # Row 3: 3-X scores
            OutcomeMapping(canonical_id="3_0", betpawa_name="3-0", sportybet_desc="3:0", bet9ja_suffix="3:0", position=18),
            OutcomeMapping(canonical_id="3_1", betpawa_name="3-1", sportybet_desc="3:1", bet9ja_suffix="3:1", position=19),
            OutcomeMapping(canonical_id="3_2", betpawa_name="3-2", sportybet_desc="3:2", bet9ja_suffix="3:2", position=20),
            OutcomeMapping(canonical_id="3_3", betpawa_name="3-3", sportybet_desc="3:3", bet9ja_suffix="3:3", position=21),
            OutcomeMapping(canonical_id="3_4", betpawa_name=None, sportybet_desc="3:4", bet9ja_suffix="3:4", position=22),
            # Row 4: 4-X scores
            OutcomeMapping(canonical_id="4_0", betpawa_name="4-0", sportybet_desc="4:0", bet9ja_suffix="4:0", position=23),
            OutcomeMapping(canonical_id="4_1", betpawa_name="4-1", sportybet_desc="4:1", bet9ja_suffix="4:1", position=24),
            OutcomeMapping(canonical_id="4_2", betpawa_name="4-2", sportybet_desc="4:2", bet9ja_suffix="4:2", position=25),
            OutcomeMapping(canonical_id="4_3", betpawa_name=None, sportybet_desc="4:3", bet9ja_suffix="4:3", position=26),
            OutcomeMapping(canonical_id="4_4", betpawa_name=None, sportybet_desc="4:4", bet9ja_suffix="4:4", position=27),
            # Row 5-6: High home scores (Betpawa only)
            OutcomeMapping(canonical_id="5_0", betpawa_name="5-0", sportybet_desc=None, bet9ja_suffix=None, position=28),
            OutcomeMapping(canonical_id="5_1", betpawa_name="5-1", sportybet_desc=None, bet9ja_suffix=None, position=29),
            OutcomeMapping(canonical_id="6_0", betpawa_name="6-0", sportybet_desc=None, bet9ja_suffix=None, position=30),
            # Other outcome
            OutcomeMapping(canonical_id="other", betpawa_name="Other", sportybet_desc="Other", bet9ja_suffix="OTH", position=31),
        ),
    ),

    MarketMapping(
        canonical_id="odd_even_ft",
        name="Odd/Even - Full Time",
        betpawa_id="4833",
        sportybet_id="26",
        bet9ja_key="S_OE",
        outcome_mapping=(
            OutcomeMapping(canonical_id="odd", betpawa_name="Odd", sportybet_desc="Odd", bet9ja_suffix="OD", position=0),
            OutcomeMapping(canonical_id="even", betpawa_name="Even", sportybet_desc="Even", bet9ja_suffix="EV", position=1),
        ),
    ),

    # === First Half Markets ===

    MarketMapping(
        canonical_id="1x2_1h",
        name="1X2 - First Half",
        betpawa_id="3668",
        sportybet_id="60",
        bet9ja_key="S_1X21T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="draw", betpawa_name="X", sportybet_desc="Draw", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="over_under_1h",
        name="Over/Under - First Half",
        betpawa_id="4958",
        sportybet_id="68",
        bet9ja_key="S_OU1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="O", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="U", position=1),
        ),
    ),

    # === Second Half Markets ===

    MarketMapping(
        canonical_id="1x2_2h",
        name="1X2 - Second Half",
        betpawa_id="3685",
        sportybet_id="83",
        bet9ja_key="S_1X22T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="draw", betpawa_name="X", sportybet_desc="Draw", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    # === Time-Based Markets ===

    MarketMapping(
        canonical_id="1x2_10min",
        name="1X2 - First 10 Minutes",
        betpawa_id="28000173",
        sportybet_id="105",
        bet9ja_key="S_1X21ST10MIN",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="draw", betpawa_name="X", sportybet_desc="Draw", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="over_under_2h",
        name="Over/Under - Second Half",
        betpawa_id="4976",
        sportybet_id="90",
        bet9ja_key="S_OU2T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="O", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="U", position=1),
        ),
    ),

    # === Team-Specific Markets ===

    MarketMapping(
        canonical_id="home_over_under_ft",
        name="Home Team Over/Under - Full Time",
        betpawa_id="5006",
        sportybet_id="19",
        bet9ja_key="S_HAOU",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="OH", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="UH", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_over_under_ft",
        name="Away Team Over/Under - Full Time",
        betpawa_id="5003",
        sportybet_id="20",
        bet9ja_key="S_HAOU",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="OA", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="UA", position=1),
        ),
    ),

    # === Additional Common Markets ===

    MarketMapping(
        canonical_id="double_chance_1h",
        name="Double Chance - First Half",
        betpawa_id="4673",
        sportybet_id="63",
        bet9ja_key="S_DC1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home_draw", betpawa_name="1X", sportybet_desc="Home or Draw", bet9ja_suffix="1X", position=0),
            OutcomeMapping(canonical_id="draw_away", betpawa_name="X2", sportybet_desc="Draw or Away", bet9ja_suffix="X2", position=1),
            OutcomeMapping(canonical_id="home_away", betpawa_name="12", sportybet_desc="Home or Away", bet9ja_suffix="12", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="btts_1h",
        name="Both Teams To Score - First Half",
        betpawa_id="3789",
        sportybet_id="75",
        bet9ja_key="S_GGNG1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="draw_no_bet_1h",
        name="Draw No Bet - First Half",
        betpawa_id="4697",
        sportybet_id="64",
        bet9ja_key="S_DNB1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="draw_no_bet_2h",
        name="Draw No Bet - Second Half",
        betpawa_id="4700",
        sportybet_id="86",
        bet9ja_key="S_DNB2T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="correct_score_1h",
        name="Correct Score - First Half",
        betpawa_id="3819",
        sportybet_id="81",
        bet9ja_key="S_CS1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="0_0", betpawa_name="0-0", sportybet_desc="0:0", bet9ja_suffix="0:0", position=0),
            OutcomeMapping(canonical_id="1_0", betpawa_name="1-0", sportybet_desc="1:0", bet9ja_suffix="1:0", position=1),
            OutcomeMapping(canonical_id="0_1", betpawa_name="0-1", sportybet_desc="0:1", bet9ja_suffix="0:1", position=2),
            OutcomeMapping(canonical_id="1_1", betpawa_name="1-1", sportybet_desc="1:1", bet9ja_suffix="1:1", position=3),
        ),
    ),

    MarketMapping(
        canonical_id="home_win_to_nil_ft",
        name="Home Team Win To Nil - Full Time",
        betpawa_id="5051",
        sportybet_id="33",
        bet9ja_key="S_HOMEWINNIL",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_win_to_nil_ft",
        name="Away Team Win To Nil - Full Time",
        betpawa_id="5042",
        sportybet_id="34",
        bet9ja_key="S_AWAYWINNIL",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="home_clean_sheet_ft",
        name="Home Team Clean Sheet - Full Time",
        betpawa_id="3816",
        sportybet_id="31",
        bet9ja_key="S_CLEANSH",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_clean_sheet_ft",
        name="Away Team Clean Sheet - Full Time",
        betpawa_id="3807",
        sportybet_id="32",
        bet9ja_key="S_CLEANSA",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    # === Additional First Half Markets ===

    MarketMapping(
        canonical_id="asian_handicap_1h",
        name="Asian Handicap - First Half",
        betpawa_id="3747",
        sportybet_id="66",
        bet9ja_key="S_AH1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="handicap_3way_1h",
        name="3-Way Handicap - First Half",
        betpawa_id="4716",
        sportybet_id="65",
        bet9ja_key="S_1X2HNDHT",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="draw", betpawa_name="X", sportybet_desc="Draw", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="odd_even_1h",
        name="Odd/Even - First Half",
        betpawa_id="4794",
        sportybet_id="74",
        bet9ja_key="S_OE1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="odd", betpawa_name="Odd", sportybet_desc="Odd", bet9ja_suffix="OD", position=0),
            OutcomeMapping(canonical_id="even", betpawa_name="Even", sportybet_desc="Even", bet9ja_suffix="EV", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="home_clean_sheet_1h",
        name="Home Team Clean Sheet - First Half",
        betpawa_id="3810",
        sportybet_id="76",
        bet9ja_key=None,
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_clean_sheet_1h",
        name="Away Team Clean Sheet - First Half",
        betpawa_id="3801",
        sportybet_id="77",
        bet9ja_key=None,
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="home_over_under_1h",
        name="Home Team Over/Under - First Half",
        betpawa_id="4964",
        sportybet_id="69",
        bet9ja_key="S_HA1HOU",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="HO", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="HU", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_over_under_1h",
        name="Away Team Over/Under - First Half",
        betpawa_id="4961",
        sportybet_id="70",
        bet9ja_key="S_HA1HOU",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="AO", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="AU", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="exact_goals_1h",
        name="Exact Goals - First Half",
        betpawa_id="4898",
        sportybet_id="71",
        bet9ja_key="S_GOALS1T",
        outcome_mapping=(
            # Note: Betpawa has 0, 1, 2+ while Sportybet/Bet9ja have 0, 1, 2, 3+
            # Betpawa's 2+ doesn't directly match others - different market structures
            OutcomeMapping(canonical_id="0", betpawa_name="0", sportybet_desc="0", bet9ja_suffix="0", position=0),
            OutcomeMapping(canonical_id="1", betpawa_name="1", sportybet_desc="1", bet9ja_suffix="1", position=1),
            OutcomeMapping(canonical_id="2+", betpawa_name="2+", sportybet_desc=None, bet9ja_suffix=None, position=2),
            OutcomeMapping(canonical_id="2", betpawa_name=None, sportybet_desc="2", bet9ja_suffix="2", position=2),
            OutcomeMapping(canonical_id="3+", betpawa_name=None, sportybet_desc="3+", bet9ja_suffix="3", position=3),
        ),
    ),

    # === Additional Second Half Markets ===

    MarketMapping(
        canonical_id="asian_handicap_2h",
        name="Asian Handicap - Second Half",
        betpawa_id="3756",
        sportybet_id="88",
        bet9ja_key="S_AH2T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="handicap_3way_2h",
        name="3-Way Handicap - Second Half",
        betpawa_id="4720",
        sportybet_id="87",
        bet9ja_key="S_1X2HND2TN",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="draw", betpawa_name="X", sportybet_desc="Draw", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="btts_2h",
        name="Both Teams To Score - Second Half",
        betpawa_id="3792",
        sportybet_id="95",
        bet9ja_key="S_GGNG2T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="double_chance_2h",
        name="Double Chance - Second Half",
        betpawa_id="4681",
        sportybet_id="85",
        bet9ja_key="S_DC2T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home_draw", betpawa_name="1X", sportybet_desc="Home or Draw", bet9ja_suffix="1X", position=0),
            OutcomeMapping(canonical_id="draw_away", betpawa_name="X2", sportybet_desc="Draw or Away", bet9ja_suffix="X2", position=1),
            OutcomeMapping(canonical_id="home_away", betpawa_name="12", sportybet_desc="Home or Away", bet9ja_suffix="12", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="odd_even_2h",
        name="Odd/Even - Second Half",
        betpawa_id="4809",
        sportybet_id="94",
        bet9ja_key="S_OE2T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="odd", betpawa_name="Odd", sportybet_desc="Odd", bet9ja_suffix="OD", position=0),
            OutcomeMapping(canonical_id="even", betpawa_name="Even", sportybet_desc="Even", bet9ja_suffix="EV", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="correct_score_2h",
        name="Correct Score - Second Half",
        betpawa_id="4063",
        sportybet_id="98",
        bet9ja_key="S_CS2T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="0_0", betpawa_name="0-0", sportybet_desc="0:0", bet9ja_suffix="0:0", position=0),
            OutcomeMapping(canonical_id="1_0", betpawa_name="1-0", sportybet_desc="1:0", bet9ja_suffix="1:0", position=1),
            OutcomeMapping(canonical_id="0_1", betpawa_name="0-1", sportybet_desc="0:1", bet9ja_suffix="0:1", position=2),
            OutcomeMapping(canonical_id="1_1", betpawa_name="1-1", sportybet_desc="1:1", bet9ja_suffix="1:1", position=3),
        ),
    ),

    MarketMapping(
        canonical_id="home_clean_sheet_2h",
        name="Home Team Clean Sheet - Second Half",
        betpawa_id="3813",
        sportybet_id="96",
        bet9ja_key=None,
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_clean_sheet_2h",
        name="Away Team Clean Sheet - Second Half",
        betpawa_id="3804",
        sportybet_id="97",
        bet9ja_key=None,
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="home_over_under_2h",
        name="Home Team Over/Under - Second Half",
        betpawa_id="4982",
        sportybet_id="91",
        bet9ja_key="S_HA2HOU",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="HO", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="HU", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_over_under_2h",
        name="Away Team Over/Under - Second Half",
        betpawa_id="4979",
        sportybet_id="92",
        bet9ja_key="S_HA2HOU",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="AO", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="AU", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="exact_goals_2h",
        name="Exact Goals - Second Half",
        betpawa_id="4912",
        sportybet_id="93",
        bet9ja_key="S_GOALS2T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="0", betpawa_name="0", sportybet_desc="0", bet9ja_suffix="0", position=0),
            OutcomeMapping(canonical_id="1", betpawa_name="1", sportybet_desc="1", bet9ja_suffix="1", position=1),
            OutcomeMapping(canonical_id="2+", betpawa_name="2+", sportybet_desc="2+", bet9ja_suffix="2", position=2),
        ),
    ),

    # === Team Odd/Even Markets ===

    MarketMapping(
        canonical_id="home_odd_even_ft",
        name="Home Team Odd/Even - Full Time",
        betpawa_id="4842",
        sportybet_id="27",
        bet9ja_key="S_OEHOME",
        outcome_mapping=(
            OutcomeMapping(canonical_id="odd", betpawa_name="Odd", sportybet_desc="Odd", bet9ja_suffix="OD", position=0),
            OutcomeMapping(canonical_id="even", betpawa_name="Even", sportybet_desc="Even", bet9ja_suffix="EV", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_odd_even_ft",
        name="Away Team Odd/Even - Full Time",
        betpawa_id="4836",
        sportybet_id="28",
        bet9ja_key="S_OEAWAY",
        outcome_mapping=(
            OutcomeMapping(canonical_id="odd", betpawa_name="Odd", sportybet_desc="Odd", bet9ja_suffix="OD", position=0),
            OutcomeMapping(canonical_id="even", betpawa_name="Even", sportybet_desc="Even", bet9ja_suffix="EV", position=1),
        ),
    ),

    # === Half-Based Markets ===

    MarketMapping(
        canonical_id="highest_scoring_half",
        name="Highest Scoring Half",
        betpawa_id="4728",
        sportybet_id="52",
        bet9ja_key="S_HIGHHALF",
        outcome_mapping=(
            OutcomeMapping(canonical_id="1st", betpawa_name="First Half", sportybet_desc="1st Half", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="equal", betpawa_name="Equal", sportybet_desc="Equal", bet9ja_suffix="E", position=1),
            OutcomeMapping(canonical_id="2nd", betpawa_name="Second Half", sportybet_desc="2nd Half", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="home_highest_scoring_half",
        name="Home Team Highest Scoring Half",
        betpawa_id="4736",
        sportybet_id="53",
        bet9ja_key="S_HOMEHIGHHALF",
        outcome_mapping=(
            OutcomeMapping(canonical_id="1st", betpawa_name="First Half", sportybet_desc="1st Half", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="equal", betpawa_name="Equal", sportybet_desc="Equal", bet9ja_suffix="E", position=1),
            OutcomeMapping(canonical_id="2nd", betpawa_name="Second Half", sportybet_desc="2nd Half", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="away_highest_scoring_half",
        name="Away Team Highest Scoring Half",
        betpawa_id="4732",
        sportybet_id="54",
        bet9ja_key="S_AWAYHIGHHALF",
        outcome_mapping=(
            OutcomeMapping(canonical_id="1st", betpawa_name="First Half", sportybet_desc="1st Half", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="equal", betpawa_name="Equal", sportybet_desc="Equal", bet9ja_suffix="E", position=1),
            OutcomeMapping(canonical_id="2nd", betpawa_name="Second Half", sportybet_desc="2nd Half", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="home_win_both_halves",
        name="Home Team Win Both Halves",
        betpawa_id="1096805",
        sportybet_id="48",
        bet9ja_key="S_HOMEWINBOTH",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_win_both_halves",
        name="Away Team Win Both Halves",
        betpawa_id="1096808",
        sportybet_id="49",
        bet9ja_key="S_AWAYWINBOTH",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="home_win_either_half",
        name="Home Team Win Either Half",
        betpawa_id="1096806",
        sportybet_id="50",
        bet9ja_key="S_HOMEWINHALF",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_win_either_half",
        name="Away Team Win Either Half",
        betpawa_id="1096809",
        sportybet_id="51",
        bet9ja_key="S_AWAYWINHALF",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="home_score_both_halves",
        name="Home Team Score In Both Halves",
        betpawa_id="1096807",
        sportybet_id="56",
        bet9ja_key="S_HOMESCOREBOTH",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_score_both_halves",
        name="Away Team Score In Both Halves",
        betpawa_id="1096814",
        sportybet_id="57",
        bet9ja_key="S_AWAYSCOREBOTH",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    # === Exact Goals Markets ===

    MarketMapping(
        canonical_id="exact_goals_ft",
        name="Exact Goals - Full Time",
        betpawa_id="4926",
        sportybet_id="21",
        bet9ja_key="S_GOALS",
        outcome_mapping=(
            OutcomeMapping(canonical_id="0", betpawa_name="0", sportybet_desc="0", bet9ja_suffix="0", position=0),
            OutcomeMapping(canonical_id="1", betpawa_name="1", sportybet_desc="1", bet9ja_suffix="1", position=1),
            OutcomeMapping(canonical_id="2", betpawa_name="2", sportybet_desc="2", bet9ja_suffix="2", position=2),
            OutcomeMapping(canonical_id="3", betpawa_name="3", sportybet_desc="3", bet9ja_suffix="3", position=3),
            OutcomeMapping(canonical_id="4", betpawa_name="4", sportybet_desc="4", bet9ja_suffix="4", position=4),
            OutcomeMapping(canonical_id="5", betpawa_name="5", sportybet_desc="5", bet9ja_suffix="5", position=5),
            OutcomeMapping(canonical_id="6+", betpawa_name="6+", sportybet_desc="6+", bet9ja_suffix="6", position=6),
        ),
    ),

    MarketMapping(
        canonical_id="home_exact_goals_ft",
        name="Home Team Exact Goals - Full Time",
        betpawa_id="4942",
        sportybet_id="23",
        bet9ja_key="S_HOMEGOALS",
        outcome_mapping=(
            OutcomeMapping(canonical_id="0", betpawa_name="0", sportybet_desc="0", bet9ja_suffix="0", position=0),
            OutcomeMapping(canonical_id="1", betpawa_name="1", sportybet_desc="1", bet9ja_suffix="1", position=1),
            OutcomeMapping(canonical_id="2", betpawa_name="2", sportybet_desc="2", bet9ja_suffix="2", position=2),
            OutcomeMapping(canonical_id="3+", betpawa_name="3+", sportybet_desc="3+", bet9ja_suffix="3", position=3),
        ),
    ),

    MarketMapping(
        canonical_id="away_exact_goals_ft",
        name="Away Team Exact Goals - Full Time",
        betpawa_id="4938",
        sportybet_id="24",
        bet9ja_key="S_AWAYGOALS",
        outcome_mapping=(
            OutcomeMapping(canonical_id="0", betpawa_name="0", sportybet_desc="0", bet9ja_suffix="0", position=0),
            OutcomeMapping(canonical_id="1", betpawa_name="1", sportybet_desc="1", bet9ja_suffix="1", position=1),
            OutcomeMapping(canonical_id="2", betpawa_name="2", sportybet_desc="2", bet9ja_suffix="2", position=2),
            OutcomeMapping(canonical_id="3+", betpawa_name="3+", sportybet_desc="3+", bet9ja_suffix="3", position=3),
        ),
    ),

    # === Which Team To Score ===

    MarketMapping(
        canonical_id="which_team_to_score",
        name="Which Team To Score",
        betpawa_id="1096782",
        sportybet_id="30",
        bet9ja_key="S_TTSCORE",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home_only", betpawa_name="Home Team Only", sportybet_desc="Home only", bet9ja_suffix="H", position=0),
            OutcomeMapping(canonical_id="away_only", betpawa_name="Away Team Only", sportybet_desc="Away only", bet9ja_suffix="A", position=1),
            OutcomeMapping(canonical_id="both", betpawa_name="Both Teams", sportybet_desc="Both Teams", bet9ja_suffix="B", position=2),
            OutcomeMapping(canonical_id="neither", betpawa_name="Neither", sportybet_desc="Neither", bet9ja_suffix="N", position=3),
        ),
    ),

    # === Winning Margin ===

    MarketMapping(
        canonical_id="winning_margin",
        name="Winning Margin",
        betpawa_id="28000209",
        sportybet_id="15",
        bet9ja_key="S_WINMARGIN",
        outcome_mapping=(
            # Position-based matching for variable outcome structure
            OutcomeMapping(canonical_id="home_1", betpawa_name="Home by 1", sportybet_desc="Home by 1", bet9ja_suffix="HT1", position=0),
            OutcomeMapping(canonical_id="home_2", betpawa_name="Home by 2", sportybet_desc="Home by 2", bet9ja_suffix="HT2", position=1),
            OutcomeMapping(canonical_id="home_3+", betpawa_name="Home by 3+", sportybet_desc="Home by 3+", bet9ja_suffix="HT>2", position=2),
            OutcomeMapping(canonical_id="draw", betpawa_name="Draw", sportybet_desc="Draw", bet9ja_suffix="X", position=3),
            OutcomeMapping(canonical_id="away_1", betpawa_name="Away by 1", sportybet_desc="Away by 1", bet9ja_suffix="AT1", position=4),
            OutcomeMapping(canonical_id="away_2", betpawa_name="Away by 2", sportybet_desc="Away by 2", bet9ja_suffix="AT2", position=5),
            OutcomeMapping(canonical_id="away_3+", betpawa_name="Away by 3+", sportybet_desc="Away by 3+", bet9ja_suffix="AT>2", position=6),
        ),
    ),

    # === Combo Markets ===

    MarketMapping(
        canonical_id="1x2_over_under_ft",
        name="1X2 and Over/Under - Full Time",
        betpawa_id="1096755",
        sportybet_id="37",
        bet9ja_key="S_1X2OU",
        outcome_mapping=(
            # Complex combo - position-based matching preferred
            OutcomeMapping(canonical_id="home_over", betpawa_name="1 & Over", sportybet_desc="Home & Over", bet9ja_suffix="1O", position=0),
            OutcomeMapping(canonical_id="home_under", betpawa_name="1 & Under", sportybet_desc="Home & Under", bet9ja_suffix="1U", position=1),
            OutcomeMapping(canonical_id="draw_over", betpawa_name="X & Over", sportybet_desc="Draw & Over", bet9ja_suffix="XO", position=2),
            OutcomeMapping(canonical_id="draw_under", betpawa_name="X & Under", sportybet_desc="Draw & Under", bet9ja_suffix="XU", position=3),
            OutcomeMapping(canonical_id="away_over", betpawa_name="2 & Over", sportybet_desc="Away & Over", bet9ja_suffix="2O", position=4),
            OutcomeMapping(canonical_id="away_under", betpawa_name="2 & Under", sportybet_desc="Away & Under", bet9ja_suffix="2U", position=5),
        ),
    ),

    MarketMapping(
        canonical_id="1x2_btts_ft",
        name="1X2 and Both Teams To Score - Full Time",
        betpawa_id="3591790",
        sportybet_id="35",
        bet9ja_key="S_1X2GGNG",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home_yes", betpawa_name="1 - Yes", sportybet_desc="Home & Yes", bet9ja_suffix="1ANDGG", position=0),
            OutcomeMapping(canonical_id="home_no", betpawa_name="1 - No", sportybet_desc="Home & No", bet9ja_suffix="1ANDNG", position=1),
            OutcomeMapping(canonical_id="draw_yes", betpawa_name="X - Yes", sportybet_desc="Draw & Yes", bet9ja_suffix="XANDGG", position=2),
            OutcomeMapping(canonical_id="draw_no", betpawa_name="X - No", sportybet_desc="Draw & No", bet9ja_suffix="XANDNG", position=3),
            OutcomeMapping(canonical_id="away_yes", betpawa_name="2 - Yes", sportybet_desc="Away & Yes", bet9ja_suffix="2ANDGG", position=4),
            OutcomeMapping(canonical_id="away_no", betpawa_name="2 - No", sportybet_desc="Away & No", bet9ja_suffix="2ANDNG", position=5),
        ),
    ),

    MarketMapping(
        canonical_id="over_under_btts_ft",
        name="Over/Under and Both Teams To Score - Full Time",
        betpawa_id="4613062",
        sportybet_id="36",
        bet9ja_key="S_OUGGNG",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over_yes", betpawa_name="Over & Yes", sportybet_desc="Over & Yes", bet9ja_suffix="OY", position=0),
            OutcomeMapping(canonical_id="over_no", betpawa_name="Over & No", sportybet_desc="Over & No", bet9ja_suffix="ON", position=1),
            OutcomeMapping(canonical_id="under_yes", betpawa_name="Under & Yes", sportybet_desc="Under & Yes", bet9ja_suffix="UY", position=2),
            OutcomeMapping(canonical_id="under_no", betpawa_name="Under & No", sportybet_desc="Under & No", bet9ja_suffix="UN", position=3),
        ),
    ),

    MarketMapping(
        canonical_id="double_chance_btts_ft",
        name="Double Chance and Both Teams To Score - Full Time",
        betpawa_id="28000014",
        sportybet_id="546",
        bet9ja_key="S_DCGGNG",
        outcome_mapping=(
            OutcomeMapping(canonical_id="1x_yes", betpawa_name="1X - Yes", sportybet_desc="Home or Draw & Yes", bet9ja_suffix="1XGG", position=0),
            OutcomeMapping(canonical_id="1x_no", betpawa_name="1X - No", sportybet_desc="Home or Draw & No", bet9ja_suffix="1XNG", position=1),
            OutcomeMapping(canonical_id="x2_yes", betpawa_name="X2 - Yes", sportybet_desc="Draw or Away & Yes", bet9ja_suffix="X2GG", position=2),
            OutcomeMapping(canonical_id="x2_no", betpawa_name="X2 - No", sportybet_desc="Draw or Away & No", bet9ja_suffix="X2NG", position=3),
            OutcomeMapping(canonical_id="12_yes", betpawa_name="12 - Yes", sportybet_desc="Home or Away & Yes", bet9ja_suffix="12GG", position=4),
            OutcomeMapping(canonical_id="12_no", betpawa_name="12 - No", sportybet_desc="Home or Away & No", bet9ja_suffix="12NG", position=5),
        ),
    ),

    MarketMapping(
        canonical_id="double_chance_over_under_ft",
        name="Double Chance and Over/Under - Full Time",
        betpawa_id="28000089",
        sportybet_id="547",
        bet9ja_key="S_DCOU",
        outcome_mapping=(
            OutcomeMapping(canonical_id="1x_over", betpawa_name="1X & Over", sportybet_desc="Home or Draw & Over", bet9ja_suffix="1XO", position=0),
            OutcomeMapping(canonical_id="1x_under", betpawa_name="1X & Under", sportybet_desc="Home or Draw & Under", bet9ja_suffix="1XU", position=1),
            OutcomeMapping(canonical_id="x2_over", betpawa_name="X2 & Over", sportybet_desc="Draw or Away & Over", bet9ja_suffix="X2O", position=2),
            OutcomeMapping(canonical_id="x2_under", betpawa_name="X2 & Under", sportybet_desc="Draw or Away & Under", bet9ja_suffix="X2U", position=3),
            OutcomeMapping(canonical_id="12_over", betpawa_name="12 & Over", sportybet_desc="Home or Away & Over", bet9ja_suffix="12O", position=4),
            OutcomeMapping(canonical_id="12_under", betpawa_name="12 & Under", sportybet_desc="Home or Away & Under", bet9ja_suffix="12U", position=5),
        ),
    ),

    MarketMapping(
        canonical_id="htft_correct_score",
        name="Half Time/Full Time Correct Score",
        betpawa_id="28000228",
        sportybet_id="46",
        bet9ja_key="S_HTFTCS",
        outcome_mapping=(
            # HT/FT Correct Score combinations - position-based matching
            OutcomeMapping(canonical_id="pos_0", betpawa_name=None, sportybet_desc=None, bet9ja_suffix=None, position=0),
        ),
    ),

    MarketMapping(
        canonical_id="htft_over_under",
        name="Half Time/Full Time and Over/Under",
        betpawa_id="28000279",
        sportybet_id="818",
        bet9ja_key="S_HTFTOU",
        outcome_mapping=(
            # Many outcomes - position-based matching
            OutcomeMapping(canonical_id="pos_0", betpawa_name=None, sportybet_desc=None, bet9ja_suffix=None, position=0),
        ),
    ),

    # === Multigoals Markets ===

    MarketMapping(
        canonical_id="multigoals_ft",
        name="Multigoals - Full Time",
        betpawa_id="28000047",
        sportybet_id="548",
        bet9ja_key="S_MULTIGOAL",
        outcome_mapping=(
            # Position-based matching for goal ranges
            OutcomeMapping(canonical_id="0_1", betpawa_name="0-1", sportybet_desc="0-1 Goals", bet9ja_suffix=None, position=0),
            OutcomeMapping(canonical_id="2_3", betpawa_name="2-3", sportybet_desc="2-3 Goals", bet9ja_suffix=None, position=1),
            OutcomeMapping(canonical_id="4_5", betpawa_name="4-5", sportybet_desc="4-5 Goals", bet9ja_suffix=None, position=2),
            OutcomeMapping(canonical_id="6+", betpawa_name="6+", sportybet_desc="6+ Goals", bet9ja_suffix=None, position=3),
        ),
    ),

    MarketMapping(
        canonical_id="multigoals_1h",
        name="Multigoals - First Half",
        betpawa_id="28000065",
        sportybet_id="552",
        bet9ja_key="S_MULTIGOAL1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="0_1", betpawa_name="0-1", sportybet_desc="0-1 Goals", bet9ja_suffix=None, position=0),
            OutcomeMapping(canonical_id="2_3", betpawa_name="2-3", sportybet_desc="2-3 Goals", bet9ja_suffix=None, position=1),
            OutcomeMapping(canonical_id="4+", betpawa_name="4+", sportybet_desc="4+ Goals", bet9ja_suffix=None, position=2),
        ),
    ),

    MarketMapping(
        canonical_id="multigoals_2h",
        name="Multigoals - Second Half",
        betpawa_id="28000071",
        sportybet_id="553",
        bet9ja_key="S_MULTIGOAL2T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="0_1", betpawa_name="0-1", sportybet_desc="0-1 Goals", bet9ja_suffix=None, position=0),
            OutcomeMapping(canonical_id="2_3", betpawa_name="2-3", sportybet_desc="2-3 Goals", bet9ja_suffix=None, position=1),
            OutcomeMapping(canonical_id="4+", betpawa_name="4+", sportybet_desc="4+ Goals", bet9ja_suffix=None, position=2),
        ),
    ),

    MarketMapping(
        canonical_id="home_multigoals_ft",
        name="Home Team Multigoals - Full Time",
        betpawa_id="28000077",
        sportybet_id="549",
        bet9ja_key="S_TMGHO",
        outcome_mapping=(
            OutcomeMapping(canonical_id="0", betpawa_name="No goal", sportybet_desc="0 Goals", bet9ja_suffix=None, position=0),
            OutcomeMapping(canonical_id="1_2", betpawa_name="1-2", sportybet_desc="1-2 Goals", bet9ja_suffix=None, position=1),
            OutcomeMapping(canonical_id="3+", betpawa_name="3+", sportybet_desc="3+ Goals", bet9ja_suffix=None, position=2),
        ),
    ),

    MarketMapping(
        canonical_id="away_multigoals_ft",
        name="Away Team Multigoals - Full Time",
        betpawa_id="28000083",
        sportybet_id="550",
        bet9ja_key="S_TMGAW",
        outcome_mapping=(
            OutcomeMapping(canonical_id="0", betpawa_name="No goal", sportybet_desc="0 Goals", bet9ja_suffix=None, position=0),
            OutcomeMapping(canonical_id="1_2", betpawa_name="1-2", sportybet_desc="1-2 Goals", bet9ja_suffix=None, position=1),
            OutcomeMapping(canonical_id="3+", betpawa_name="3+", sportybet_desc="3+ Goals", bet9ja_suffix=None, position=2),
        ),
    ),

    # === Multiscores Market ===

    MarketMapping(
        canonical_id="multiscores_ft",
        name="Multiscores - Full Time",
        betpawa_id="28000035",
        sportybet_id="551",
        bet9ja_key=None,
        outcome_mapping=(
            # Position-based matching for score ranges
            OutcomeMapping(canonical_id="pos_0", betpawa_name=None, sportybet_desc=None, bet9ja_suffix=None, position=0),
        ),
    ),

    # === Corner Markets ===

    MarketMapping(
        canonical_id="corners_over_under_ft",
        name="Total Corners Over/Under - Full Time",
        betpawa_id="1096783",
        sportybet_id="166",
        bet9ja_key="S_OUCORNERS",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="O", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="U", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="corners_over_under_1h",
        name="Total Corners Over/Under - First Half",
        betpawa_id="1096784",
        sportybet_id="177",
        bet9ja_key="S_OUCORNERS1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="O", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="U", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="corners_1x2_ft",
        name="Corner Count 1X2 - Full Time",
        betpawa_id="1096787",
        sportybet_id="162",
        bet9ja_key="S_1X2CORNERS",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="draw", betpawa_name="X", sportybet_desc="Draw", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="corners_1x2_1h",
        name="Corner Count 1X2 - First Half",
        betpawa_id="1096788",
        sportybet_id="173",
        bet9ja_key="S_1X2CORNERS1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="draw", betpawa_name="X", sportybet_desc="Draw", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="corner_handicap_ft",
        name="Corner Asian Handicap - Full Time",
        betpawa_id="1096785",
        sportybet_id="165",
        bet9ja_key="S_AHCORNERS",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="corner_handicap_1h",
        name="Corner Asian Handicap - First Half",
        betpawa_id="1096786",
        sportybet_id="176",
        bet9ja_key="S_AHCORNERS1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="home_corners_ft",
        name="Home Team Total Corners - Full Time",
        betpawa_id="1096793",
        sportybet_id="900300",
        bet9ja_key="S_CORNERSHOMEOU",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="HCO", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="HCU", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="home_corners_1h",
        name="Home Team Total Corners - First Half",
        betpawa_id="1096794",
        sportybet_id="900302",
        bet9ja_key=None,
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix=None, position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix=None, position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_corners_ft",
        name="Away Team Total Corners - Full Time",
        betpawa_id="1096797",
        sportybet_id="900301",
        bet9ja_key="S_CORNERSAWAYOU",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="ACO", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="ACU", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_corners_1h",
        name="Away Team Total Corners - First Half",
        betpawa_id="1096802",
        sportybet_id="900303",
        bet9ja_key=None,
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix=None, position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix=None, position=1),
        ),
    ),

    MarketMapping(
        canonical_id="last_corner_ft",
        name="Last Corner - Full Time",
        betpawa_id="1096795",
        sportybet_id="164",
        bet9ja_key="S_LASTCORNER",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="Home", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="none", betpawa_name="None", sportybet_desc="None", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="Away", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="last_corner_1h",
        name="Last Corner - First Half",
        betpawa_id="1096796",
        sportybet_id="175",
        bet9ja_key="S_LCH",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="Home", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="none", betpawa_name="None", sportybet_desc="None", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="Away", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="first_corner_ft",
        name="First Corner - Full Time",
        betpawa_id=None,
        sportybet_id="163",
        bet9ja_key="S_1STCORNER",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="Home", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="none", betpawa_name="None", sportybet_desc="None", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="Away", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="corners_exact_ft",
        name="Total Corners Exact - Full Time",
        betpawa_id="1096803",
        sportybet_id="169",
        bet9ja_key="S_NCORN",
        outcome_mapping=(
            # Position-based matching for variable outcome counts
            OutcomeMapping(canonical_id="pos_0", betpawa_name=None, sportybet_desc=None, bet9ja_suffix=None, position=0),
        ),
    ),

    MarketMapping(
        canonical_id="corners_exact_1h",
        name="Total Corners Exact - First Half",
        betpawa_id="1096804",
        sportybet_id="182",
        bet9ja_key=None,
        outcome_mapping=(
            # Position-based matching for variable outcome counts
            OutcomeMapping(canonical_id="pos_0", betpawa_name=None, sportybet_desc=None, bet9ja_suffix=None, position=0),
        ),
    ),

    MarketMapping(
        canonical_id="corners_odd_even_ft",
        name="Total Corners Odd/Even - Full Time",
        betpawa_id="1096789",
        sportybet_id="172",
        bet9ja_key="S_OECORNER",
        outcome_mapping=(
            OutcomeMapping(canonical_id="odd", betpawa_name="Odd", sportybet_desc="Odd", bet9ja_suffix="OD", position=0),
            OutcomeMapping(canonical_id="even", betpawa_name="Even", sportybet_desc="Even", bet9ja_suffix="EV", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="corners_odd_even_1h",
        name="Total Corners Odd/Even - First Half",
        betpawa_id="1096790",
        sportybet_id="183",
        bet9ja_key=None,
        outcome_mapping=(
            OutcomeMapping(canonical_id="odd", betpawa_name="Odd", sportybet_desc="Odd", bet9ja_suffix=None, position=0),
            OutcomeMapping(canonical_id="even", betpawa_name="Even", sportybet_desc="Even", bet9ja_suffix=None, position=1),
        ),
    ),

    # === Booking Markets ===

    MarketMapping(
        canonical_id="bookings_over_under_ft",
        name="Total Bookings Over/Under - Full Time",
        betpawa_id="1096764",
        sportybet_id="139",
        bet9ja_key="S_OUBOOK",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="O", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="U", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="bookings_over_under_1h",
        name="Total Bookings Over/Under - First Half",
        betpawa_id="1096765",
        sportybet_id="152",
        bet9ja_key="S_OUBOOK1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="O", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="U", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="bookings_1x2_ft",
        name="Team with Most Bookings 3-Way - Full Time",
        betpawa_id="1096774",
        sportybet_id="136",
        bet9ja_key="S_1X2BOOK",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="draw", betpawa_name="X", sportybet_desc="Draw", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="bookings_1x2_1h",
        name="Team with Most Bookings 3-Way - First Half",
        betpawa_id="1096775",
        sportybet_id="149",
        bet9ja_key="S_1X2BOOK1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="1", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="draw", betpawa_name="X", sportybet_desc="Draw", bet9ja_suffix="X", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="2", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="first_card_ft",
        name="First Card - Full Time",
        betpawa_id=None,
        sportybet_id="137",
        bet9ja_key="S_1STBOOK",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="Home", sportybet_desc="Home", bet9ja_suffix="1", position=0),
            OutcomeMapping(canonical_id="none", betpawa_name="None", sportybet_desc="None", bet9ja_suffix="N", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="Away", sportybet_desc="Away", bet9ja_suffix="2", position=2),
        ),
    ),

    MarketMapping(
        canonical_id="bookings_exact_ft",
        name="Total Bookings Exact - Full Time",
        betpawa_id="1096776",
        sportybet_id="142",
        bet9ja_key="S_EXACTBOOK",
        outcome_mapping=(
            # Position-based matching for variable outcome counts
            OutcomeMapping(canonical_id="pos_0", betpawa_name=None, sportybet_desc=None, bet9ja_suffix=None, position=0),
        ),
    ),

    MarketMapping(
        canonical_id="bookings_exact_1h",
        name="Total Bookings Exact - First Half",
        betpawa_id="1096777",
        sportybet_id="155",
        bet9ja_key=None,
        outcome_mapping=(
            # Position-based matching for variable outcome counts
            OutcomeMapping(canonical_id="pos_0", betpawa_name=None, sportybet_desc=None, bet9ja_suffix=None, position=0),
        ),
    ),

    MarketMapping(
        canonical_id="home_bookings_ft",
        name="Home Team Total Bookings - Full Time",
        betpawa_id="1096768",
        sportybet_id="900304",
        bet9ja_key="S_OUBOOKHOME",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="O", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="U", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="home_bookings_1h",
        name="Home Team Total Bookings - First Half",
        betpawa_id="1096769",
        sportybet_id="900306",
        bet9ja_key=None,
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="O", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="U", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_bookings_ft",
        name="Away Team Total Bookings - Full Time",
        betpawa_id="1096770",
        sportybet_id="900305",
        bet9ja_key="S_OUBOOKAWAY",
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="O", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="U", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_bookings_1h",
        name="Away Team Total Bookings - First Half",
        betpawa_id="1096771",
        sportybet_id="900307",
        bet9ja_key=None,
        outcome_mapping=(
            OutcomeMapping(canonical_id="over", betpawa_name="Over", sportybet_desc="Over", bet9ja_suffix="O", position=0),
            OutcomeMapping(canonical_id="under", betpawa_name="Under", sportybet_desc="Under", bet9ja_suffix="U", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="sending_off_ft",
        name="Player Sent Off - Full Time",
        betpawa_id="1096766",
        sportybet_id="146",
        bet9ja_key="S_SENDOFF",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="home_sending_off_ft",
        name="Home Team Sending Off - Full Time",
        betpawa_id="1096778",
        sportybet_id="147",
        bet9ja_key="S_RCH",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    MarketMapping(
        canonical_id="away_sending_off_ft",
        name="Away Team Sending Off - Full Time",
        betpawa_id="1096780",
        sportybet_id="148",
        bet9ja_key="S_RCA",
        outcome_mapping=(
            OutcomeMapping(canonical_id="yes", betpawa_name="Yes", sportybet_desc="Yes", bet9ja_suffix="Y", position=0),
            OutcomeMapping(canonical_id="no", betpawa_name="No", sportybet_desc="No", bet9ja_suffix="N", position=1),
        ),
    ),

    # === Additional Goal Markets ===

    MarketMapping(
        canonical_id="last_goal_ft",
        name="Team To Score Last / Last Goal - Full Time",
        betpawa_id="4870",
        sportybet_id="9",
        bet9ja_key="S_LASTGOAL",
        outcome_mapping=(
            OutcomeMapping(canonical_id="home", betpawa_name="Home", sportybet_desc="Home", bet9ja_suffix="H", position=0),
            OutcomeMapping(canonical_id="none", betpawa_name="No Goal", sportybet_desc="No Goal", bet9ja_suffix="N", position=1),
            OutcomeMapping(canonical_id="away", betpawa_name="Away", sportybet_desc="Away", bet9ja_suffix="A", position=2),
        ),
    ),

    # === Additional Double Chance Combo Markets ===

    MarketMapping(
        canonical_id="double_chance_btts_1h",
        name="Double Chance and Both Teams To Score - First Half",
        betpawa_id="28000021",
        sportybet_id="542",
        bet9ja_key="S_DCGGNG1T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="1x_yes", betpawa_name="1X - Yes", sportybet_desc="Home or Draw & Yes", bet9ja_suffix="1XGG1T", position=0),
            OutcomeMapping(canonical_id="1x_no", betpawa_name="1X - No", sportybet_desc="Home or Draw & No", bet9ja_suffix="1XNG1T", position=1),
            OutcomeMapping(canonical_id="x2_yes", betpawa_name="X2 - Yes", sportybet_desc="Draw or Away & Yes", bet9ja_suffix="X2GG1T", position=2),
            OutcomeMapping(canonical_id="x2_no", betpawa_name="X2 - No", sportybet_desc="Draw or Away & No", bet9ja_suffix="X2NG1T", position=3),
            OutcomeMapping(canonical_id="12_yes", betpawa_name="12 - Yes", sportybet_desc="Home or Away & Yes", bet9ja_suffix="12GG1T", position=4),
            OutcomeMapping(canonical_id="12_no", betpawa_name="12 - No", sportybet_desc="Home or Away & No", bet9ja_suffix="12NG1T", position=5),
        ),
    ),

    MarketMapping(
        canonical_id="double_chance_btts_2h",
        name="Double Chance and Both Teams To Score - Second Half",
        betpawa_id="28000028",
        sportybet_id="545",
        bet9ja_key="S_DCGGNG2T",
        outcome_mapping=(
            OutcomeMapping(canonical_id="1x_yes", betpawa_name="1X - Yes", sportybet_desc="Home or Draw & Yes", bet9ja_suffix="1XGG2T", position=0),
            OutcomeMapping(canonical_id="1x_no", betpawa_name="1X - No", sportybet_desc="Home or Draw & No", bet9ja_suffix="1XNG2T", position=1),
            OutcomeMapping(canonical_id="x2_yes", betpawa_name="X2 - Yes", sportybet_desc="Draw or Away & Yes", bet9ja_suffix="X2GG2T", position=2),
            OutcomeMapping(canonical_id="x2_no", betpawa_name="X2 - No", sportybet_desc="Draw or Away & No", bet9ja_suffix="X2NG2T", position=3),
            OutcomeMapping(canonical_id="12_yes", betpawa_name="12 - Yes", sportybet_desc="Home or Away & Yes", bet9ja_suffix="12GG2T", position=4),
            OutcomeMapping(canonical_id="12_no", betpawa_name="12 - No", sportybet_desc="Home or Away & No", bet9ja_suffix="12NG2T", position=5),
        ),
    ),
)


# =============================================================================
# Lookup Dictionaries (built at module load time for O(1) access)
# =============================================================================

_BY_BETPAWA_ID: dict[str, MarketMapping] = {}
_BY_SPORTYBET_ID: dict[str, MarketMapping] = {}
_BY_CANONICAL_ID: dict[str, MarketMapping] = {}
_BY_BET9JA_KEY: dict[str, MarketMapping] = {}


def _build_lookups() -> None:
    """Build lookup dictionaries at module load time."""
    for mapping in MARKET_MAPPINGS:
        _BY_CANONICAL_ID[mapping.canonical_id] = mapping
        if mapping.betpawa_id:
            _BY_BETPAWA_ID[mapping.betpawa_id] = mapping
        if mapping.sportybet_id:
            _BY_SPORTYBET_ID[mapping.sportybet_id] = mapping
        if mapping.bet9ja_key:
            _BY_BET9JA_KEY[mapping.bet9ja_key] = mapping


_build_lookups()


# =============================================================================
# Market Classification Sets (based on Sportybet IDs)
# =============================================================================

# Over/Under market IDs (Sportybet IDs)
OVER_UNDER_MARKET_IDS: frozenset[str] = frozenset({
    "18",  # Over/Under - Full Time
    "68",  # Over/Under - First Half
    "90",  # Over/Under - Second Half
    "19",  # Home Team Over/Under - Full Time
    "20",  # Away Team Over/Under - Full Time
    "69",  # Home Team Over/Under - First Half
    "70",  # Away Team Over/Under - First Half
    "91",  # Home Team Over/Under - Second Half
    "92",  # Away Team Over/Under - Second Half
    "166",  # Total Corners Over/Under - Full Time
    "177",  # Total Corners Over/Under - First Half
    "139",  # Total Bookings Over/Under - Full Time
    "152",  # Total Bookings Over/Under - First Half
    "900300",  # Home Team Total Corners - Full Time
    "900301",  # Away Team Total Corners - Full Time
    "900302",  # Home Team Total Corners - First Half
    "900303",  # Away Team Total Corners - First Half
    "900304",  # Home Team Total Bookings - Full Time
    "900305",  # Away Team Total Bookings - Full Time
    "900306",  # Home Team Total Bookings - First Half
    "900307",  # Away Team Total Bookings - First Half
})

# Handicap market IDs (Sportybet IDs)
HANDICAP_MARKET_IDS: frozenset[str] = frozenset({
    "14",  # 3-Way Handicap - Full Time
    "16",  # Asian Handicap - Full Time
    "65",  # 3-Way Handicap - First Half
    "66",  # Asian Handicap - First Half
    "87",  # 3-Way Handicap - Second Half
    "88",  # Asian Handicap - Second Half
    "165",  # Corner Asian Handicap - Full Time
    "176",  # Corner Asian Handicap - First Half
})

# Variant/exact goal market IDs (Sportybet IDs)
VARIANT_MARKET_IDS: frozenset[str] = frozenset({
    "21",  # Exact Goals - Full Time
    "23",  # Home Team Exact Goals - Full Time
    "24",  # Away Team Exact Goals - Full Time
    "71",  # Exact Goals - First Half
    "93",  # Exact Goals - Second Half
    "15",  # Winning Margin
    "548",  # Multigoals - Full Time
    "549",  # Home Team Multigoals - Full Time
    "550",  # Away Team Multigoals - Full Time
    "551",  # Multiscores - Full Time
    "552",  # Multigoals - First Half
    "553",  # Multigoals - Second Half
})


# =============================================================================
# Lookup Functions
# =============================================================================

def find_by_betpawa_id(market_id: str) -> MarketMapping | None:
    """Find a market mapping by Betpawa market type ID.

    Args:
        market_id: Betpawa marketType.id (e.g., "3743")

    Returns:
        The matching MarketMapping or None if not found
    """
    return _BY_BETPAWA_ID.get(market_id)


def find_by_sportybet_id(market_id: str) -> MarketMapping | None:
    """Find a market mapping by Sportybet market ID.

    Args:
        market_id: Sportybet market.id (e.g., "1")

    Returns:
        The matching MarketMapping or None if not found
    """
    return _BY_SPORTYBET_ID.get(market_id)


def find_by_canonical_id(canonical_id: str) -> MarketMapping | None:
    """Find a market mapping by canonical ID.

    Args:
        canonical_id: Canonical market ID (e.g., "1x2_ft")

    Returns:
        The matching MarketMapping or None if not found
    """
    return _BY_CANONICAL_ID.get(canonical_id)


def find_by_bet9ja_key(bet9ja_key: str) -> MarketMapping | None:
    """Find a market mapping by Bet9ja key.

    Accepts a market key (e.g., "S_1X2", "S_OU").

    Args:
        bet9ja_key: Bet9ja market key (e.g., "S_1X2")

    Returns:
        The matching MarketMapping or None if not found
    """
    return _BY_BET9JA_KEY.get(bet9ja_key)


# =============================================================================
# Classification Helper Functions
# =============================================================================

def is_over_under_market(sportybet_id: str) -> bool:
    """Check if a market is an Over/Under type market.

    Args:
        sportybet_id: Sportybet market ID

    Returns:
        True if the market is an Over/Under market
    """
    return sportybet_id in OVER_UNDER_MARKET_IDS


def is_handicap_market(sportybet_id: str) -> bool:
    """Check if a market is a Handicap type market.

    Args:
        sportybet_id: Sportybet market ID

    Returns:
        True if the market is a Handicap market
    """
    return sportybet_id in HANDICAP_MARKET_IDS


def is_variant_market(sportybet_id: str) -> bool:
    """Check if a market is a Variant/Exact goals type market.

    Args:
        sportybet_id: Sportybet market ID

    Returns:
        True if the market is a Variant market
    """
    return sportybet_id in VARIANT_MARKET_IDS
