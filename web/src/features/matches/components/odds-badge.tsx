import { cn } from '@/lib/utils'
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { formatUnavailableSince } from '../lib/market-utils'

interface OddsBadgeProps {
  odds: number | null
  isBest: boolean
  isWorst: boolean
  isSuspended: boolean
  betpawaOdds?: number | null
  onClick?: (e: React.MouseEvent) => void
  /** Whether the market is currently available (default true) */
  available?: boolean
  /** ISO timestamp when market became unavailable */
  unavailableSince?: string | null
}

/**
 * OddsBadge displays an odds value with color coding.
 *
 * Color logic:
 * - Green: This is the best odds among all bookmakers
 * - Red: This is NOT the best and is worse than Betpawa by >3%
 * - Gray/strikethrough: Suspended selection or unavailable market
 * - Neutral: All other cases
 *
 * Availability states:
 * - available (default): Normal odds display
 * - unavailable: Strikethrough with tooltip showing when it became unavailable
 * - never_offered: Plain dash (odds is null, available is true/undefined)
 */
export function OddsBadge({
  odds,
  isBest,
  isWorst,
  isSuspended,
  betpawaOdds,
  onClick,
  available,
  unavailableSince,
}: OddsBadgeProps) {
  // Determine availability state
  const isUnavailable = available === false

  // Case 1: No odds and unavailable → strikethrough dash with tooltip
  if (odds === null && isUnavailable) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <span className="text-muted-foreground line-through cursor-help">-</span>
        </TooltipTrigger>
        <TooltipContent>
          <p>{unavailableSince ? formatUnavailableSince(unavailableSince) : 'Market unavailable'}</p>
        </TooltipContent>
      </Tooltip>
    )
  }

  // Case 2: No odds and available/undefined → plain dash (never_offered)
  if (odds === null) {
    return <span className="text-muted-foreground">-</span>
  }

  // Case 3: Has odds but unavailable → strikethrough odds with tooltip
  if (isUnavailable) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={cn(
              'inline-flex items-center justify-center px-2 py-0.5 rounded text-sm font-medium min-w-[3rem]',
              'text-muted-foreground line-through cursor-help'
            )}
          >
            {odds.toFixed(2)}
          </span>
        </TooltipTrigger>
        <TooltipContent>
          <p>{unavailableSince ? formatUnavailableSince(unavailableSince) : 'Market unavailable'}</p>
        </TooltipContent>
      </Tooltip>
    )
  }

  // Case 4: Has odds and available → normal rendering
  // Calculate if significantly worse than Betpawa (>3% lower odds)
  const isSignificantlyWorse =
    betpawaOdds !== null &&
    betpawaOdds !== undefined &&
    odds < betpawaOdds * 0.97

  // Determine styling
  let bgClass = ''
  let textClass = ''

  if (isSuspended) {
    textClass = 'text-muted-foreground line-through'
  } else if (isBest) {
    bgClass = 'bg-green-100 dark:bg-green-900/30'
    textClass = 'text-green-700 dark:text-green-400'
  } else if (isWorst || isSignificantlyWorse) {
    bgClass = 'bg-red-100 dark:bg-red-900/30'
    textClass = 'text-red-700 dark:text-red-400'
  }

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center px-2 py-0.5 rounded text-sm font-medium min-w-[3rem]',
        bgClass,
        textClass,
        onClick && 'cursor-pointer hover:ring-1 hover:ring-primary/50'
      )}
      onClick={(e) => onClick?.(e)}
    >
      {odds.toFixed(2)}
    </span>
  )
}
