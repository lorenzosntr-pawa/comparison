import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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
import { Calendar, Search, ChevronsUpDown } from 'lucide-react'
import { format, subDays } from 'date-fns'
import { BookmakerFilter } from './bookmaker-filter'

export interface DateRange {
  from?: Date
  to?: Date
}

interface FilterBarProps {
  dateRange: DateRange
  onDateRangeChange: (range: DateRange) => void
  selectedBookmakers: string[]
  onBookmakersChange: (selected: string[]) => void
  searchQuery: string
  onSearchChange: (query: string) => void
  availableCountries: string[]
  selectedCountries: string[]
  onCountriesChange: (countries: string[]) => void
}

function formatDateForInput(date: Date | undefined): string {
  if (!date) return ''
  return format(date, 'yyyy-MM-dd')
}

function formatDateForDisplay(date: Date | undefined): string {
  if (!date) return 'Select date'
  return format(date, 'MMM d, yyyy')
}

export function FilterBar({
  dateRange,
  onDateRangeChange,
  selectedBookmakers,
  onBookmakersChange,
  searchQuery,
  onSearchChange,
  availableCountries,
  selectedCountries,
  onCountriesChange,
}: FilterBarProps) {
  const [countryPopoverOpen, setCountryPopoverOpen] = useState(false)

  const toggleCountry = (country: string) => {
    if (selectedCountries.includes(country)) {
      onCountriesChange(selectedCountries.filter((c) => c !== country))
    } else {
      onCountriesChange([...selectedCountries, country])
    }
  }

  const clearAllCountries = () => {
    onCountriesChange([])
  }

  const selectAllCountries = () => {
    onCountriesChange(availableCountries)
  }

  const handleFromChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    const date = value ? new Date(value + 'T00:00:00') : undefined
    onDateRangeChange({ ...dateRange, from: date })
  }

  const handleToChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    const date = value ? new Date(value + 'T23:59:59') : undefined
    onDateRangeChange({ ...dateRange, to: date })
  }

  const applyPreset = (days: number) => {
    const today = new Date()
    today.setHours(23, 59, 59, 999)
    const from = subDays(today, days)
    from.setHours(0, 0, 0, 0)
    onDateRangeChange({ from, to: today })
  }

  return (
    <div className="flex flex-wrap items-end gap-4 p-4 bg-muted/30 rounded-lg">
      {/* Quick presets */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">
          Quick Select
        </label>
        <div className="flex items-center gap-1">
          <Button
            variant="outline"
            size="sm"
            onClick={() => applyPreset(7)}
            className="h-9 px-3 text-xs"
          >
            Last 7 days
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => applyPreset(30)}
            className="h-9 px-3 text-xs"
          >
            Last 30 days
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => applyPreset(90)}
            className="h-9 px-3 text-xs"
          >
            Last 90 days
          </Button>
        </div>
      </div>

      {/* Tournament search */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">
          Search
        </label>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            type="text"
            placeholder="Search tournaments..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-[200px] pl-10"
          />
        </div>
      </div>

      {/* Country filter */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">
          Country
        </label>
        <Popover open={countryPopoverOpen} onOpenChange={setCountryPopoverOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              role="combobox"
              aria-expanded={countryPopoverOpen}
              className="w-[160px] justify-between font-normal"
            >
              {selectedCountries.length === 0
                ? 'All countries'
                : `${selectedCountries.length} ${selectedCountries.length === 1 ? 'country' : 'countries'}`}
              <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[250px] p-0" align="start">
            <Command>
              <CommandInput placeholder="Search countries..." />
              <CommandList>
                <CommandEmpty>No countries found.</CommandEmpty>
                <CommandGroup>
                  {availableCountries.map((country) => (
                    <CommandItem
                      key={country}
                      value={country}
                      onSelect={() => toggleCountry(country)}
                    >
                      <Checkbox
                        checked={selectedCountries.includes(country)}
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

      {/* Bookmaker filter */}
      <BookmakerFilter
        selected={selectedBookmakers}
        onChange={onBookmakersChange}
      />

      {/* From date */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">From</label>
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            type="date"
            value={formatDateForInput(dateRange.from)}
            onChange={handleFromChange}
            className="w-[180px] pl-10"
          />
        </div>
      </div>

      {/* To date */}
      <div className="flex flex-col gap-1.5">
        <label className="text-xs font-medium text-muted-foreground">To</label>
        <div className="relative">
          <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            type="date"
            value={formatDateForInput(dateRange.to)}
            onChange={handleToChange}
            className="w-[180px] pl-10"
          />
        </div>
      </div>

      {/* Selected range display */}
      {dateRange.from && dateRange.to && (
        <div className="flex items-center text-sm text-muted-foreground">
          <span>
            {formatDateForDisplay(dateRange.from)} - {formatDateForDisplay(dateRange.to)}
          </span>
        </div>
      )}
    </div>
  )
}
