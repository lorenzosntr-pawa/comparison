/**
 * Hook for managing column visibility in the matches table.
 *
 * @module use-column-settings
 * @description Provides persistent column visibility settings for the matches
 * list view. Users can show/hide market columns (1X2, Over/Under, BTTS, etc.)
 * and their preferences are stored in localStorage.
 *
 * This is a UI state hook, not a data fetching hook - it manages local
 * preferences rather than server data.
 *
 * @example
 * ```typescript
 * import { useColumnSettings, AVAILABLE_COLUMNS } from '@/features/matches/hooks/use-column-settings'
 *
 * function ColumnPicker() {
 *   const { visibleColumns, toggleColumn, showAll, hideAll } = useColumnSettings()
 *
 *   return (
 *     <div>
 *       {AVAILABLE_COLUMNS.map(col => (
 *         <Checkbox
 *           key={col.id}
 *           checked={visibleColumns.includes(col.id)}
 *           onCheckedChange={() => toggleColumn(col.id)}
 *         >
 *           {col.label}
 *         </Checkbox>
 *       ))}
 *     </div>
 *   )
 * }
 * ```
 */

import { useState, useEffect, useCallback } from 'react'

/** LocalStorage key for persisting column settings */
const STORAGE_KEY = 'match-list-columns'

/**
 * Configuration for a displayable column.
 *
 * @description Defines a market column that can be shown in the matches table.
 */
export interface ColumnConfig {
  /** Market ID matching backend INLINE_MARKET_IDS (Betpawa taxonomy) */
  id: string
  /** Human-readable column label */
  label: string
}

/**
 * Available market columns for the matches table.
 *
 * @description Maps to backend INLINE_MARKET_IDS using Betpawa's market taxonomy:
 * - 3743 = 1X2 Full Time (Match Result)
 * - 5000 = Over/Under Full Time (Goals Total)
 * - 3795 = Both Teams To Score Full Time (BTTS)
 * - 4693 = Double Chance Full Time
 */
export const AVAILABLE_COLUMNS: ColumnConfig[] = [
  { id: '3743', label: '1X2' },
  { id: '5000', label: 'O/U 2.5' },
  { id: '3795', label: 'BTTS' },
  { id: '4693', label: 'Double Chance' },
]

/** Default columns shown when no localStorage data exists */
const DEFAULT_VISIBLE_COLUMNS = ['3743', '5000', '3795']

/**
 * Loads column visibility settings from localStorage.
 * @returns Array of visible column IDs, or defaults if not found/invalid
 * @internal
 */
function loadFromStorage(): string[] {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      const parsed = JSON.parse(stored)
      if (Array.isArray(parsed)) {
        // Validate that all stored IDs are valid
        const validIds = AVAILABLE_COLUMNS.map((c) => c.id)
        return parsed.filter((id: string) => validIds.includes(id))
      }
    }
  } catch (e) {
    console.error('Failed to load column settings from localStorage:', e)
  }
  return DEFAULT_VISIBLE_COLUMNS
}

/**
 * Persists column visibility settings to localStorage.
 * @param columns - Array of visible column IDs to save
 * @internal
 */
function saveToStorage(columns: string[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(columns))
  } catch (e) {
    console.error('Failed to save column settings to localStorage:', e)
  }
}

/**
 * Manages column visibility settings with localStorage persistence.
 *
 * @description Provides state and controls for showing/hiding market columns
 * in the matches table. Settings are automatically persisted to localStorage
 * and restored on page reload.
 *
 * ## Features
 * - Toggle individual columns on/off
 * - Show all / hide all shortcuts
 * - Prevents hiding all columns (keeps at least one visible)
 * - Auto-saves to localStorage on any change
 *
 * @returns Object containing:
 *   - `visibleColumns`: Array of currently visible column IDs
 *   - `toggleColumn`: Function to toggle a single column
 *   - `isColumnVisible`: Function to check if a column is visible
 *   - `showAll`: Function to show all available columns
 *   - `hideAll`: Function to hide all except first column
 *   - `availableColumns`: Reference to AVAILABLE_COLUMNS constant
 *
 * @example
 * ```typescript
 * const { visibleColumns, toggleColumn, isColumnVisible } = useColumnSettings()
 *
 * // In table header
 * {AVAILABLE_COLUMNS.filter(col => isColumnVisible(col.id)).map(col => (
 *   <th key={col.id}>{col.label}</th>
 * ))}
 * ```
 */
export function useColumnSettings() {
  const [visibleColumns, setVisibleColumns] = useState<string[]>(() =>
    loadFromStorage()
  )

  // Save to localStorage whenever visible columns change
  useEffect(() => {
    saveToStorage(visibleColumns)
  }, [visibleColumns])

  const toggleColumn = useCallback((columnId: string) => {
    setVisibleColumns((prev) => {
      if (prev.includes(columnId)) {
        // Don't allow removing all columns
        if (prev.length === 1) return prev
        return prev.filter((id) => id !== columnId)
      }
      return [...prev, columnId]
    })
  }, [])

  const isColumnVisible = useCallback(
    (columnId: string) => visibleColumns.includes(columnId),
    [visibleColumns]
  )

  const showAll = useCallback(() => {
    setVisibleColumns(AVAILABLE_COLUMNS.map((c) => c.id))
  }, [])

  const hideAll = useCallback(() => {
    // Keep at least one column visible
    setVisibleColumns([AVAILABLE_COLUMNS[0].id])
  }, [])

  return {
    visibleColumns,
    toggleColumn,
    isColumnVisible,
    showAll,
    hideAll,
    availableColumns: AVAILABLE_COLUMNS,
  }
}
