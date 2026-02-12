import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import { Checkbox } from '@/components/ui/checkbox'
import { useTournaments } from '../hooks/use-tournaments'
import { X, ChevronsUpDown } from 'lucide-react'

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
  search: string
  countryFilter: string[]
  tournamentIds: number[]
  kickoffFrom: string
  kickoffTo: string
  minBookmakers: number
  sortBy: 'kickoff' | 'tournament'
  availability: 'betpawa' | 'competitor'
}

interface MatchFiltersProps {
  filters: MatchFiltersState
  onFiltersChange: (filters: MatchFiltersState) => void
}

export function MatchFilters({ filters, onFiltersChange }: MatchFiltersProps) {
  const { data: tournaments, isPending: tournamentsLoading } = useTournaments()
  const [leaguePopoverOpen, setLeaguePopoverOpen] = useState(false)
  const [countryPopoverOpen, setCountryPopoverOpen] = useState(false)

  // Extract unique countries from tournaments
  const countries = Array.from(
    new Set(tournaments?.map((t) => t.country).filter((c): c is string => c !== null) ?? [])
  ).sort()

  // Filter tournaments by selected countries
  const filteredTournaments = filters.countryFilter.length > 0
    ? tournaments?.filter((t) => t.country && filters.countryFilter.includes(t.country))
    : tournaments

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

  const toggleTournament = (tournamentId: number) => {
    const currentIds = filters.tournamentIds
    const newIds = currentIds.includes(tournamentId)
      ? currentIds.filter((id) => id !== tournamentId)
      : [...currentIds, tournamentId]
    updateFilter('tournamentIds', newIds)
  }

  const clearAllTournaments = () => {
    updateFilter('tournamentIds', [])
  }

  const selectAllTournaments = () => {
    if (filteredTournaments) {
      updateFilter('tournamentIds', filteredTournaments.map((t) => t.id))
    }
  }

  const toggleCountry = (country: string) => {
    const currentCountries = filters.countryFilter
    const newCountries = currentCountries.includes(country)
      ? currentCountries.filter((c) => c !== country)
      : [...currentCountries, country]
    // Reset tournament filter when country filter changes
    onFiltersChange({ ...filters, countryFilter: newCountries, tournamentIds: [] })
  }

  const clearAllCountries = () => {
    // Also reset tournament filter when clearing countries
    onFiltersChange({ ...filters, countryFilter: [], tournamentIds: [] })
  }

  const selectAllCountries = () => {
    // Reset tournament filter when selecting all countries
    onFiltersChange({ ...filters, countryFilter: countries, tournamentIds: [] })
  }

  const clearFilters = () => {
    onFiltersChange({
      search: '',
      countryFilter: [],
      tournamentIds: [],
      kickoffFrom: '',
      kickoffTo: '',
      minBookmakers: 2,
      sortBy: 'kickoff',
      availability: 'betpawa',
    })
  }

  const hasActiveFilters =
    filters.search !== '' ||
    filters.countryFilter.length > 0 ||
    filters.tournamentIds.length > 0 ||
    filters.kickoffFrom !== '' ||
    filters.kickoffTo !== '' ||
    filters.minBookmakers !== 2

  return (
    <div className="flex flex-wrap items-end gap-4 p-4 bg-muted/30 rounded-lg">
      {/* Team search */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">Team</label>
        <Input
          type="text"
          placeholder="Search team..."
          value={filters.search}
          onChange={(e) => updateFilter('search', e.target.value)}
          className="w-[160px]"
        />
      </div>

      {/* Country filter - searchable multi-select */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">Country</label>
        <Popover open={countryPopoverOpen} onOpenChange={setCountryPopoverOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              role="combobox"
              aria-expanded={countryPopoverOpen}
              className="w-[160px] justify-between font-normal"
              disabled={tournamentsLoading}
            >
              {filters.countryFilter.length === 0
                ? 'All countries'
                : `${filters.countryFilter.length} ${filters.countryFilter.length === 1 ? 'country' : 'countries'}`}
              <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[250px] p-0" align="start">
            <Command>
              <CommandInput placeholder="Search countries..." />
              <CommandList>
                <CommandEmpty>No countries found.</CommandEmpty>
                <CommandGroup>
                  {countries.map((country) => (
                    <CommandItem
                      key={country}
                      value={country}
                      onSelect={() => toggleCountry(country)}
                    >
                      <Checkbox
                        checked={filters.countryFilter.includes(country)}
                        className="mr-2"
                      />
                      <span className="truncate flex-1">{country}</span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
              <div className="flex items-center justify-between border-t p-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearAllCountries}
                  className="text-xs"
                >
                  Clear all
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={selectAllCountries}
                  className="text-xs"
                >
                  Select all
                </Button>
              </div>
            </Command>
          </PopoverContent>
        </Popover>
      </div>

      {/* League filter - searchable multi-select */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">League</label>
        <Popover open={leaguePopoverOpen} onOpenChange={setLeaguePopoverOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              role="combobox"
              aria-expanded={leaguePopoverOpen}
              className="w-[200px] justify-between font-normal"
              disabled={tournamentsLoading}
            >
              {filters.tournamentIds.length === 0
                ? 'All leagues'
                : `${filters.tournamentIds.length} league${filters.tournamentIds.length > 1 ? 's' : ''}`}
              <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[300px] p-0" align="start">
            <Command>
              <CommandInput placeholder="Search leagues..." />
              <CommandList>
                <CommandEmpty>No leagues found.</CommandEmpty>
                <CommandGroup>
                  {filteredTournaments?.map((t) => (
                    <CommandItem
                      key={t.id}
                      value={`${t.name} ${t.country ?? ''}`}
                      onSelect={() => toggleTournament(t.id)}
                    >
                      <Checkbox
                        checked={filters.tournamentIds.includes(t.id)}
                        className="mr-2"
                      />
                      <span className="truncate flex-1">{t.name}</span>
                      {t.country && (
                        <span className="ml-2 text-xs text-muted-foreground shrink-0">
                          {t.country}
                        </span>
                      )}
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
              <div className="flex items-center justify-between border-t p-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={clearAllTournaments}
                  className="text-xs"
                >
                  Clear all
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={selectAllTournaments}
                  className="text-xs"
                >
                  Select all
                </Button>
              </div>
            </Command>
          </PopoverContent>
        </Popover>
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
