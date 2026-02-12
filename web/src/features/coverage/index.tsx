import { useState, useMemo } from 'react'
import { useCoverage, usePalimpsestEvents } from './hooks'
import {
  CoverageStatsCards,
  TournamentStatsCards,
  CoverageFilterBar,
  TournamentTable,
  type CoverageFilters,
} from './components'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'

const DEFAULT_FILTERS: CoverageFilters = {
  availability: 'all',
  search: '',
  countries: [],
  includeStarted: false,
}

export function CoveragePage() {
  const [filters, setFilters] = useState<CoverageFilters>(DEFAULT_FILTERS)

  // Map filter availability to API param (null for 'all')
  const apiAvailability =
    filters.availability === 'all' ? undefined : filters.availability

  const {
    data: coverage,
    isPending: coveragePending,
    error: coverageError,
  } = useCoverage({ includeStarted: filters.includeStarted })

  // Unfiltered query for stats cards - always fetches ALL tournaments
  const {
    data: statsData,
    isPending: statsPending,
    error: statsError,
  } = usePalimpsestEvents({
    includeStarted: filters.includeStarted,
  })

  // Filtered query for table display
  const {
    data: eventsData,
    isPending: eventsPending,
    error: eventsError,
  } = usePalimpsestEvents({
    availability: apiAvailability,
    search: filters.search || undefined,
    includeStarted: filters.includeStarted,
  })

  const error = coverageError || eventsError || statsError

  // Stable reference for all tournaments (used by TournamentStatsCards)
  // Uses statsData which never changes based on availability filter
  const allTournaments = useMemo(
    () => statsData?.tournaments ?? [],
    [statsData?.tournaments]
  )

  // Extract unique countries from tournaments for the country filter dropdown
  const uniqueCountries = useMemo(() => {
    if (!allTournaments.length) return []
    const countries = new Set<string>()
    allTournaments.forEach((t) => {
      if (t.tournament_country) {
        countries.add(t.tournament_country)
      }
    })
    return Array.from(countries).sort()
  }, [allTournaments])

  // Get tournaments from availability-filtered data for table display
  const tableTournaments = useMemo(
    () => eventsData?.tournaments ?? [],
    [eventsData?.tournaments]
  )

  // Filter table tournaments by selected countries
  const filteredTournaments = useMemo(() => {
    if (!tableTournaments.length) return []
    if (filters.countries.length === 0) return tableTournaments
    return tableTournaments.filter(
      (t) =>
        t.tournament_country && filters.countries.includes(t.tournament_country)
    )
  }, [tableTournaments, filters.countries])

  // Calculate filtered event count
  const filteredEventCount = useMemo(() => {
    return filteredTournaments.reduce((sum, t) => sum + t.events.length, 0)
  }, [filteredTournaments])

  if (error) {
    return (
      <div className="p-4 text-red-500 bg-red-50 rounded-md">
        Failed to load coverage data: {error.message}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Coverage Comparison</h1>
        <div className="flex items-center gap-4">
          {/* Include Started Toggle */}
          <div className="flex items-center gap-2">
            <Switch
              id="include-started"
              checked={filters.includeStarted}
              onCheckedChange={(checked) =>
                setFilters({ ...filters, includeStarted: checked })
              }
            />
            <Label
              htmlFor="include-started"
              className="text-sm text-muted-foreground"
            >
              Include Started
            </Label>
          </div>
          {/* Event count */}
          {eventsData && (
            <span className="text-sm text-muted-foreground">
              {filteredEventCount} events
              {filters.countries.length > 0 &&
                ` in ${
                  filters.countries.length <= 2
                    ? filters.countries.join(', ')
                    : `${filters.countries.length} countries`
                }`}
            </span>
          )}
        </div>
      </div>

      {/* Event Stats Cards */}
      <CoverageStatsCards coverage={coverage} isLoading={coveragePending} />

      {/* Tournament Stats Cards - uses statsData (unfiltered) to avoid re-computation on filter changes */}
      <TournamentStatsCards
        tournaments={allTournaments}
        isLoading={statsPending}
      />

      {/* Filters */}
      <CoverageFilterBar
        filters={filters}
        onFiltersChange={setFilters}
        countries={uniqueCountries}
      />

      {/* Tournament Table */}
      <TournamentTable
        tournaments={filteredTournaments}
        isLoading={eventsPending}
      />
    </div>
  )
}
