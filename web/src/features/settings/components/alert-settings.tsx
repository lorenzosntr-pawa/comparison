import { Label } from '@/components/ui/label'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useSettings, useUpdateSettings } from '../hooks'

/**
 * Toggle switch for enabling/disabling alert detection.
 */
export function AlertEnabledToggle() {
  const { data: settings } = useSettings()
  const { mutate: updateSettings, isPending } = useUpdateSettings()

  const enabled = settings?.alertEnabled ?? true

  const handleChange = (checked: boolean) => {
    updateSettings({ alertEnabled: checked })
  }

  return (
    <div className="flex items-center justify-between">
      <div className="space-y-0.5">
        <Label htmlFor="alert-enabled" className="text-sm font-medium">
          Enable Alerts
        </Label>
        <p className="text-xs text-muted-foreground">
          Detect and notify on significant odds movements
        </p>
      </div>
      <Switch
        id="alert-enabled"
        checked={enabled}
        onCheckedChange={handleChange}
        disabled={isPending}
      />
    </div>
  )
}

const ALERT_RETENTION_OPTIONS = [
  { value: '1', label: '1 day' },
  { value: '3', label: '3 days' },
  { value: '7', label: '7 days' },
  { value: '14', label: '14 days' },
  { value: '30', label: '30 days' },
  { value: '60', label: '60 days' },
  { value: '90', label: '90 days' },
]

/**
 * Dropdown selector for alert retention period.
 */
export function AlertRetentionSelector() {
  const { data: settings } = useSettings()
  const { mutate: updateSettings, isPending } = useUpdateSettings()

  const value = settings?.alertRetentionDays?.toString() ?? '7'

  const handleChange = (newValue: string) => {
    updateSettings({ alertRetentionDays: parseInt(newValue, 10) })
  }

  return (
    <div className="space-y-1.5">
      <Label className="text-sm font-medium">Alert Retention</Label>
      <Select value={value} onValueChange={handleChange} disabled={isPending}>
        <SelectTrigger className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {ALERT_RETENTION_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

interface AlertThresholdInputProps {
  label: string
  field: 'alertThresholdWarning' | 'alertThresholdElevated' | 'alertThresholdCritical'
  min?: number
  max?: number
}

/**
 * Number input for alert threshold configuration.
 * Shows threshold as percentage.
 */
export function AlertThresholdInput({
  label,
  field,
  min = 1,
  max = 100,
}: AlertThresholdInputProps) {
  const { data: settings } = useSettings()
  const { mutate: updateSettings, isPending } = useUpdateSettings()

  const value = settings?.[field] ?? (field === 'alertThresholdWarning' ? 7 : field === 'alertThresholdElevated' ? 10 : 15)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = parseFloat(e.target.value)
    if (!isNaN(newValue) && newValue >= min && newValue <= max) {
      updateSettings({ [field]: newValue })
    }
  }

  const handleBlur = (e: React.FocusEvent<HTMLInputElement>) => {
    const newValue = parseFloat(e.target.value)
    if (isNaN(newValue) || newValue < min) {
      e.target.value = min.toString()
      updateSettings({ [field]: min })
    } else if (newValue > max) {
      e.target.value = max.toString()
      updateSettings({ [field]: max })
    }
  }

  // Color indicator based on severity
  const colorClass =
    field === 'alertThresholdWarning'
      ? 'border-l-yellow-500'
      : field === 'alertThresholdElevated'
        ? 'border-l-orange-500'
        : 'border-l-red-500'

  return (
    <div className="space-y-1.5">
      <Label className="text-sm font-medium">{label}</Label>
      <div className="relative">
        <Input
          type="number"
          step="0.5"
          min={min}
          max={max}
          defaultValue={value}
          onChange={handleChange}
          onBlur={handleBlur}
          disabled={isPending}
          className={`pr-8 border-l-4 ${colorClass}`}
        />
        <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
          %
        </span>
      </div>
    </div>
  )
}
