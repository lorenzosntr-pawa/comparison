import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useSettings, useUpdateSettings } from '../hooks'

const RETENTION_OPTIONS = [
  { value: '7', label: '7 days' },
  { value: '14', label: '14 days' },
  { value: '30', label: '30 days' },
  { value: '60', label: '60 days' },
  { value: '90', label: '90 days' },
  { value: '180', label: '180 days' },
  { value: '365', label: '1 year' },
]

interface RetentionSelectorProps {
  field: 'oddsRetentionDays' | 'matchRetentionDays'
}

export function RetentionSelector({ field }: RetentionSelectorProps) {
  const { data: settings } = useSettings()
  const { mutate: updateSettings, isPending } = useUpdateSettings()

  const value = settings?.[field]?.toString() ?? '30'

  const handleChange = (newValue: string) => {
    updateSettings({ [field]: parseInt(newValue, 10) })
  }

  return (
    <Select value={value} onValueChange={handleChange} disabled={isPending}>
      <SelectTrigger className="w-full">
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {RETENTION_OPTIONS.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
