import { useState, useMemo } from 'react'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { useCoverage, usePalimpsestEvents } from './hooks'
import {
  CoverageStatsCards,
  CoverageFilterBar,
  type CoverageFilters,
} from './components'

const DEFAULT_FILTERS: CoverageFilters = {
  availability: 'all',
  search: '',
  country: undefined,
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
  } = useCoverage()

  const {
    data: eventsData,
    isPending: eventsPending,
    error: eventsError,
  } = usePalimpsestEvents({
    availability: apiAvailability,
    search: filters.search || undefined,
  })

  const isPending = coveragePending || eventsPending
  const error = coverageError || eventsError

  // Extract unique countries from tournaments for the country filter dropdown
  const uniqueCountries = useMemo(() => {
    if (!eventsData?.tournaments) return []
    const countries = new Set<string>()
    eventsData.tournaments.forEach((t) => {
      if (t.tournament_country) {
        countries.add(t.tournament_country)
      }
    })
    return Array.from(countries).sort()
  }, [eventsData?.tournaments])

  // Filter tournaments by country if selected
  const filteredTournaments = useMemo(() => {
    if (!eventsData?.tournaments) return []
    if (!filters.country) return eventsData.tournaments
    return eventsData.tournaments.filter(
      (t) => t.tournament_country === filters.country
    )
  }, [eventsData?.tournaments, filters.country])

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
        {eventsData && (
          <span className="text-sm text-muted-foreground">
            {filteredEventCount} events
            {filters.country && ` in ${filters.country}`}
          </span>
        )}
      </div>

      {/* Stats Cards */}
      <CoverageStatsCards coverage={coverage} isLoading={coveragePending} />

      {/* Filters */}
      <CoverageFilterBar
        filters={filters}
        onFiltersChange={setFilters}
        countries={uniqueCountries}
      />

      {/* Tournament data placeholder */}
      {isPending ? (
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" />
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="text-sm text-muted-foreground p-4 border rounded-md">
          Tournament data: {filteredTournaments.length} tournaments,{' '}
          {filteredEventCount} events
          {filters.availability !== 'all' && ` (${filters.availability})`}
        </div>
      )}
    </div>
  )
}
