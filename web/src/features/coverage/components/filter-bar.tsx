import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'
import { Search } from 'lucide-react'
import { CountryMultiSelect } from './country-multi-select'

export type AvailabilityFilter =
  | 'all'
  | 'matched'
  | 'betpawa-only'
  | 'competitor-only'

export interface CoverageFilters {
  availability: AvailabilityFilter
  search: string
  countries: string[]
}

interface CoverageFilterBarProps {
  filters: CoverageFilters
  onFiltersChange: (filters: CoverageFilters) => void
  countries?: string[]
}

const availabilityOptions: { value: AvailabilityFilter; label: string }[] = [
  { value: 'all', label: 'All Events' },
  { value: 'matched', label: 'Matched' },
  { value: 'betpawa-only', label: 'BetPawa Only' },
  { value: 'competitor-only', label: 'Gaps' },
]

export function CoverageFilterBar({
  filters,
  onFiltersChange,
  countries,
}: CoverageFilterBarProps) {
  const updateFilter = <K extends keyof CoverageFilters>(
    key: K,
    value: CoverageFilters[K]
  ) => {
    onFiltersChange({ ...filters, [key]: value })
  }

  return (
    <div className="flex flex-wrap items-center gap-4">
      {/* Availability toggle */}
      <div className="inline-flex h-9 items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground">
        {availabilityOptions.map((option) => (
          <Button
            key={option.value}
            type="button"
            variant="ghost"
            size="sm"
            className={cn(
              'h-7 px-3 text-xs font-medium',
              filters.availability === option.value &&
                'bg-background text-foreground shadow-sm'
            )}
            onClick={() => updateFilter('availability', option.value)}
          >
            {option.label}
          </Button>
        ))}
      </div>

      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search tournaments or teams..."
          value={filters.search}
          onChange={(e) => updateFilter('search', e.target.value)}
          className="w-64 pl-9"
        />
      </div>

      {/* Country filter - only shown if countries provided */}
      {countries && countries.length > 0 && (
        <CountryMultiSelect
          countries={countries}
          selected={filters.countries}
          onSelectedChange={(selected) => updateFilter('countries', selected)}
        />
      )}
    </div>
  )
}
