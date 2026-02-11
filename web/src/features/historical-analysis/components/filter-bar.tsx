import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Calendar } from 'lucide-react'
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
}: FilterBarProps) {
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
