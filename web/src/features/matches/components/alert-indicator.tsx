/**
 * Alert indicator badge for event rows and headers.
 *
 * @module alert-indicator
 * @description Shows alert count with severity-colored badge and navigation to Risk Monitoring.
 */

import { useNavigate } from 'react-router'
import { Badge } from '@/components/ui/badge'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

export interface AlertIndicatorProps {
  /** Number of alerts for this event */
  count: number
  /** Maximum severity level of alerts */
  maxSeverity: 'warning' | 'elevated' | 'critical' | null
  /** Event ID for navigation */
  eventId: number
  /** Badge size */
  size?: 'sm' | 'md'
}

/** Severity color classes for Tailwind JIT */
const SEVERITY_COLORS = {
  warning: 'bg-yellow-500 text-yellow-950 hover:bg-yellow-600',
  elevated: 'bg-orange-500 text-orange-950 hover:bg-orange-600',
  critical: 'bg-red-500 text-white hover:bg-red-600',
} as const

/** Size classes */
const SIZE_CLASSES = {
  sm: 'px-1.5 py-0.5 text-[10px]',
  md: 'px-2 py-0.5 text-xs',
} as const

/**
 * Alert indicator showing count badge with severity color.
 * Clicking navigates to Risk Monitoring filtered by event.
 */
export function AlertIndicator({
  count,
  maxSeverity,
  eventId,
  size = 'sm',
}: AlertIndicatorProps) {
  const navigate = useNavigate()

  // Don't render if no alerts
  if (count === 0 || maxSeverity === null) {
    return null
  }

  const displayCount = count > 99 ? '99+' : count.toString()
  const tooltipText = `${count} alert${count !== 1 ? 's' : ''} - click to view`

  const handleClick = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    navigate(`/risk-monitoring?event_id=${eventId}`)
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge
          className={cn(
            'cursor-pointer border-transparent',
            SEVERITY_COLORS[maxSeverity],
            SIZE_CLASSES[size]
          )}
          onClick={handleClick}
        >
          {displayCount}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>
        <p>{tooltipText}</p>
      </TooltipContent>
    </Tooltip>
  )
}
