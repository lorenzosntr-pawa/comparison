# Market Mapping Utility - Architecture Design

**Date:** 2026-02-13
**Status:** Implementation Ready
**Target Phases:** 101-106

## Overview

This document specifies the architecture for a user-editable market mapping system that:
1. Persists user-defined mappings alongside code mappings
2. Logs unmapped markets for discovery and analysis
3. Provides CRUD API for mapping management
4. Supports hot reload without application restart

---

## 1. Database Schema

### 1.1 user_market_mappings

Stores user-defined market mappings that can override or extend code definitions.

```sql
CREATE TABLE user_market_mappings (
    id SERIAL PRIMARY KEY,
    canonical_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    betpawa_id VARCHAR(50),
    sportybet_id VARCHAR(50),
    bet9ja_key VARCHAR(50),
    outcome_mapping JSONB NOT NULL,
    priority INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_user_mappings_active ON user_market_mappings(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_user_mappings_betpawa ON user_market_mappings(betpawa_id) WHERE betpawa_id IS NOT NULL;
CREATE INDEX idx_user_mappings_sportybet ON user_market_mappings(sportybet_id) WHERE sportybet_id IS NOT NULL;
CREATE INDEX idx_user_mappings_bet9ja ON user_market_mappings(bet9ja_key) WHERE bet9ja_key IS NOT NULL;
```

**Column Details:**

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Auto-increment primary key |
| `canonical_id` | VARCHAR(100) | Unique market identifier (e.g., "1x2_ft", "user_over_3.5") |
| `name` | VARCHAR(255) | Human-readable name (e.g., "1X2 - Full Time") |
| `betpawa_id` | VARCHAR(50) | BetPawa marketType.id, nullable if not mapped |
| `sportybet_id` | VARCHAR(50) | SportyBet market.id, nullable if not mapped |
| `bet9ja_key` | VARCHAR(50) | Bet9ja key prefix (e.g., "S_1X2"), nullable |
| `outcome_mapping` | JSONB | Array of outcome mappings (see schema below) |
| `priority` | INTEGER | Override priority (higher wins over code) |
| `is_active` | BOOLEAN | Soft delete flag, defaults to true |
| `created_at` | TIMESTAMPTZ | Creation timestamp |
| `updated_at` | TIMESTAMPTZ | Last modification timestamp |
| `created_by` | VARCHAR(100) | User identifier (future auth integration) |

**outcome_mapping JSONB Schema:**

```json
[
  {
    "canonical_id": "home",
    "betpawa_name": "1",
    "sportybet_desc": "Home",
    "bet9ja_suffix": "1",
    "position": 0
  },
  {
    "canonical_id": "draw",
    "betpawa_name": "X",
    "sportybet_desc": "Draw",
    "bet9ja_suffix": "X",
    "position": 1
  }
]
```

### 1.2 mapping_audit_log

Tracks all changes to user mappings for accountability and debugging.

```sql
CREATE TABLE mapping_audit_log (
    id SERIAL PRIMARY KEY,
    mapping_id INTEGER REFERENCES user_market_mappings(id) ON DELETE SET NULL,
    canonical_id VARCHAR(100) NOT NULL,
    action VARCHAR(20) NOT NULL,
    old_value JSONB,
    new_value JSONB,
    reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by VARCHAR(100)
);

-- Indexes
CREATE INDEX idx_audit_log_mapping ON mapping_audit_log(mapping_id);
CREATE INDEX idx_audit_log_canonical ON mapping_audit_log(canonical_id);
CREATE INDEX idx_audit_log_action ON mapping_audit_log(action);
CREATE INDEX idx_audit_log_created ON mapping_audit_log(created_at);
```

**Column Details:**

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Auto-increment primary key |
| `mapping_id` | INTEGER | FK to user_market_mappings, nullable (for deleted) |
| `canonical_id` | VARCHAR(100) | Mapping canonical_id (preserved even if FK deleted) |
| `action` | VARCHAR(20) | One of: CREATE, UPDATE, DELETE, ACTIVATE, DEACTIVATE |
| `old_value` | JSONB | Previous state (null for CREATE) |
| `new_value` | JSONB | New state (null for DELETE) |
| `reason` | TEXT | Optional explanation for the change |
| `created_at` | TIMESTAMPTZ | When action occurred |
| `created_by` | VARCHAR(100) | User who made the change |

### 1.3 unmapped_market_log

Persists unmapped markets discovered during scraping for analysis.

```sql
CREATE TABLE unmapped_market_log (
    id SERIAL PRIMARY KEY,
    source VARCHAR(20) NOT NULL,
    external_market_id VARCHAR(100) NOT NULL,
    market_name VARCHAR(255),
    sample_outcomes JSONB,
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    occurrence_count INTEGER DEFAULT 1,
    status VARCHAR(20) DEFAULT 'NEW',
    notes TEXT,
    UNIQUE(source, external_market_id)
);

-- Indexes
CREATE INDEX idx_unmapped_source ON unmapped_market_log(source);
CREATE INDEX idx_unmapped_status ON unmapped_market_log(status);
CREATE INDEX idx_unmapped_occurrences ON unmapped_market_log(occurrence_count DESC);
CREATE INDEX idx_unmapped_last_seen ON unmapped_market_log(last_seen_at DESC);
```

**Column Details:**

| Column | Type | Description |
|--------|------|-------------|
| `id` | SERIAL | Auto-increment primary key |
| `source` | VARCHAR(20) | Platform: "sportybet" or "bet9ja" |
| `external_market_id` | VARCHAR(100) | Platform's market ID |
| `market_name` | VARCHAR(255) | Market name from platform (if available) |
| `sample_outcomes` | JSONB | Example outcome structure for reference |
| `first_seen_at` | TIMESTAMPTZ | When first encountered |
| `last_seen_at` | TIMESTAMPTZ | When last encountered |
| `occurrence_count` | INTEGER | How many times seen (for prioritization) |
| `status` | VARCHAR(20) | NEW, ACKNOWLEDGED, MAPPED, IGNORED |
| `notes` | TEXT | Admin notes about the market |

**Unique Constraint:** (source, external_market_id) prevents duplicate entries per platform.

---

## 2. Runtime Merge Strategy

### 2.1 Load Order

```
┌─────────────────────────────────────────────────────────────────┐
│                    Application Startup                          │
├─────────────────────────────────────────────────────────────────┤
│  1. Load code MARKET_MAPPINGS (tuple from market_ids.py)        │
│                           ↓                                     │
│  2. Load DB user_market_mappings WHERE is_active = TRUE         │
│                           ↓                                     │
│  3. Merge: DB overrides code on matching canonical_id           │
│                           ↓                                     │
│  4. Build lookup indexes (by_betpawa, by_sportybet, by_bet9ja)  │
│                           ↓                                     │
│  5. Cache merged result in memory                               │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Merge Rules

| Scenario | Behavior |
|----------|----------|
| Code-only mapping | Use code mapping |
| DB-only mapping | Use DB mapping |
| Both exist (same canonical_id) | DB overrides code |
| DB mapping with is_active=false | Excluded from merged set |
| Multiple DB mappings, same betpawa_id | Higher priority wins |

### 2.3 Cache Implementation

```python
# src/market_mapping/cache.py

from dataclasses import dataclass
from typing import Dict, Optional
import asyncio

@dataclass(frozen=True)
class CachedMapping:
    """Immutable cached mapping for thread-safe access."""
    canonical_id: str
    name: str
    betpawa_id: Optional[str]
    sportybet_id: Optional[str]
    bet9ja_key: Optional[str]
    outcome_mapping: tuple  # Frozen tuple of OutcomeMapping
    source: str  # "code" or "db"
    priority: int

class MappingCache:
    """Thread-safe in-memory mapping cache with hot reload."""

    def __init__(self):
        self._mappings: Dict[str, CachedMapping] = {}
        self._by_betpawa: Dict[str, CachedMapping] = {}
        self._by_sportybet: Dict[str, CachedMapping] = {}
        self._by_bet9ja: Dict[str, CachedMapping] = {}
        self._lock = asyncio.Lock()
        self._loaded_at: Optional[datetime] = None

    async def load(self, session: AsyncSession) -> int:
        """Load and merge mappings from code and DB."""
        async with self._lock:
            # 1. Start with code mappings
            merged = {m.canonical_id: self._from_code(m)
                      for m in MARKET_MAPPINGS}

            # 2. Load DB mappings
            result = await session.execute(
                select(UserMarketMapping)
                .where(UserMarketMapping.is_active == True)
            )
            db_mappings = result.scalars().all()

            # 3. Merge: DB overrides code
            for db_map in db_mappings:
                merged[db_map.canonical_id] = self._from_db(db_map)

            # 4. Build indexes
            self._mappings = merged
            self._by_betpawa = {m.betpawa_id: m for m in merged.values()
                               if m.betpawa_id}
            self._by_sportybet = {m.sportybet_id: m for m in merged.values()
                                  if m.sportybet_id}
            self._by_bet9ja = {m.bet9ja_key: m for m in merged.values()
                              if m.bet9ja_key}
            self._loaded_at = datetime.utcnow()

            return len(merged)

    def find_by_betpawa_id(self, id: str) -> Optional[CachedMapping]:
        return self._by_betpawa.get(id)

    def find_by_sportybet_id(self, id: str) -> Optional[CachedMapping]:
        return self._by_sportybet.get(id)

    def find_by_bet9ja_key(self, key: str) -> Optional[CachedMapping]:
        # Handle key prefix matching for Bet9ja
        for prefix, mapping in self._by_bet9ja.items():
            if key.startswith(prefix):
                return mapping
        return None
```

### 2.4 Hot Reload

Cache reload triggered by:
1. POST /api/mappings/reload endpoint
2. After any CRUD operation on user_market_mappings
3. Optionally via scheduler (e.g., every 5 minutes)

```python
# In API router
@router.post("/mappings/reload")
async def reload_mappings(db: AsyncSession = Depends(get_db)):
    count = await mapping_cache.load(db)
    return {"status": "ok", "mapping_count": count}
```

---

## 3. API Contract Specification

### 3.1 CRUD Endpoints

#### GET /api/mappings

List all mappings (merged view of code + DB).

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `source` | string | Filter by source: "code", "db", or omit for all |
| `is_active` | boolean | Filter by active status (DB only) |
| `search` | string | Search in canonical_id and name |
| `platform` | string | Filter by platform support: "betpawa", "sportybet", "bet9ja" |
| `page` | integer | Page number (default 1) |
| `page_size` | integer | Items per page (default 50, max 100) |

**Response: MappingListResponse**
```json
{
  "items": [
    {
      "canonicalId": "1x2_ft",
      "name": "1X2 - Full Time",
      "betpawaId": "3743",
      "sportybetId": "1",
      "bet9jaKey": "S_1X2",
      "outcomeCount": 3,
      "source": "code",
      "isActive": true,
      "priority": 0
    }
  ],
  "total": 129,
  "page": 1,
  "pageSize": 50
}
```

#### GET /api/mappings/{canonical_id}

Get single mapping with full details.

**Response: MappingDetailResponse**
```json
{
  "canonicalId": "1x2_ft",
  "name": "1X2 - Full Time",
  "betpawaId": "3743",
  "sportybetId": "1",
  "bet9jaKey": "S_1X2",
  "outcomeMapping": [
    {
      "canonicalId": "home",
      "betpawaName": "1",
      "sportybetDesc": "Home",
      "bet9jaSuffix": "1",
      "position": 0
    }
  ],
  "source": "code",
  "isActive": true,
  "priority": 0,
  "createdAt": "2026-01-20T00:00:00Z",
  "updatedAt": null
}
```

#### POST /api/mappings

Create new user mapping.

**Request: CreateMappingRequest**
```json
{
  "canonicalId": "user_1x2_variant",
  "name": "1X2 Variant (User Defined)",
  "betpawaId": "9999",
  "sportybetId": "999",
  "bet9jaKey": "S_CUSTOM",
  "outcomeMapping": [
    {
      "canonicalId": "home",
      "betpawaName": "1",
      "sportybetDesc": "Home",
      "bet9jaSuffix": "1",
      "position": 0
    }
  ],
  "priority": 10,
  "reason": "Custom mapping for new market type"
}
```

**Response:** 201 Created with MappingDetailResponse

**Side Effects:**
- Creates audit log entry (action: CREATE)
- Triggers cache reload

#### PATCH /api/mappings/{canonical_id}

Update existing user mapping (partial update).

**Request: UpdateMappingRequest**
```json
{
  "name": "Updated Name",
  "sportybetId": "999",
  "reason": "Corrected SportyBet ID"
}
```

**Response:** MappingDetailResponse

**Side Effects:**
- Creates audit log entry (action: UPDATE) with old/new values
- Triggers cache reload

**Error:** 400 if attempting to update code-only mapping

#### DELETE /api/mappings/{canonical_id}

Soft delete (deactivate) user mapping.

**Response:** 204 No Content

**Side Effects:**
- Sets is_active = false
- Creates audit log entry (action: DEACTIVATE)
- Triggers cache reload

**Error:** 400 if attempting to delete code-only mapping

### 3.2 Discovery Endpoints

#### GET /api/mappings/unmapped

List unmapped markets discovered during scraping.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `source` | string | Filter by platform |
| `status` | string | Filter by status: NEW, ACKNOWLEDGED, MAPPED, IGNORED |
| `min_occurrences` | integer | Minimum occurrence count |
| `sort_by` | string | Sort field: occurrence_count, last_seen_at, first_seen_at |
| `sort_order` | string | asc or desc (default desc) |
| `page` | integer | Page number |
| `page_size` | integer | Items per page |

**Response: UnmappedMarketListResponse**
```json
{
  "items": [
    {
      "id": 1,
      "source": "sportybet",
      "externalMarketId": "800117",
      "marketName": "Player to be Booked",
      "sampleOutcomes": [{"name": "Yes", "odds": 1.85}],
      "firstSeenAt": "2026-02-02T10:00:00Z",
      "lastSeenAt": "2026-02-13T15:30:00Z",
      "occurrenceCount": 302395,
      "status": "NEW"
    }
  ],
  "total": 150,
  "page": 1,
  "pageSize": 50
}
```

#### GET /api/mappings/unmapped/{id}

Get unmapped market details with sample data.

**Response: UnmappedMarketDetailResponse**
```json
{
  "id": 1,
  "source": "sportybet",
  "externalMarketId": "800117",
  "marketName": "Player to be Booked",
  "sampleOutcomes": [
    {"name": "C. Palmer - Yes", "odds": 2.50},
    {"name": "C. Palmer - No", "odds": 1.45}
  ],
  "firstSeenAt": "2026-02-02T10:00:00Z",
  "lastSeenAt": "2026-02-13T15:30:00Z",
  "occurrenceCount": 302395,
  "status": "NEW",
  "notes": null
}
```

#### PATCH /api/mappings/unmapped/{id}

Update unmapped market status or notes.

**Request:**
```json
{
  "status": "ACKNOWLEDGED",
  "notes": "Player prop - BetPawa doesn't offer"
}
```

**Response:** UnmappedMarketDetailResponse

### 3.3 Analysis Endpoints

#### GET /api/mappings/stats

Get coverage statistics.

**Response: MappingStatsResponse**
```json
{
  "totalMappings": 135,
  "codeMappings": 129,
  "dbMappings": 6,
  "activeMappings": 133,
  "platforms": {
    "betpawa": {"total": 120, "unique": 120},
    "sportybet": {"total": 115, "unique": 110},
    "bet9ja": {"total": 90, "unique": 85}
  },
  "unmapped": {
    "total": 150,
    "byStatus": {
      "NEW": 120,
      "ACKNOWLEDGED": 20,
      "MAPPED": 5,
      "IGNORED": 5
    },
    "byPlatform": {
      "sportybet": 80,
      "bet9ja": 70
    }
  },
  "lastReloadAt": "2026-02-13T15:30:00Z"
}
```

#### GET /api/mappings/audit-log

Get audit history for mappings.

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| `mapping_id` | integer | Filter by specific mapping |
| `canonical_id` | string | Filter by canonical_id |
| `action` | string | Filter by action type |
| `from_date` | datetime | Start of date range |
| `to_date` | datetime | End of date range |
| `page` | integer | Page number |
| `page_size` | integer | Items per page |

**Response: AuditLogListResponse**
```json
{
  "items": [
    {
      "id": 1,
      "mappingId": 5,
      "canonicalId": "user_1x2_variant",
      "action": "CREATE",
      "oldValue": null,
      "newValue": {"name": "1X2 Variant", "betpawaId": "9999"},
      "reason": "Custom mapping for new market",
      "createdAt": "2026-02-13T14:00:00Z",
      "createdBy": "admin"
    }
  ],
  "total": 25,
  "page": 1,
  "pageSize": 50
}
```

---

## 4. Pydantic Schemas (Outline)

### 4.1 File: src/api/schemas/mappings.py

```python
"""Pydantic schemas for market mapping API.

Schemas follow project conventions:
- ConfigDict with from_attributes for ORM compat
- alias_generator=to_camel for frontend camelCase
- populate_by_name=True for both case support
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


# === Outcome Mapping ===

class OutcomeMappingSchema(BaseModel):
    """Single outcome mapping within a market."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    canonical_id: str = Field(description="Canonical outcome identifier")
    betpawa_name: Optional[str] = Field(default=None)
    sportybet_desc: Optional[str] = Field(default=None)
    bet9ja_suffix: Optional[str] = Field(default=None)
    position: int = Field(description="Display order position")


# === Mapping Responses ===

class MappingListItem(BaseModel):
    """Summary item for mapping list."""
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    canonical_id: str
    name: str
    betpawa_id: Optional[str]
    sportybet_id: Optional[str]
    bet9ja_key: Optional[str]
    outcome_count: int
    source: str  # "code" or "db"
    is_active: bool
    priority: int


class MappingListResponse(BaseModel):
    """Paginated list of mappings."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: list[MappingListItem]
    total: int
    page: int
    page_size: int


class MappingDetailResponse(BaseModel):
    """Full mapping details."""
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    canonical_id: str
    name: str
    betpawa_id: Optional[str]
    sportybet_id: Optional[str]
    bet9ja_key: Optional[str]
    outcome_mapping: list[OutcomeMappingSchema]
    source: str
    is_active: bool
    priority: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]


# === Mapping Requests ===

class CreateMappingRequest(BaseModel):
    """Create new user mapping."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    canonical_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=255)
    betpawa_id: Optional[str] = Field(default=None, max_length=50)
    sportybet_id: Optional[str] = Field(default=None, max_length=50)
    bet9ja_key: Optional[str] = Field(default=None, max_length=50)
    outcome_mapping: list[OutcomeMappingSchema]
    priority: int = Field(default=0, ge=0, le=100)
    reason: Optional[str] = Field(default=None, max_length=500)


class UpdateMappingRequest(BaseModel):
    """Partial update for user mapping."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    name: Optional[str] = Field(default=None, max_length=255)
    betpawa_id: Optional[str] = Field(default=None, max_length=50)
    sportybet_id: Optional[str] = Field(default=None, max_length=50)
    bet9ja_key: Optional[str] = Field(default=None, max_length=50)
    outcome_mapping: Optional[list[OutcomeMappingSchema]] = None
    priority: Optional[int] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None
    reason: Optional[str] = Field(default=None, max_length=500)


# === Unmapped Market Schemas ===

class UnmappedMarketListItem(BaseModel):
    """Summary item for unmapped market list."""
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int
    source: str
    external_market_id: str
    market_name: Optional[str]
    first_seen_at: datetime
    last_seen_at: datetime
    occurrence_count: int
    status: str


class UnmappedMarketListResponse(BaseModel):
    """Paginated list of unmapped markets."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: list[UnmappedMarketListItem]
    total: int
    page: int
    page_size: int


class UnmappedMarketDetailResponse(BaseModel):
    """Full unmapped market details."""
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int
    source: str
    external_market_id: str
    market_name: Optional[str]
    sample_outcomes: Optional[dict]
    first_seen_at: datetime
    last_seen_at: datetime
    occurrence_count: int
    status: str
    notes: Optional[str]


class UpdateUnmappedRequest(BaseModel):
    """Update unmapped market status."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: Optional[str] = Field(default=None, pattern="^(NEW|ACKNOWLEDGED|MAPPED|IGNORED)$")
    notes: Optional[str] = Field(default=None, max_length=1000)


# === Stats Schemas ===

class PlatformStats(BaseModel):
    """Stats for a single platform."""
    total: int
    unique: int


class UnmappedStats(BaseModel):
    """Unmapped market statistics."""
    total: int
    by_status: dict[str, int]
    by_platform: dict[str, int]


class MappingStatsResponse(BaseModel):
    """Overall mapping statistics."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total_mappings: int
    code_mappings: int
    db_mappings: int
    active_mappings: int
    platforms: dict[str, PlatformStats]
    unmapped: UnmappedStats
    last_reload_at: Optional[datetime]


# === Audit Log Schemas ===

class AuditLogItem(BaseModel):
    """Single audit log entry."""
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    id: int
    mapping_id: Optional[int]
    canonical_id: str
    action: str
    old_value: Optional[dict]
    new_value: Optional[dict]
    reason: Optional[str]
    created_at: datetime
    created_by: Optional[str]


class AuditLogListResponse(BaseModel):
    """Paginated audit log."""
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    items: list[AuditLogItem]
    total: int
    page: int
    page_size: int
```

---

## 5. Implementation Phases

### Phase 101: Database Foundation
- Alembic migration for 3 tables
- SQLAlchemy models
- Basic CRUD repository

### Phase 102: Mapping Cache
- MappingCache implementation
- Hot reload mechanism
- Integration with existing mappers

### Phase 103: CRUD API
- GET/POST/PATCH/DELETE endpoints
- Audit logging
- Cache invalidation

### Phase 104: Discovery API
- Unmapped market logging during scrape
- Discovery endpoints
- Status management

### Phase 105: Analysis API
- Stats endpoint
- Audit log endpoint
- Integration with frontend

### Phase 106: Frontend UI
- Mapping list/detail views
- Create/edit forms
- Unmapped market discovery UI

---

*Design Document v1.0 - 2026-02-13*
