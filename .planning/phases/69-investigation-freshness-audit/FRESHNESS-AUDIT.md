# Odds Freshness Audit

## Executive Summary

The odds freshness architecture has a fundamental disconnect between cache and database timestamps. The cache stores `captured_at` as the current scrape time (always fresh), while the database stores `captured_at` as the time odds **last changed** (can be hours old). The API uses `captured_at` for `snapshot_time`, causing data to appear stale when served from DB (warmup, cache misses). Additionally, the `last_confirmed_at` field was added for freshness tracking but is never exposed in the API. The WebSocket infrastructure for real-time updates exists but the frontend doesn't subscribe to odds update messages - it only invalidates queries on scrape completion, not on individual odds changes.

---

## Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            SCRAPING PHASE                                     │
│  event_coordinator.py                                                         │
│                                                                               │
│  1. Scrape all platforms in parallel                                         │
│  2. Change detection: compare against cache                                   │
│     └─ markets_changed() → classifies as CHANGED or UNCHANGED                │
│                                                                               │
│  3. Create WriteData DTOs with market data                                   │
└─────────────────────────────────────────────────────────────────────────────┬┘
                                                                              │
                              ┌───────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            CACHE UPDATE                                       │
│  odds_cache.py (immediate, before DB write)                                  │
│                                                                               │
│  put_betpawa_snapshot() / put_competitor_snapshot()                          │
│    └─ captured_at = now_naive  ← ALWAYS FRESH (current scrape time)          │
│    └─ _notify_update() → fires for ALL puts (changed + unchanged)            │
│                                                                               │
│  ⚡ WebSocket callback triggered: on_cache_update()                          │
│     └─ Broadcasts odds_update message to "odds_updates" topic                │
└─────────────────────────────────────────────────────────────────────────────┬┘
                                                                              │
                              ┌───────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            ASYNC WRITE QUEUE                                  │
│  write_queue.py → write_handler.py (async, delayed)                          │
│                                                                               │
│  FOR CHANGED DATA (INSERT new snapshot row):                                 │
│    ├─ captured_at = server_default=func.now()  ← SET BY DATABASE             │
│    └─ last_confirmed_at = now                                                │
│                                                                               │
│  FOR UNCHANGED DATA (UPDATE existing row):                                   │
│    ├─ captured_at = UNCHANGED (from original INSERT)                         │
│    └─ last_confirmed_at = now  ← UPDATED EVERY SCRAPE                       │
└─────────────────────────────────────────────────────────────────────────────┬┘
                                                                              │
                              ┌───────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            API READ PATH                                      │
│  events.py                                                                    │
│                                                                               │
│  _load_snapshots_cached():                                                   │
│    1. Try cache first → get CachedSnapshot                                   │
│    2. On cache miss → fall back to DB query                                  │
│                                                                               │
│  snapshot_time = snapshot.captured_at                                        │
│    └─ From CACHE: always fresh (time of last scrape)                         │
│    └─ From DB: time of last CHANGE (can be stale)                           │
│                                                                               │
│  ❌ last_confirmed_at is NEVER used in API response                          │
└─────────────────────────────────────────────────────────────────────────────┬┘
                                                                              │
                              ┌───────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND                                           │
│                                                                               │
│  useWebSocketScrapeProgress():                                               │
│    └─ Subscribes to: "scrape_progress" only                                  │
│    └─ Invalidates queries on: 'completed' or 'failed' phase                  │
│                                                                               │
│  ❌ NO subscription to "odds_updates" topic                                   │
│  ❌ NO handler for odds_update messages                                       │
│                                                                               │
│  useMatches / useMatchDetail:                                                │
│    └─ refetchInterval: 60000ms (polls every 60 seconds)                      │
│    └─ staleTime: 30000ms (30 seconds)                                        │
│                                                                               │
│  formatRelativeTime(snapshot_time):                                          │
│    └─ Displays "Xm ago" based on captured_at                                 │
│    └─ Can show "4h ago" for unchanged odds (DB source)                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Timestamp Inventory

| Field | Location | Set When | Updated When | Used For | Issues |
|-------|----------|----------|--------------|----------|--------|
| `captured_at` | OddsSnapshot (DB) | INSERT via `server_default=func.now()` | Never - only on INSERT | API `snapshot_time` | Shows when data CHANGED, not when last scraped |
| `captured_at` | CachedSnapshot (memory) | Cache put (`now_naive`) | Every cache put | API `snapshot_time` (cache path) | Always fresh, but inconsistent with DB |
| `last_confirmed_at` | OddsSnapshot (DB) | INSERT (`now`) | Every scrape (UPDATE for unchanged) | **NOT USED** | Added for freshness but never exposed |
| `snapshot_time` | API response | From `snapshot.captured_at` | N/A | Frontend display | Source varies (cache vs DB) |

---

## Staleness Sources

### CRITICAL

#### 1. **Cache/DB Timestamp Inconsistency**
- **Location**: `event_coordinator.py:1462`, `write_handler.py:90-96`
- **Issue**: Cache stores `captured_at = now_naive` (fresh), but DB stores via `server_default` (only on INSERT). When cache warms from DB, timestamps become stale.
- **Impact**: After app restart or cache miss, `snapshot_time` can show hours-old timestamps even though data was just scraped and confirmed unchanged.
- **User experience**: "Updated 4h ago" when odds were actually verified 30 seconds ago.
- **Severity**: CRITICAL - directly causes stale appearance

#### 2. **API Uses `captured_at` Instead of `last_confirmed_at`**
- **Location**: `events.py:194,200,488,598,665,718,743`
- **Issue**: API returns `snapshot_time = snapshot.captured_at` instead of `last_confirmed_at`
- **Impact**: `last_confirmed_at` is updated every scrape but never exposed to users
- **User experience**: Frontend shows when odds changed, not when they were last verified
- **Severity**: CRITICAL - the fix exists (last_confirmed_at) but isn't used

### HIGH

#### 3. **Frontend Doesn't Subscribe to `odds_updates` Topic**
- **Location**: `use-websocket-scrape-progress.ts:130`
- **Issue**: Only subscribes to `['scrape_progress']`, not `['odds_updates']`
- **Impact**: WebSocket broadcasts odds updates but frontend ignores them
- **User experience**: Data only refreshes on 60s poll or scrape completion, not on individual odds changes
- **Severity**: HIGH - real-time infrastructure exists but unused

#### 4. **No Query Invalidation on odds_update Messages**
- **Location**: `use-websocket-scrape-progress.ts:110-117`
- **Issue**: Query invalidation only triggers on scrape `completed`/`failed`, not on `odds_update`
- **Impact**: Even if frontend subscribed to odds_updates, there's no handler to refresh data
- **Severity**: HIGH - prevents real-time updates

### MEDIUM

#### 5. **60-Second Polling Interval for Match Data**
- **Location**: `use-matches.ts:33`, `use-match-detail.ts:11`
- **Issue**: `refetchInterval: 60000` means up to 60 seconds before UI shows new odds
- **Impact**: With real-time WebSocket available, polling is unnecessarily slow
- **Severity**: MEDIUM - acceptable with WebSocket working, poor without

#### 6. **Cache Warmup Loads Stale `captured_at` from DB**
- **Location**: `warmup.py:185`
- **Issue**: `snapshot_to_cached()` uses `snapshot.captured_at` from DB
- **Impact**: After restart, cache starts with stale timestamps until first scrape
- **Severity**: MEDIUM - transient issue, resolves after first scrape cycle

### LOW

#### 7. **CachedSnapshot Doesn't Store `last_confirmed_at`**
- **Location**: `odds_cache.py:45-59`
- **Issue**: CachedSnapshot only has `captured_at`, not `last_confirmed_at`
- **Impact**: Even if API wanted to use `last_confirmed_at`, cache can't provide it
- **Severity**: LOW - requires schema change if we want cache-path freshness

---

## Recommended Fixes

### Phase 70: Backend Freshness Fixes

| Issue | Fix | Complexity |
|-------|-----|------------|
| #1 Cache/DB inconsistency | **Option A**: Use `last_confirmed_at` in API (simple) **Option B**: Set `captured_at` explicitly in write_handler (more complex) | Low/Medium |
| #2 API uses captured_at | Change `events.py` to use `last_confirmed_at` for `snapshot_time` | Low |
| #7 Cache lacks last_confirmed_at | Add `last_confirmed_at` to CachedSnapshot if needed | Medium |

**Recommended approach**: Use `last_confirmed_at` in API. It's already updated every scrape and represents "when we last verified this data" - exactly what users want to see.

### Phase 71: Frontend Freshness Fixes

| Issue | Fix | Complexity |
|-------|-----|------------|
| #3 No odds_updates subscription | Add `odds_updates` topic to WebSocket subscription | Low |
| #4 No query invalidation | Add handler for `odds_update` messages that invalidates affected event queries | Medium |
| #5 60-second polling | Reduce poll interval OR remove polling when WebSocket connected | Low |

**Recommended approach**:
1. Create new hook `useOddsUpdates()` that subscribes to `odds_updates` topic
2. On `odds_update` message, invalidate queries for affected `event_ids`
3. Keep polling as fallback but reduce interval when WebSocket connected

---

## Verification Checklist

### Backend Verification

- [ ] **API returns fresh timestamps**: After scrape, API should return timestamps within 2 minutes of current time, regardless of whether odds changed
- [ ] **Cache warmup uses correct field**: After restart, `snapshot_time` should reflect last scrape time, not last change time
- [ ] **Check logs**: `cache.warmup.complete` should log correct snapshot counts
- [ ] **Test cache miss path**: Evict specific event from cache, verify API still returns correct timestamp

### Frontend Verification

- [ ] **WebSocket shows `odds_update` messages**: Check browser DevTools WebSocket frames for `type: "odds_update"` messages
- [ ] **Query invalidation on odds change**: After scrape with changed odds, verify TanStack Query DevTools shows query invalidation
- [ ] **Real-time UI update**: Change odds on one platform, verify UI updates within 5 seconds (not 60)
- [ ] **Fallback polling works**: Disconnect WebSocket, verify data still refreshes on 60s interval

### End-to-End Test

1. Note current `snapshot_time` for an event (e.g., "2m ago")
2. Wait for next scrape cycle (odds unchanged)
3. Verify `snapshot_time` updates to show recent time (e.g., "10s ago")
4. **Currently fails**: Shows old time like "4h ago" when served from DB

---

## Key Logs to Monitor

| Log Message | Location | What to Check |
|-------------|----------|---------------|
| `cache.warmup.complete` | warmup.py | Snapshot counts after restart |
| `snapshot_loading` | events.py | `cache_hits` vs `cache_misses` |
| `change_detection.classify` | change_detection.py | `betpawa_changed` vs `betpawa_unchanged` counts |
| `ws.cache_bridge.registered` | bridge.py | WebSocket bridge is connected |
| `[useWebSocket] Connection acknowledged` | Browser console | Frontend WebSocket connected with correct topics |

---

## Summary

The freshness issue stems from a fundamental design mismatch:

1. **The cache is right**: It stores `captured_at` as the time data was last scraped (fresh)
2. **The DB is right**: It stores `captured_at` as the time data last changed (for history)
3. **The API is wrong**: It uses `captured_at` when it should use `last_confirmed_at`

The `last_confirmed_at` field already exists and is already updated every scrape cycle. The fix is simply to expose it in the API response instead of `captured_at`.

Additionally, the real-time WebSocket infrastructure is fully built on the backend but not connected on the frontend. Subscribing to `odds_updates` and invalidating queries would enable true real-time updates.
