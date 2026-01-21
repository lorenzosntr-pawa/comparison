import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useTournaments } from '../hooks/use-tournaments'
import { X } from 'lucide-react'

type DatePreset = 'today' | 'tomorrow' | 'weekend' | 'next7days'

function getDatePreset(preset: DatePreset): { from: Date; to: Date } {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())

  switch (preset) {
    case 'today': {
      const end = new Date(today)
      end.setDate(end.getDate() + 1)
      return { from: today, to: end }
    }
    case 'tomorrow': {
      const start = new Date(today)
      start.setDate(start.getDate() + 1)
      const end = new Date(start)
      end.setDate(end.getDate() + 1)
      return { from: start, to: end }
    }
    case 'weekend': {
      // Find next Saturday (or today if it is Saturday)
      const saturday = new Date(today)
      const dayOfWeek = saturday.getDay()
      if (dayOfWeek === 0) {
        // Sunday - go back to Saturday
        saturday.setDate(saturday.getDate() - 1)
      } else if (dayOfWeek !== 6) {
        // Not Saturday - find next Saturday
        saturday.setDate(saturday.getDate() + (6 - dayOfWeek))
      }
      const monday = new Date(saturday)
      monday.setDate(monday.getDate() + 2)
      return { from: saturday, to: monday }
    }
    case 'next7days': {
      const end = new Date(today)
      end.setDate(end.getDate() + 7)
      return { from: today, to: end }
    }
  }
}

function toDatetimeLocal(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day}T${hours}:${minutes}`
}

export interface MatchFiltersState {
  tournamentId: number | undefined
  kickoffFrom: string
  kickoffTo: string
  minBookmakers: number
  sortBy: 'kickoff' | 'tournament'
}

interface MatchFiltersProps {
  filters: MatchFiltersState
  onFiltersChange: (filters: MatchFiltersState) => void
}

export function MatchFilters({ filters, onFiltersChange }: MatchFiltersProps) {
  const { data: tournaments, isPending: tournamentsLoading } = useTournaments()

  const updateFilter = <K extends keyof MatchFiltersState>(
    key: K,
    value: MatchFiltersState[K]
  ) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  const applyDatePreset = (preset: DatePreset) => {
    const { from, to } = getDatePreset(preset)
    onFiltersChange({
      ...filters,
      kickoffFrom: toDatetimeLocal(from),
      kickoffTo: toDatetimeLocal(to),
    })
  }

  const clearFilters = () => {
    onFiltersChange({
      tournamentId: undefined,
      kickoffFrom: '',
      kickoffTo: '',
      minBookmakers: 2,
      sortBy: 'kickoff',
    })
  }

  const hasActiveFilters =
    filters.tournamentId !== undefined ||
    filters.kickoffFrom !== '' ||
    filters.kickoffTo !== '' ||
    filters.minBookmakers !== 2

  return (
    <div className="flex flex-wrap items-end gap-4 p-4 bg-muted/30 rounded-lg">
      {/* Tournament filter */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">Tournament</label>
        <Select
          value={filters.tournamentId?.toString() ?? 'all'}
          onValueChange={(value) =>
            updateFilter('tournamentId', value === 'all' ? undefined : parseInt(value))
          }
          disabled={tournamentsLoading}
        >
          <SelectTrigger className="w-[200px]">
            <SelectValue placeholder="All tournaments" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All tournaments</SelectItem>
            {tournaments?.map((t) => (
              <SelectItem key={t.id} value={t.id.toString()}>
                {t.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* Date presets and range */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">Date</label>
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => applyDatePreset('today')}
            className="h-9 px-2 text-xs"
          >
            Today
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => applyDatePreset('tomorrow')}
            className="h-9 px-2 text-xs"
          >
            Tomorrow
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => applyDatePreset('weekend')}
            className="h-9 px-2 text-xs"
          >
            Weekend
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => applyDatePreset('next7days')}
            className="h-9 px-2 text-xs"
          >
            7 Days
          </Button>
        </div>
      </div>

      {/* Kickoff from */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">From</label>
        <Input
          type="datetime-local"
          value={filters.kickoffFrom}
          onChange={(e) => updateFilter('kickoffFrom', e.target.value)}
          className="w-[180px]"
        />
      </div>

      {/* Kickoff to */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">To</label>
        <Input
          type="datetime-local"
          value={filters.kickoffTo}
          onChange={(e) => updateFilter('kickoffTo', e.target.value)}
          className="w-[180px]"
        />
      </div>

      {/* Min bookmakers */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">Min Bookmakers</label>
        <Select
          value={filters.minBookmakers.toString()}
          onValueChange={(value) => updateFilter('minBookmakers', parseInt(value))}
        >
          <SelectTrigger className="w-[100px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="1">1+</SelectItem>
            <SelectItem value="2">2+</SelectItem>
            <SelectItem value="3">3</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Sort by */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">Sort by</label>
        <Select
          value={filters.sortBy}
          onValueChange={(value) =>
            updateFilter('sortBy', value as 'kickoff' | 'tournament')
          }
        >
          <SelectTrigger className="w-[120px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="kickoff">Kickoff</SelectItem>
            <SelectItem value="tournament">Tournament</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Clear filters button */}
      {hasActiveFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={clearFilters}
          className="text-muted-foreground"
        >
          <X className="w-4 h-4 mr-1" />
          Clear
        </Button>
      )}
    </div>
  )
}
