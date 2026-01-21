import { useState, useEffect, useCallback } from 'react'

const STORAGE_KEY = 'match-list-columns'

export interface ColumnConfig {
  id: string
  label: string
}

// Available market columns matching backend INLINE_MARKET_IDS (Betpawa taxonomy)
// 3743 = 1X2 Full Time, 5000 = Over/Under Full Time, 3795 = Both Teams To Score Full Time
export const AVAILABLE_COLUMNS: ColumnConfig[] = [
  { id: '3743', label: '1X2' },
  { id: '5000', label: 'O/U 2.5' },
  { id: '3795', label: 'BTTS' },
]

const DEFAULT_VISIBLE_COLUMNS = ['3743', '5000', '3795']

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

function saveToStorage(columns: string[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(columns))
  } catch (e) {
    console.error('Failed to save column settings to localStorage:', e)
  }
}

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
