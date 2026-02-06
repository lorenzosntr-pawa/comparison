# 58-01 WebSocket Hooks - Summary

## Objective

Create React hooks for WebSocket communication with the backend.

## Tasks Completed

### Task 1: Create core useWebSocket hook
**Commit:** `5934c58` feat(58-01): create core useWebSocket hook

Created `web/src/hooks/use-websocket.ts` with:
- Connection management to `/api/ws` with optional topics query param
- WebSocket lifecycle handling (connecting, connected, disconnected, error states)
- Auto-reconnect with exponential backoff (1s, 2s, 4s, 8s, max 30s, max 10 retries)
- Ping/pong keepalive (ping every 30s, expect pong within 5s)
- Message envelope parsing (`{type, timestamp, data}`)
- Internal handling of `connection_ack` and `pong` messages
- Clean cleanup on unmount

Exported types:
- `WebSocketState`: 'connecting' | 'connected' | 'disconnected' | 'error'
- `WebSocketMessage<T>`: Message envelope interface
- `UseWebSocketOptions<T>`: Hook options (topics, onMessage, enabled, onError)
- `UseWebSocketReturn`: Hook return type (state, send, error)

### Task 2: Create useWebSocketScrapeProgress hook
**Commit:** `17dda21` feat(58-01): create useWebSocketScrapeProgress hook

Created `web/src/hooks/use-websocket-scrape-progress.ts` with:
- Subscribes to `scrape_progress` topic
- Matches existing SSE hook interface for drop-in replacement:
  - `isConnected: boolean`
  - `currentProgress: ScrapeProgressEvent | null`
  - `platformProgress: Map<string, PlatformProgress>`
  - `overallPhase: string`
  - `error: string | null`
- Updates platform progress map on platform-specific events
- Invalidates `scheduler-history`, `events`, and `scrape-run` queries on completion/failure
- Supports `onComplete` callback

Created `web/src/hooks/index.ts` exporting both hooks and existing `useIsMobile`.

### Lint Fixes
**Commit:** `1d24bdd` fix(58-01): fix linting issues in WebSocket hooks

Fixed linting issues:
- Used ref pattern to avoid circular callback dependencies in `scheduleReconnect`/`connect`
- Derived `overallPhase` via `useMemo` instead of `setState` in effect
- Added eslint-disable for legitimate external system connection in useEffect

## Verification

- [x] `npm run build` in web/ succeeds without TypeScript errors
- [x] `npm run lint` passes for hook files (pre-existing errors in other files)
- [x] `useWebSocket` connects to `/api/ws` and handles lifecycle
- [x] `useWebSocketScrapeProgress` provides same interface as SSE hooks

## Files Created/Modified

- `web/src/hooks/use-websocket.ts` (new)
- `web/src/hooks/use-websocket-scrape-progress.ts` (new)
- `web/src/hooks/index.ts` (new)

## Next Steps

Phase 58-02 will integrate these hooks into dashboard pages, replacing SSE-based progress tracking with WebSocket-based real-time updates.
