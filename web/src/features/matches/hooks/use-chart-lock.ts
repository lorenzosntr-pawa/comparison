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

/**
 * Return type for useChartLock hook.
 */
export interface UseChartLockReturn extends ChartLockState {
  /** Handle chart click to toggle lock state */
  handleChartClick: (data: ChartClickData) => void
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
    (data: ChartClickData) => {
      // Debounce: ignore clicks within 100ms of last click
      const now = Date.now()
      if (now - lastClickRef.current < 100) {
        return
      }
      lastClickRef.current = now

      // Extract time from recharts payload
      const time = data.activePayload?.[0]?.payload?.time as string | undefined
      // activeTooltipIndex is the index in the data array
      const index = typeof data.activeTooltipIndex === 'number' ? data.activeTooltipIndex : null

      if (time === undefined || index === null) {
        // Clicked outside of data area or between points
        return
      }

      // Use index comparison for toggle (more reliable than time string comparison)
      if (lockedIndexRef.current === index) {
        // Clicking same index unlocks
        setLockedTime(null)
        setLockedIndex(null)
        lockedIndexRef.current = null
      } else {
        // Lock at new position
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
