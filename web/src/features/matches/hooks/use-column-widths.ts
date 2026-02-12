/**
 * Hook for managing column widths in the matches table.
 *
 * @module use-column-widths
 * @description Provides persistent column width settings for the matches
 * list view. Users can resize columns by dragging borders, and their
 * preferences are stored in localStorage.
 *
 * This is a UI state hook separate from column visibility (use-column-settings).
 *
 * @example
 * ```typescript
 * import { useColumnWidths } from '@/features/matches/hooks/use-column-widths'
 *
 * function MatchTable() {
 *   const { widths, setWidth, resetWidths } = useColumnWidths()
 *
 *   return (
 *     <th style={{ width: widths.region }}>Region</th>
 *   )
 * }
 * ```
 */

import { useState, useCallback } from 'react'

/** LocalStorage key for persisting column widths (separate from visibility) */
const STORAGE_KEY = 'match-list-column-widths'

/** Minimum column width in pixels */
const MIN_WIDTH = 40

/**
 * Default widths for fixed columns in pixels.
 * Market columns use dynamic sizing based on content.
 */
const DEFAULT_WIDTHS: Record<string, number> = {
  region: 100,
  tournament: 150,
  kickoff: 120,
  match: 200,
  book: 50,
}

/**
 * Return type for the useColumnWidths hook.
 */
export interface UseColumnWidthsReturn {
  /** Current column widths in pixels */
  widths: Record<string, number>
  /** Set width for a specific column (enforces MIN_WIDTH) */
  setWidth: (columnId: string, width: number) => void
  /** Reset all widths to defaults */
  resetWidths: () => void
}

/**
 * Loads column widths from localStorage.
 * @returns Record of column widths, or defaults if not found/invalid
 * @internal
 */
function loadFromStorage(): Record<string, number> {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (typeof parsed === 'object' && parsed !== null) {
        // Merge with defaults to handle new columns
        return { ...DEFAULT_WIDTHS, ...parsed }
      }
    }
  } catch (e) {
    console.error('Failed to load column widths from localStorage:', e)
  }
  return { ...DEFAULT_WIDTHS }
}

/**
 * Persists column widths to localStorage.
 * @param widths - Record of column widths to save
 * @internal
 */
function saveToStorage(widths: Record<string, number>): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(widths))
  } catch (e) {
    console.error('Failed to save column widths to localStorage:', e)
  }
}

/**
 * Manages column width settings with localStorage persistence.
 *
 * @description Provides state and controls for resizing columns in the
 * matches table. Widths are automatically persisted to localStorage and
 * restored on page reload.
 *
 * ## Features
 * - Set width for individual columns
 * - Enforces minimum width constraint (40px)
 * - Reset all widths to defaults
 * - Auto-saves to localStorage on any change
 *
 * @returns Object containing:
 *   - `widths`: Current column widths in pixels
 *   - `setWidth`: Function to set a column's width
 *   - `resetWidths`: Function to reset all widths to defaults
 */
export function useColumnWidths(): UseColumnWidthsReturn {
  const [widths, setWidths] = useState<Record<string, number>>(() =>
    loadFromStorage()
  )

  const setWidth = useCallback((columnId: string, width: number) => {
    // Enforce minimum width
    const constrainedWidth = Math.max(MIN_WIDTH, width)

    setWidths((prev) => {
      const next = { ...prev, [columnId]: constrainedWidth }
      saveToStorage(next)
      return next
    })
  }, [])

  const resetWidths = useCallback(() => {
    setWidths({ ...DEFAULT_WIDTHS })
    saveToStorage({ ...DEFAULT_WIDTHS })
  }, [])

  return {
    widths,
    setWidth,
    resetWidths,
  }
}
