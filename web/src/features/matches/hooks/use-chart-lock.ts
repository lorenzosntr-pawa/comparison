import { useState, useCallback } from 'react'

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

/**
 * Return type for useChartLock hook.
 */
export interface UseChartLockReturn extends ChartLockState {
  /** Handle chart click to toggle lock state */
  handleChartClick: (data: {
    activePayload?: Array<{ payload: { time: string } }>
    activeTooltipIndex?: number
  }) => void
  /** Clear the lock state */
  clearLock: () => void
}

/**
 * Hook to manage chart crosshair lock state.
 *
 * Enables click-to-lock functionality on recharts LineChart components.
 * Clicking on a data point locks the crosshair at that position;
 * clicking again on the same point (or calling clearLock) unlocks it.
 */
export function useChartLock(): UseChartLockReturn {
  const [lockedTime, setLockedTime] = useState<string | null>(null)
  const [lockedIndex, setLockedIndex] = useState<number | null>(null)

  const isLocked = lockedTime !== null

  const handleChartClick = useCallback(
    (data: {
      activePayload?: Array<{ payload: { time: string } }>
      activeTooltipIndex?: number
    }) => {
      const time = data.activePayload?.[0]?.payload?.time
      const index = data.activeTooltipIndex ?? null

      if (!time) {
        // Clicked outside of data area
        return
      }

      if (lockedTime === time) {
        // Clicking same point unlocks
        setLockedTime(null)
        setLockedIndex(null)
      } else {
        // Lock at new position
        setLockedTime(time)
        setLockedIndex(index)
      }
    },
    [lockedTime]
  )

  const clearLock = useCallback(() => {
    setLockedTime(null)
    setLockedIndex(null)
  }, [])

  return {
    lockedTime,
    lockedIndex,
    isLocked,
    handleChartClick,
    clearLock,
  }
}
