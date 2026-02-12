import { useState, useMemo } from 'react'
import { subDays } from 'date-fns'
import { FilterBar, TournamentList, type DateRange } from './components'
import { useTournaments } from './hooks'

export { TournamentDetailPage } from './tournament-detail'

export function HistoricalAnalysisPage() {
  // Default to last 7 days
  const [dateRange, setDateRange] = useState<DateRange>(() => {
    const today = new Date()
    today.setHours(23, 59, 59, 999)
    const from = subDays(today, 7)
    from.setHours(0, 0, 0, 0)
    return { from, to: today }
  })

  // Bookmaker filter state - all selected by default
  const [selectedBookmakers, setSelectedBookmakers] = useState([
    'betpawa',
    'sportybet',
    'bet9ja',
  ])

  // Tournament search filter
  const [searchQuery, setSearchQuery] = useState('')

  // Country filter state
  const [selectedCountries, setSelectedCountries] = useState<string[]>([])

  const { data: tournaments, isPending, error } = useTournaments(dateRange)

  // Extract unique countries from tournaments
  const availableCountries = useMemo(() => {
    if (!tournaments) return []
    const countries = new Set<string>()
    tournaments.forEach((t) => {
      if (t.country) countries.add(t.country)
    })
    return Array.from(countries).sort()
  }, [tournaments])

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Historical Analysis</h1>

      <FilterBar
        dateRange={dateRange}
        onDateRangeChange={setDateRange}
        selectedBookmakers={selectedBookmakers}
        onBookmakersChange={setSelectedBookmakers}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        availableCountries={availableCountries}
        selectedCountries={selectedCountries}
        onCountriesChange={setSelectedCountries}
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
        searchQuery={searchQuery}
        selectedCountries={selectedCountries}
      />
    </div>
  )
}
