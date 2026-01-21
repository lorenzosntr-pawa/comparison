import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useSettings, useUpdateSettings } from '../hooks'

const INTERVAL_OPTIONS = [
  { value: '5', label: '5 minutes' },
  { value: '10', label: '10 minutes' },
  { value: '15', label: '15 minutes' },
  { value: '30', label: '30 minutes' },
]

export function IntervalSelector() {
  const { data: settings } = useSettings()
  const { mutate: updateSettings, isPending } = useUpdateSettings()

  const handleChange = (value: string) => {
    updateSettings({ scrapeIntervalMinutes: parseInt(value, 10) })
  }

  return (
    <div className="flex items-center justify-between">
      <div className="space-y-0.5">
        <div className="text-sm font-medium">Scrape Interval</div>
        <div className="text-sm text-muted-foreground">
          How often to fetch odds from bookmakers
        </div>
      </div>
      <Select
        value={settings?.scrapeIntervalMinutes?.toString() ?? ''}
        onValueChange={handleChange}
        disabled={isPending}
      >
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Select interval" />
        </SelectTrigger>
        <SelectContent>
          {INTERVAL_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
