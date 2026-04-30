-- Competition coverage gap analysis: BetPawa vs competitors
-- Shows which tournaments competitors offer that BetPawa doesn't,
-- and how many days before kickoff each platform lists events.
-- Parameters: Replace date range and competitor filter in WHERE clause.

WITH event_coverage AS (
    SELECT
        ct.source AS competitor,
        ct.id AS competitor_tournament_id,
        ct.name AS competitor_tournament,
        ct.country_raw AS country,
        ce.kickoff,
        ce.created_at AS competitor_created_at,
        ce.betpawa_event_id,
        e.created_at AS betpawa_created_at,
        t.name AS betpawa_tournament
    FROM competitor_events ce
    INNER JOIN competitor_tournaments ct ON ct.id = ce.tournament_id
    LEFT JOIN events e ON e.id = ce.betpawa_event_id
    LEFT JOIN tournaments t ON t.id = e.tournament_id
    WHERE
        ce.kickoff >= '2026-01-01'::timestamp  -- Start date (inclusive)
        AND ce.kickoff < '2026-04-01'::timestamp -- End date (exclusive)
        -- AND ct.source = 'sportybet'           -- Uncomment to filter by competitor
        AND ce.deleted_at IS NULL
        AND ct.deleted_at IS NULL
)

SELECT
    competitor AS "Competitor",
    competitor_tournament AS "Competitor Tournament",
    MODE() WITHIN GROUP (ORDER BY betpawa_tournament) AS "BetPawa Tournament",
    country AS "Country",
    COUNT(*) AS "Total Events (Competitor)",
    COUNT(betpawa_event_id) AS "Total Events (BetPawa)",
    COUNT(*) - COUNT(betpawa_event_id) AS "Missing Events",
    ROUND(
        COUNT(betpawa_event_id)::numeric / COUNT(*)::numeric * 100, 1
    ) AS "Coverage %",
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM (kickoff - competitor_created_at)) / 86400.0
        ) FILTER (WHERE competitor_created_at IS NOT NULL),
        1
    ) AS "Avg Days Before KO (Competitor)",
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM (kickoff - betpawa_created_at)) / 86400.0
        ) FILTER (WHERE betpawa_event_id IS NOT NULL AND betpawa_created_at IS NOT NULL),
        1
    ) AS "Avg Days Before KO (BetPawa)",
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM (kickoff - competitor_created_at)) / 86400.0
            - EXTRACT(EPOCH FROM (kickoff - betpawa_created_at)) / 86400.0
        ) FILTER (WHERE betpawa_event_id IS NOT NULL AND competitor_created_at IS NOT NULL AND betpawa_created_at IS NOT NULL),
        1
    ) AS "Avg Timing Gap (Days)"  -- Positive = competitor listed earlier than BetPawa
FROM event_coverage
GROUP BY competitor, competitor_tournament_id, competitor_tournament, country
ORDER BY "Missing Events" DESC, competitor_tournament;
