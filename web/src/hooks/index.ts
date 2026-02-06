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

// Mobile detection hook
export { useIsMobile } from './use-mobile.tsx'
