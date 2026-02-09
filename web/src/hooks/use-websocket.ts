/**
 * Core WebSocket hook for real-time communication with the backend.
 *
 * @module use-websocket
 * @description Provides a robust WebSocket connection to the FastAPI backend's `/api/ws`
 * endpoint with automatic reconnection, exponential backoff, and ping/pong keepalive.
 * Supports topic-based subscriptions for filtering messages.
 *
 * Features:
 * - Auto-reconnect with exponential backoff (up to 10 retries)
 * - Ping/pong keepalive every 30 seconds
 * - Type-safe message handling with generics
 * - Clean cleanup on component unmount
 * - Reconnection callback for state synchronization
 *
 * @example
 * ```typescript
 * import { useWebSocket, type WebSocketMessage } from '@/hooks/use-websocket'
 *
 * interface MyData {
 *   id: number
 *   value: string
 * }
 *
 * function MyComponent() {
 *   const { state, send, reconnect } = useWebSocket<MyData>({
 *     topics: ['my_topic'],
 *     onMessage: (message) => {
 *       console.log('Received:', message.data)
 *     },
 *     onReconnect: () => {
 *       // Invalidate caches or refresh state
 *     },
 *   })
 *
 *   return <div>Status: {state}</div>
 * }
 * ```
 */

import { useEffect, useRef, useCallback, useState } from 'react'

/**
 * WebSocket connection state.
 *
 * @description Represents the current state of the WebSocket connection.
 * - 'connecting': Initial connection in progress
 * - 'connected': Successfully connected
 * - 'disconnected': Not connected (initial or after close)
 * - 'error': Connection failed (check error property for details)
 */
export type WebSocketState = 'connecting' | 'connected' | 'disconnected' | 'error'

/**
 * WebSocket message envelope structure.
 *
 * @description All messages from the backend are wrapped in this envelope
 * containing message type, timestamp, and payload data.
 *
 * @template T - The type of the data payload
 */
export interface WebSocketMessage<T = unknown> {
  /** Message type identifier (e.g., 'scrape_progress', 'odds_update') */
  type: string
  /** ISO timestamp when message was sent */
  timestamp: string
  /** Message payload */
  data: T
}

/**
 * Configuration options for the useWebSocket hook.
 *
 * @template T - The expected message data type
 */
export interface UseWebSocketOptions<T = unknown> {
  /** Topics to subscribe to (passed as query param, e.g., ['scrape_progress', 'odds_updates']) */
  topics?: string[]
  /** Callback for incoming messages (excluding internal pong/connection_ack) */
  onMessage?: (message: WebSocketMessage<T>) => void
  /** Whether to connect (default: true). Set to false to disable the connection. */
  enabled?: boolean
  /** Callback for error messages from server */
  onError?: (code: string, detail: string) => void
  /** Callback fired when connection re-establishes after a disconnect (not on initial connect). Use for cache invalidation. */
  onReconnect?: () => void
}

/**
 * Return value from the useWebSocket hook.
 *
 * @description Provides connection state, messaging capability, and manual reconnection control.
 */
export interface UseWebSocketReturn {
  /** Current connection state */
  state: WebSocketState
  /** Send a JSON-serializable message to the server. No-op if not connected. */
  send: (message: unknown) => void
  /** Last error message (populated when state is 'error') */
  error: string | null
  /** Manually trigger reconnection. Clears timers, resets retry state, and initiates new connection. */
  reconnect: () => void
}

// ─────────────────────────────────────────────────────────────────────────────
// Configuration Constants
// ─────────────────────────────────────────────────────────────────────────────

/** Initial delay before first reconnection attempt (ms) */
const INITIAL_RECONNECT_DELAY = 1000
/** Maximum delay between reconnection attempts (ms) */
const MAX_RECONNECT_DELAY = 30000
/** Maximum number of reconnection attempts before giving up */
const MAX_RETRIES = 10

/** Interval between ping messages (ms) */
const PING_INTERVAL = 30000
/** Timeout waiting for pong response before considering connection dead (ms) */
const PONG_TIMEOUT = 5000

/**
 * Core WebSocket hook for connecting to /api/ws with topic-based subscriptions.
 *
 * @description Establishes and maintains a WebSocket connection to the backend,
 * handling reconnection, keepalive, and message routing automatically.
 *
 * @template T - The expected type of message data payloads
 * @param options - Configuration options for the WebSocket connection
 * @returns Object containing connection state and control methods
 *
 * @example
 * ```typescript
 * const { state, send, error, reconnect } = useWebSocket({
 *   topics: ['scrape_progress'],
 *   onMessage: (msg) => console.log(msg),
 *   onReconnect: () => queryClient.invalidateQueries(),
 * })
 * ```
 */
export function useWebSocket<T = unknown>(
  options: UseWebSocketOptions<T> = {}
): UseWebSocketReturn {
  const { topics, onMessage, enabled = true, onError, onReconnect } = options

  const [state, setState] = useState<WebSocketState>('disconnected')
  const [error, setError] = useState<string | null>(null)

  // Refs to avoid effect dependencies and circular callback issues
  const wsRef = useRef<WebSocket | null>(null)
  const pingIntervalRef = useRef<number | null>(null)
  const pongTimeoutRef = useRef<number | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const stableConnectionTimeoutRef = useRef<number | null>(null)
  const reconnectDelayRef = useRef(INITIAL_RECONNECT_DELAY)
  const retriesRef = useRef(0)
  const mountedRef = useRef(true)
  const topicsRef = useRef(topics)
  // Track whether we had a previous successful connection (for detecting reconnection)
  const wasConnectedRef = useRef(false)

  // Keep topics ref updated
  useEffect(() => {
    topicsRef.current = topics
  }, [topics])

  // Stable refs for callbacks
  const onMessageRef = useRef(onMessage)
  const onErrorRef = useRef(onError)
  const onReconnectRef = useRef(onReconnect)
  useEffect(() => {
    onMessageRef.current = onMessage
    onErrorRef.current = onError
    onReconnectRef.current = onReconnect
  }, [onMessage, onError, onReconnect])

  // Clear all timers
  const clearTimers = useCallback(() => {
    if (pingIntervalRef.current !== null) {
      window.clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = null
    }
    if (pongTimeoutRef.current !== null) {
      window.clearTimeout(pongTimeoutRef.current)
      pongTimeoutRef.current = null
    }
    if (reconnectTimeoutRef.current !== null) {
      window.clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    if (stableConnectionTimeoutRef.current !== null) {
      window.clearTimeout(stableConnectionTimeoutRef.current)
      stableConnectionTimeoutRef.current = null
    }
  }, [])

  // Start ping interval
  const startPing = useCallback(() => {
    if (pingIntervalRef.current !== null) return

    pingIntervalRef.current = window.setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        // Send ping
        wsRef.current.send(JSON.stringify({ type: 'ping' }))

        // Set pong timeout
        pongTimeoutRef.current = window.setTimeout(() => {
          // No pong received, force reconnect
          console.warn('[useWebSocket] Pong timeout, reconnecting...')
          wsRef.current?.close()
        }, PONG_TIMEOUT)
      }
    }, PING_INTERVAL)
  }, [])

  // Clear pong timeout (called when pong received)
  const handlePong = useCallback(() => {
    if (pongTimeoutRef.current !== null) {
      window.clearTimeout(pongTimeoutRef.current)
      pongTimeoutRef.current = null
    }
  }, [])

  // Ref to hold the connect function for use in scheduleReconnect
  const connectRef = useRef<() => void>(() => {})

  // Schedule reconnect with exponential backoff
  const scheduleReconnect = useCallback(() => {
    if (!mountedRef.current) return
    if (retriesRef.current >= MAX_RETRIES) {
      console.error(`[useWebSocket] Max retries (${MAX_RETRIES}) reached, giving up`)
      setState('error')
      setError(`Failed to connect after ${MAX_RETRIES} attempts`)
      return
    }

    const delay = reconnectDelayRef.current
    console.log(`[useWebSocket] Reconnecting in ${delay}ms (attempt ${retriesRef.current + 1}/${MAX_RETRIES})`)

    reconnectTimeoutRef.current = window.setTimeout(() => {
      if (mountedRef.current) {
        connectRef.current()
      }
    }, delay)

    // Exponential backoff
    reconnectDelayRef.current = Math.min(delay * 2, MAX_RECONNECT_DELAY)
    retriesRef.current += 1
  }, [])

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!mountedRef.current) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    clearTimers()
    setState('connecting')
    setError(null)

    // Build URL with optional topics
    let url = '/api/ws'
    const currentTopics = topicsRef.current
    if (currentTopics && currentTopics.length > 0) {
      url += `?topics=${encodeURIComponent(currentTopics.join(','))}`
    }

    // Convert relative URL to absolute WebSocket URL
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${wsProtocol}//${window.location.host}${url}`

    try {
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        if (!mountedRef.current) {
          ws.close()
          return
        }

        // Detect reconnection (not initial connect)
        const isReconnect = wasConnectedRef.current
        if (isReconnect) {
          console.log('[useWebSocket] Reconnected')
          // Fire reconnect callback
          onReconnectRef.current?.()
        } else {
          console.log('[useWebSocket] Connected')
        }

        // Mark that we've been connected at least once
        wasConnectedRef.current = true
        setState('connected')

        // Reset reconnect delay immediately for next disconnect
        reconnectDelayRef.current = INITIAL_RECONNECT_DELAY

        // Reset retry counter after connection is stable for 30s
        stableConnectionTimeoutRef.current = window.setTimeout(() => {
          if (mountedRef.current && wsRef.current?.readyState === WebSocket.OPEN) {
            retriesRef.current = 0
          }
        }, 30000)

        // Start keepalive
        startPing()
      }

      ws.onclose = (event) => {
        if (!mountedRef.current) return
        console.log(`[useWebSocket] Closed (code: ${event.code})`)
        clearTimers()
        wsRef.current = null

        // Don't reconnect if it was a clean close or component unmounted
        if (event.code === 1000 || !mountedRef.current) {
          setState('disconnected')
        } else {
          setState('disconnected')
          scheduleReconnect()
        }
      }

      ws.onerror = () => {
        if (!mountedRef.current) return
        console.error('[useWebSocket] Error')
        // onclose will be called after onerror, so just update state
        setState('error')
        setError('WebSocket connection error')
      }

      ws.onmessage = (event) => {
        if (!mountedRef.current) return

        try {
          const message = JSON.parse(event.data) as WebSocketMessage<T>

          // Handle internal messages
          if (message.type === 'pong') {
            handlePong()
            return
          }

          if (message.type === 'connection_ack') {
            const ackData = message.data as { topics?: string[] }
            console.log('[useWebSocket] Connection acknowledged, topics:', ackData.topics)
            return
          }

          if (message.type === 'error') {
            const errorData = message.data as { code?: string; detail?: string }
            console.error('[useWebSocket] Server error:', errorData)
            onErrorRef.current?.(errorData.code ?? 'unknown', errorData.detail ?? 'Unknown error')
            return
          }

          // Forward to callback
          onMessageRef.current?.(message)
        } catch (e) {
          console.error('[useWebSocket] Failed to parse message:', e)
        }
      }
    } catch (e) {
      console.error('[useWebSocket] Failed to create WebSocket:', e)
      setState('error')
      setError('Failed to create WebSocket connection')
      scheduleReconnect()
    }
  }, [clearTimers, startPing, handlePong, scheduleReconnect])

  // Keep connectRef updated
  useEffect(() => {
    connectRef.current = connect
  }, [connect])

  // Send message
  const send = useCallback((message: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('[useWebSocket] Cannot send, not connected')
    }
  }, [])

  // Manual reconnect function
  const reconnect = useCallback(() => {
    console.log('[useWebSocket] Manual reconnect requested')
    // Clear all timers and reset state
    clearTimers()
    reconnectDelayRef.current = INITIAL_RECONNECT_DELAY
    retriesRef.current = 0
    setError(null)

    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual reconnect')
      wsRef.current = null
    }

    // Reconnect
    connect()
  }, [clearTimers, connect])

  // Connect/disconnect based on enabled flag
  useEffect(() => {
    mountedRef.current = true

    if (enabled) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- WebSocket connection is an external system
      connect()
    } else {
      // Disconnect if disabled
      if (wsRef.current) {
        wsRef.current.close(1000, 'Disabled')
        wsRef.current = null
      }
      clearTimers()
      setState('disconnected')
    }

    return () => {
      mountedRef.current = false
      clearTimers()
      if (wsRef.current) {
        wsRef.current.close(1000, 'Unmount')
        wsRef.current = null
      }
    }
  }, [enabled, connect, clearTimers])

  return { state, send, error, reconnect }
}
