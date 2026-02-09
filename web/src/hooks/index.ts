// Core WebSocket hook
export {
  useWebSocket,
  type WebSocketState,
  type WebSocketMessage,
  type UseWebSocketOptions,
  type UseWebSocketReturn,
} from './use-websocket'

// Scrape progress WebSocket hook
export {
  useWebSocketScrapeProgress,
  type ScrapeProgressEvent,
  type PlatformProgress,
  type UseWebSocketScrapeProgressOptions,
  type UseWebSocketScrapeProgressReturn,
} from './use-websocket-scrape-progress'

// Odds updates WebSocket hook
export {
  useOddsUpdates,
  type OddsUpdateData,
  type UseOddsUpdatesOptions,
  type UseOddsUpdatesReturn,
} from './use-odds-updates'

// Mobile detection hook
export { useIsMobile } from './use-mobile.tsx'
