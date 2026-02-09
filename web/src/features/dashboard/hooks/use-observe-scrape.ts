import { useState, useCallback, useRef, useEffect } from 'react'
import {
  useWebSocketScrapeProgress,
  type PlatformProgress,
} from '@/hooks/use-websocket-scrape-progress'
import { api } from '@/lib/api'

export interface ScrapeProgress {
  platform: string | null
  phase: string
  current: number
  total: number
  events_count: number | null
  message: string | null
  timestamp: string
}

/**
 * Hook to check for and observe active scrapes via WebSocket.
 * Polls for active scrapes and automatically observes via WebSocket.
 */
export function useActiveScrapesObserver() {
  const [activeScrapeId, setActiveScrapeId] = useState<number | null>(null)
  const [isChecking, setIsChecking] = useState(true)
  const checkIntervalRef = useRef<number | null>(null)

  const checkForActiveScrapes = useCallback(async () => {
    try {
      const activeIds = await api.get<number[]>('/scrape/runs/active')
      if (activeIds.length > 0) {
        setActiveScrapeId(activeIds[0])
      } else {
        setActiveScrapeId(null)
      }
    } catch {
      console.debug('No active scrapes or endpoint not available')
      setActiveScrapeId(null)
    } finally {
      setIsChecking(false)
    }
  }, [])

  // Check initially and then every 5 seconds
  useEffect(() => {
    checkForActiveScrapes()

    checkIntervalRef.current = window.setInterval(checkForActiveScrapes, 5000)

    return () => {
      if (checkIntervalRef.current) {
        window.clearInterval(checkIntervalRef.current)
      }
    }
  }, [checkForActiveScrapes])

  // WebSocket transport for progress observation
  const ws = useWebSocketScrapeProgress({
    enabled: true,
    onComplete: () => {
      setActiveScrapeId(null)
    },
  })

  return {
    activeScrapeId,
    isChecking,
    isObserving: activeScrapeId !== null && ws.isConnected,
    progress: ws.currentProgress,
    platformProgress: ws.platformProgress as Map<string, PlatformProgress>,
    overallPhase: ws.overallPhase,
    error: ws.error,
    stopChecking: () => {
      if (checkIntervalRef.current) {
        window.clearInterval(checkIntervalRef.current)
        checkIntervalRef.current = null
      }
    },
  }
}
