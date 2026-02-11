import { useState } from 'react'
import { subDays } from 'date-fns'
import { FilterBar, TournamentList, type DateRange } from './components'
import { useTournaments } from './hooks'

export { TournamentDetailPage } from './tournament-detail'

/** Default bookmakers: all enabled */
const DEFAULT_BOOKMAKERS = ['betpawa', 'sportybet', 'bet9ja']

export function HistoricalAnalysisPage() {
  // Default to last 7 days
  const [dateRange, setDateRange] = useState<DateRange>(() => {
    const today = new Date()
    today.setHours(23, 59, 59, 999)
    const from = subDays(today, 7)
    from.setHours(0, 0, 0, 0)
    return { from, to: today }
  })

  // Bookmaker selection state (all enabled by default)
  const [selectedBookmakers, setSelectedBookmakers] = useState<string[]>(DEFAULT_BOOKMAKERS)

  const { data: tournaments, isPending, error } = useTournaments(dateRange)

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Historical Analysis</h1>

      <FilterBar
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        selectedBookmakers={selectedBookmakers}
        onBookmakersChange={setSelectedBookmakers}
      />

      {error && (
        <div className="p-4 text-red-500 bg-red-50 rounded-md">
          Failed to load tournaments: {error.message}
        </div>
      )}

      <TournamentList
        tournaments={tournaments ?? []}
        isLoading={isPending}
        selectedBookmakers={selectedBookmakers}
      />
    </div>
  )
}
