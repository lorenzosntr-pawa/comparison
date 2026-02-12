import { useState, useMemo, useCallback } from 'react'
import { useParams } from 'react-router'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { MatchTable, MatchFilters, ColumnSettings, MatchHeader, MarketGrid, SummarySection } from './components'
import type { MatchFiltersState } from './components'
import { useMatches, useColumnSettings, useMatchDetail } from './hooks'
import { cn } from '@/lib/utils'

const DEFAULT_BETPAWA_FILTERS: MatchFiltersState = {
  search: '',
  countryFilter: [],
  tournamentIds: [],
  kickoffFrom: '',
  kickoffTo: '',
  minBookmakers: 2,
  sortBy: 'kickoff',
  availability: 'betpawa',
}

const DEFAULT_COMPETITOR_FILTERS: MatchFiltersState = {
  search: '',
  countryFilter: [],
  tournamentIds: [],
  kickoffFrom: '',
  kickoffTo: '',
  minBookmakers: 2,
  sortBy: 'kickoff',
  availability: 'competitor',
}

export function MatchList() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)

  // Per-mode filter state - each mode has independent filters
  const [betpawaFilters, setBetpawaFilters] = useState<MatchFiltersState>(DEFAULT_BETPAWA_FILTERS)
  const [competitorFilters, setCompetitorFilters] = useState<MatchFiltersState>(DEFAULT_COMPETITOR_FILTERS)
  const [currentMode, setCurrentMode] = useState<'betpawa' | 'competitor'>('betpawa')

  // Get current filters based on mode
  const filters = currentMode === 'betpawa' ? betpawaFilters : competitorFilters
  const setFilters = currentMode === 'betpawa' ? setBetpawaFilters : setCompetitorFilters

  // Column visibility settings (persisted to localStorage)
  const {
    visibleColumns,
    toggleColumn,
    showAll,
    hideAll,
  } = useColumnSettings()

  // Convert datetime-local format to ISO for API
  const apiKickoffFrom = useMemo(() => {
    if (!filters.kickoffFrom) return undefined
    return new Date(filters.kickoffFrom).toISOString()
  }, [filters.kickoffFrom])

  const apiKickoffTo = useMemo(() => {
    if (!filters.kickoffTo) return undefined
    return new Date(filters.kickoffTo).toISOString()
  }, [filters.kickoffTo])

  const { data, isPending, error } = useMatches({
    page,
    pageSize,
    minBookmakers: filters.minBookmakers,
    tournamentIds: filters.tournamentIds.length > 0 ? filters.tournamentIds : undefined,
    countries: filters.countryFilter.length > 0 ? filters.countryFilter : undefined,
    kickoffFrom: apiKickoffFrom,
    kickoffTo: apiKickoffTo,
    search: filters.search || undefined,
    availability: filters.availability,
  })

  // Handle filter changes (excluding mode switch)
  const handleFiltersChange = useCallback((newFilters: MatchFiltersState) => {
    // If availability changed, switch mode instead of updating current filters
    if (newFilters.availability !== currentMode) {
      setCurrentMode(newFilters.availability)
      setPage(1)
      return
    }
    // Otherwise update current mode's filters
    setFilters(newFilters)
    setPage(1)
  }, [currentMode, setFilters])

  // Handle mode switch via toggle buttons
  const handleModeSwitch = useCallback((mode: 'betpawa' | 'competitor') => {
    if (mode !== currentMode) {
      setCurrentMode(mode)
      setPage(1)
    }
  }, [currentMode])

  // Sort events client-side based on sortBy
  const sortedEvents = useMemo(() => {
    if (!data?.events) return []
    if (filters.sortBy === 'tournament') {
      return [...data.events].sort((a, b) =>
        a.tournament_name.localeCompare(b.tournament_name)
      )
    }
    return data.events // Already sorted by kickoff from API
  }, [data?.events, filters.sortBy])

  const totalPages = data ? Math.ceil(data.total / pageSize) : 0

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Odds Comparison</h1>
        <div className="flex items-center gap-4">
          {data && (
            <span className="text-sm text-muted-foreground">
              {data.total} matches found
            </span>
          )}
          {/* Availability toggle */}
          <div className="inline-flex h-9 items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className={cn(
                'h-7 px-3 text-xs font-medium',
                currentMode === 'betpawa' &&
                  'bg-background text-foreground shadow-sm'
              )}
              onClick={() => handleModeSwitch('betpawa')}
            >
              BetPawa
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className={cn(
                'h-7 px-3 text-xs font-medium',
                currentMode === 'competitor' &&
                  'bg-background text-foreground shadow-sm'
              )}
              onClick={() => handleModeSwitch('competitor')}
            >
              Competitors Only
            </Button>
          </div>
          <ColumnSettings
            visibleColumns={visibleColumns}
            onToggleColumn={toggleColumn}
            onShowAll={showAll}
            onHideAll={hideAll}
          />
        </div>
      </div>

      {/* Filters */}
      <MatchFilters filters={filters} onFiltersChange={handleFiltersChange} />

      {error && (
        <div className="p-4 text-red-500 bg-red-50 rounded-md">
          Failed to load matches: {error.message}
        </div>
      )}

      <MatchTable
        events={sortedEvents}
        isLoading={isPending}
        visibleColumns={visibleColumns}
        excludeBetpawa={filters.availability === 'competitor'}
      />

      {/* Pagination */}
      {data && data.total > 0 && (
        <div className="flex items-center justify-between pt-4">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= totalPages}
            >
              Next
            </Button>
          </div>

          <span className="text-sm text-muted-foreground">
            Page {page} of {totalPages || 1}
          </span>

          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Per page:</span>
            <Select
              value={pageSize.toString()}
              onValueChange={(value) => {
                setPageSize(parseInt(value))
                setPage(1)
              }}
            >
              <SelectTrigger className="w-[80px]">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="25">25</SelectItem>
                <SelectItem value="50">50</SelectItem>
                <SelectItem value="100">100</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      )}
    </div>
  )
}

export function MatchDetail() {
  const { id } = useParams<{ id: string }>()
  const eventId = id ? parseInt(id, 10) : undefined

  const { data: event, isPending, error } = useMatchDetail(eventId)

  if (isPending) {
    return (
      <div className="space-y-4">
        <Card>
          <CardHeader>
            <Skeleton className="h-8 w-48" />
          </CardHeader>
          <CardContent>
            <Skeleton className="h-6 w-64 mb-2" />
            <Skeleton className="h-4 w-48" />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Markets</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-4 text-red-500 bg-red-50 rounded-md">
        Failed to load match details: {error.message}
      </div>
    )
  }

  if (!event) {
    return (
      <div className="p-4 text-muted-foreground">Match not found.</div>
    )
  }

  return (
    <div className="space-y-4">
      <MatchHeader event={event} />

      <SummarySection marketsByBookmaker={event.markets_by_bookmaker} />

      <MarketGrid marketsByBookmaker={event.markets_by_bookmaker} eventId={eventId!} />
    </div>
  )
}
