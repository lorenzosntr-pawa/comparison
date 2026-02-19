# Plan 107-02 Summary: API Endpoints & Write Handler

## Completed
- **Duration**: ~15 minutes
- **Tasks**: 3/3 completed
- **Commits**: 3

## Task Outcomes

### Task 1: Create Pydantic schemas for risk alerts
**Files**: `src/api/schemas/alerts.py`, `src/api/schemas/__init__.py`
**Commit**: `7427314`

Created Pydantic schemas following storage.py patterns:
- `RiskAlertResponse`: Full alert data with 17 fields, from_attributes=True for ORM validation
- `RiskAlertsResponse`: Paginated list with status counts (new, acknowledged, past)
- `RiskAlertStatsResponse`: Summary statistics grouped by status/severity/type
- `AcknowledgeAlertRequest`: Request body for acknowledge/unacknowledge

All schemas use ConfigDict with to_camel alias generator for frontend compatibility.

### Task 2: Create alerts API routes
**Files**: `src/api/routes/alerts.py`, `src/api/routes/events.py`, `src/api/app.py`
**Commit**: `37ce271`

Created FastAPI router with endpoints:
- `GET /alerts`: List with filters (status, severity, event_id), pagination, status counts
- `GET /alerts/stats`: Summary statistics grouped by status/severity/type
- `GET /alerts/{id}`: Single alert retrieval with 404 handling
- `PATCH /alerts/{id}`: Acknowledge/unacknowledge with 400 for PAST alerts
- `GET /events/{id}/alerts`: Event-specific alerts (added to events router)

Used deferred imports to avoid circular dependencies.

### Task 3: Extend WriteBatch and write_handler for alert persistence
**Files**: `src/storage/write_queue.py`, `src/storage/write_handler.py`, `src/scraping/event_coordinator.py`
**Commit**: `bd6b1d6`

Extended persistence layer:
- Added `alerts: tuple[RiskAlertData, ...] = ()` field to WriteBatch
- Added Step 7 to write_handler: INSERT RiskAlert rows from DTOs with status="new"
- Updated event_coordinator to pass `alerts=tuple(risk_alerts)` to WriteBatch
- Added alerts_inserted to stats dict for logging

## Verification Results
- All imports verified working
- WriteBatch has alerts field
- RiskAlertResponse has all 17 expected fields
- API endpoints registered in app router

## Changes Summary
- **Created**: 1 new file (alerts.py schemas)
- **Created**: 1 new file (alerts.py routes)
- **Modified**: 4 existing files (schemas/__init__.py, app.py, events.py, write_queue.py, write_handler.py, event_coordinator.py)

## Key Patterns Applied
- Pydantic v2 ConfigDict with to_camel alias generator and from_attributes=True
- Deferred imports in routes to avoid circular dependencies
- Frozen dataclass DTO (RiskAlertData) for decoupled persistence
- Per-batch atomic commits with alerts alongside other data

## End-to-End Flow
1. Scrape cycle detects alerts via detect_risk_alerts()
2. Alerts passed as tuple to WriteBatch
3. write_handler persists RiskAlert rows with status="new"
4. API endpoints retrieve and manage alerts
5. PATCH endpoint handles acknowledge workflow

## Notes
- No alerts exist yet until scraper detects price movements
- Phase 108 (Risk Monitoring Page) will consume these endpoints
