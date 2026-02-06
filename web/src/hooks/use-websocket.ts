import { useEffect, useRef, useCallback, useState } from 'react'

/**
 * WebSocket connection state
 */
export type WebSocketState = 'connecting' | 'connected' | 'disconnected' | 'error'

/**
 * WebSocket message envelope
 */
export interface WebSocketMessage<T = unknown> {
  type: string
  timestamp: string
  data: T
}

/**
 * Options for useWebSocket hook
 */
export interface UseWebSocketOptions<T = unknown> {
  /** Topics to subscribe to (passed as query param) */
  topics?: string[]
  /** Callback for incoming messages (excluding internal pong/connection_ack) */
  onMessage?: (message: WebSocketMessage<T>) => void
  /** Whether to connect (default: true) */
  enabled?: boolean
  /** Callback for error messages from server */
  onError?: (code: string, detail: string) => void
}

/**
 * Return type for useWebSocket hook
 */
export interface UseWebSocketReturn {
  /** Current connection state */
  state: WebSocketState
  /** Send a message to the server */
  send: (message: unknown) => void
  /** Last error message (if state is 'error') */
  error: string | null
}

// Reconnect configuration
const INITIAL_RECONNECT_DELAY = 1000
const MAX_RECONNECT_DELAY = 30000
const MAX_RETRIES = 10

// Keepalive configuration
const PING_INTERVAL = 30000
const PONG_TIMEOUT = 5000

/**
 * Core WebSocket hook for connecting to /api/ws with topic-based subscriptions.
 *
 * Features:
 * - Auto-reconnect with exponential backoff
 * - Ping/pong keepalive
 * - Message envelope parsing
 * - Clean cleanup on unmount
 */
export function useWebSocket<T = unknown>(
  options: UseWebSocketOptions<T> = {}
): UseWebSocketReturn {
  const { topics, onMessage, enabled = true, onError } = options

  const [state, setState] = useState<WebSocketState>('disconnected')
  const [error, setError] = useState<string | null>(null)

  // Refs to avoid effect dependencies
  const wsRef = useRef<WebSocket | null>(null)
  const pingIntervalRef = useRef<number | null>(null)
  const pongTimeoutRef = useRef<number | null>(null)
  const reconnectTimeoutRef = useRef<number | null>(null)
  const reconnectDelayRef = useRef(INITIAL_RECONNECT_DELAY)
  const retriesRef = useRef(0)
  const mountedRef = useRef(true)

  // Stable refs for callbacks
  const onMessageRef = useRef(onMessage)
  const onErrorRef = useRef(onError)
  useEffect(() => {
    onMessageRef.current = onMessage
    onErrorRef.current = onError
  }, [onMessage, onError])

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
        connect()
      }
    }, delay)

    // Exponential backoff
    reconnectDelayRef.current = Math.min(delay * 2, MAX_RECONNECT_DELAY)
    retriesRef.current += 1
  }, []) // connect added below

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (!mountedRef.current) return
    if (wsRef.current?.readyState === WebSocket.OPEN) return

    clearTimers()
    setState('connecting')
    setError(null)

    // Build URL with optional topics
    let url = '/api/ws'
    if (topics && topics.length > 0) {
      url += `?topics=${encodeURIComponent(topics.join(','))}`
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
        console.log('[useWebSocket] Connected')
        setState('connected')
        // Reset reconnect state on successful connection
        reconnectDelayRef.current = INITIAL_RECONNECT_DELAY
        retriesRef.current = 0
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
  }, [topics, clearTimers, startPing, handlePong, scheduleReconnect])

  // Send message
  const send = useCallback((message: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message))
    } else {
      console.warn('[useWebSocket] Cannot send, not connected')
    }
  }, [])

  // Connect/disconnect based on enabled flag
  useEffect(() => {
    mountedRef.current = true

    if (enabled) {
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

  return { state, send, error }
}
