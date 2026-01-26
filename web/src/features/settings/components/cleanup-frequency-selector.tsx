import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useSettings, useUpdateSettings } from '../hooks'

const FREQUENCY_OPTIONS = [
  { value: '6', label: '6 hours' },
  { value: '12', label: '12 hours' },
  { value: '24', label: '1 day' },
  { value: '48', label: '2 days' },
  { value: '72', label: '3 days' },
  { value: '168', label: '1 week' },
]

export function CleanupFrequencySelector() {
  const { data: settings } = useSettings()
  const { mutate: updateSettings, isPending } = useUpdateSettings()

  const value = settings?.cleanupFrequencyHours?.toString() ?? '24'

  const handleChange = (newValue: string) => {
    updateSettings({ cleanupFrequencyHours: parseInt(newValue, 10) })
  }

  return (
    <Select value={value} onValueChange={handleChange} disabled={isPending}>
      <SelectTrigger className="w-full">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {FREQUENCY_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
