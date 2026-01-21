import { useState, useMemo } from 'react'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { MatchTable, MatchFilters } from './components'
import type { MatchFiltersState } from './components'
import { useMatches } from './hooks'

const DEFAULT_FILTERS: MatchFiltersState = {
  tournamentId: undefined,
  kickoffFrom: '',
  kickoffTo: '',
  minBookmakers: 2,
  sortBy: 'kickoff',
}

export function MatchList() {
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [filters, setFilters] = useState<MatchFiltersState>(DEFAULT_FILTERS)

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
    tournamentId: filters.tournamentId,
    kickoffFrom: apiKickoffFrom,
    kickoffTo: apiKickoffTo,
  })

  // Reset to page 1 when filters change
  const handleFiltersChange = (newFilters: MatchFiltersState) => {
    setFilters(newFilters)
    setPage(1)
  }

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
        <h1 className="text-2xl font-bold">Matches</h1>
        {data && (
          <span className="text-sm text-muted-foreground">
            {data.total} matches found
          </span>
        )}
      </div>

      {/* Filters */}
      <MatchFilters filters={filters} onFiltersChange={handleFiltersChange} />

      {error && (
        <div className="p-4 text-red-500 bg-red-50 rounded-md">
          Failed to load matches: {error.message}
        </div>
      )}

      <MatchTable events={sortedEvents} isLoading={isPending} />

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
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Match Detail</h1>
      <p className="text-muted-foreground">
        Detailed market odds comparison will appear here.
      </p>
    </div>
  )
}
