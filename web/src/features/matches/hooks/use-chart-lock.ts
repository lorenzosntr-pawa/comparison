import { useState, useCallback, useRef } from 'react'

/**
 * State for chart crosshair lock functionality.
 */
export interface ChartLockState {
  /** ISO timestamp of the locked point, or null if unlocked */
  lockedTime: string | null
  /** Index in chart data array of the locked point, or null if unlocked */
  lockedIndex: number | null
  /** Convenience flag indicating whether chart is locked */
  isLocked: boolean
}

/** Recharts chart click event data (simplified type compatible with CategoricalChartFunc) */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type ChartClickData = Record<string, any>

/** Chart data point with at least a time field */
export interface ChartDataPoint {
  time: string
  [key: string]: unknown
}

/**
 * Return type for useChartLock hook.
 */
export interface UseChartLockReturn extends ChartLockState {
  /** Handle chart click to toggle lock state - pass chartData to enable index lookup */
  handleChartClick: (data: ChartClickData, chartData?: ChartDataPoint[]) => void
  /** Clear the lock state */
  clearLock: () => void
}

/**
 * Hook to manage chart crosshair lock state.
 *
 * Enables click-to-lock functionality on recharts LineChart components.
 * Clicking on a data point locks the crosshair at that position;
 * clicking again on the same point (or calling clearLock) unlocks it.
 *
 * Uses index-based comparison for toggle to avoid time string format issues.
 * Includes debounce to prevent multiple rapid clicks from causing issues.
 *
 * IMPORTANT: Pass chartData to handleChartClick to enable index lookup when
 * recharts doesn't provide activeTooltipIndex (which happens in some cases).
 */
export function useChartLock(): UseChartLockReturn {
  const [lockedTime, setLockedTime] = useState<string | null>(null)
  const [lockedIndex, setLockedIndex] = useState<number | null>(null)

  // Track last click time to debounce rapid clicks
  const lastClickRef = useRef<number>(0)

  // Use ref to track current locked index to avoid stale closure issues
  const lockedIndexRef = useRef<number | null>(null)

  const isLocked = lockedTime !== null

  const handleChartClick = useCallback(
    (data: ChartClickData, chartData?: ChartDataPoint[]) => {
      console.log('[useChartLock] handleChartClick called', {
        dataKeys: Object.keys(data),
        activePayload: data.activePayload,
        activeTooltipIndex: data.activeTooltipIndex,
        chartDataLength: chartData?.length,
      })

      // Debounce: ignore clicks within 100ms of last click
      const now = Date.now()
      if (now - lastClickRef.current < 100) {
        console.log('[useChartLock] Debounced - ignoring click')
        return
      }
      lastClickRef.current = now

      // Get index from activeTooltipIndex (recharts may provide as string or number)
      let index: number | null = null
      if (data.activeTooltipIndex !== undefined && data.activeTooltipIndex !== null) {
        const parsed = typeof data.activeTooltipIndex === 'number'
          ? data.activeTooltipIndex
          : parseInt(String(data.activeTooltipIndex), 10)
        if (!isNaN(parsed)) {
          index = parsed
        }
      }

      console.log('[useChartLock] Parsed index:', index)

      if (index === null) {
        console.log('[useChartLock] No valid index - clicked outside data area')
        return
      }

      // Get time from chartData using the index
      let time: string | undefined
      if (chartData && index >= 0 && index < chartData.length) {
        time = chartData[index].time
      }

      // Fallback: try activePayload if available
      if (!time) {
        time = data.activePayload?.[0]?.payload?.time as string | undefined
      }

      if (!time) {
        console.log('[useChartLock] No time found for index', index)
        return
      }

      console.log('[useChartLock] Got time from chartData:', time)

      console.log('[useChartLock] Processing click', { time, index, currentLockedIndex: lockedIndexRef.current })

      // Use index comparison for toggle (more reliable than time string comparison)
      if (lockedIndexRef.current === index) {
        // Clicking same index unlocks
        console.log('[useChartLock] Unlocking - same index clicked')
        setLockedTime(null)
        setLockedIndex(null)
        lockedIndexRef.current = null
      } else {
        // Lock at new position
        console.log('[useChartLock] Locking at', { time, index })
        setLockedTime(time)
        setLockedIndex(index)
        lockedIndexRef.current = index
      }
    },
    [] // No dependencies - uses refs for current state
  )

  const clearLock = useCallback(() => {
    setLockedTime(null)
    setLockedIndex(null)
    lockedIndexRef.current = null
  }, [])

  return {
    lockedTime,
    lockedIndex,
    isLocked,
    handleChartClick,
    clearLock,
  }
}
