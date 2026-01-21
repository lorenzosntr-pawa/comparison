import { useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'

export interface ScrapeProgress {
  platform: string | null
  phase: string
  current: number
  total: number
  events_count: number | null
  message: string | null
  timestamp: string
}

export function useScrapeProgress() {
  const queryClient = useQueryClient()
  const [isStreaming, setIsStreaming] = useState(false)
  const [progress, setProgress] = useState<ScrapeProgress | null>(null)
  const [error, setError] = useState<string | null>(null)

  const startScrape = useCallback(() => {
    setIsStreaming(true)
    setError(null)
    setProgress(null)

    const eventSource = new EventSource('/api/scrape/stream')

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data) as ScrapeProgress
      setProgress(data)

      if (data.phase === 'completed' || data.phase === 'failed') {
        eventSource.close()
        setIsStreaming(false)
        // Invalidate queries to refresh data
        queryClient.invalidateQueries({ queryKey: ['scheduler-history'] })
        queryClient.invalidateQueries({ queryKey: ['events'] })
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      setIsStreaming(false)
      setError('Connection lost')
    }

    return () => {
      eventSource.close()
      setIsStreaming(false)
    }
  }, [queryClient])

  return { startScrape, isStreaming, progress, error }
}
