import { useState, useCallback, useRef, useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
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
 * Hook to observe progress of an existing running scrape.
 * Unlike useScrapeProgress which starts a new scrape,
 * this observes an existing scrape by ID.
 */
export function useObserveScrape(scrapeRunId: number | null) {
  const queryClient = useQueryClient()
  const eventSourceRef = useRef<EventSource | null>(null)

  const [isObserving, setIsObserving] = useState(false)
  const [progress, setProgress] = useState<ScrapeProgress | null>(null)
  const [error, setError] = useState<string | null>(null)

  const cleanup = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    setIsObserving(false)
  }, [])

  const observe = useCallback(() => {
    if (!scrapeRunId) return

    cleanup()
    setError(null)
    setProgress(null)
    setIsObserving(true)

    const eventSource = new EventSource(`/api/scrape/runs/${scrapeRunId}/progress`)
    eventSourceRef.current = eventSource

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ScrapeProgress
        setProgress(data)

        // Handle completion
        if (data.phase === 'completed' || data.phase === 'failed') {
          eventSource.close()
          setIsObserving(false)

          // Invalidate queries to refresh data
          queryClient.invalidateQueries({ queryKey: ['scheduler-history'] })
          queryClient.invalidateQueries({ queryKey: ['events'] })
          queryClient.invalidateQueries({ queryKey: ['scrape-run'] })
        }
      } catch (e) {
        console.error('Failed to parse SSE event:', e)
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      setIsObserving(false)
      // 410 Gone means scrape already completed - not an error
      // Other errors are connection issues
      setError('Connection lost or scrape already completed')
    }
  }, [scrapeRunId, cleanup, queryClient])

  // Auto-observe when scrapeRunId changes
  useEffect(() => {
    if (scrapeRunId) {
      observe()
    }
    return cleanup
  }, [scrapeRunId, observe, cleanup])

  return { isObserving, progress, error, observe, cleanup }
}

/**
 * Hook to check for and observe active scrapes.
 * Polls for active scrapes and automatically starts observing if one is found.
 */
export function useActiveScrapesObserver() {
  const [activeScrapeId, setActiveScrapeId] = useState<number | null>(null)
  const [isChecking, setIsChecking] = useState(true)
  const checkIntervalRef = useRef<number | null>(null)

  const checkForActiveScrapes = useCallback(async () => {
    try {
      // api.get returns the data directly, not wrapped in { data: ... }
      const activeIds = await api.get<number[]>('/scrape/runs/active')
      if (activeIds.length > 0) {
        // Take the most recent (first) active scrape
        setActiveScrapeId(activeIds[0])
      } else {
        setActiveScrapeId(null)
      }
    } catch {
      // Endpoint might not exist or other error - ignore
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

  // Use the observe hook with the found ID
  const observation = useObserveScrape(activeScrapeId)

  return {
    activeScrapeId,
    isChecking,
    ...observation,
    // Expose function to stop checking (e.g., when user starts manual scrape)
    stopChecking: () => {
      if (checkIntervalRef.current) {
        window.clearInterval(checkIntervalRef.current)
        checkIntervalRef.current = null
      }
    },
  }
}
