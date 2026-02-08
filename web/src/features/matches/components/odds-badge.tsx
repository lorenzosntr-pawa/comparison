import { cn } from '@/lib/utils'

interface OddsBadgeProps {
  odds: number | null
  isBest: boolean
  isWorst: boolean
  isSuspended: boolean
  betpawaOdds?: number | null
  onClick?: (e: React.MouseEvent) => void
}

/**
 * OddsBadge displays an odds value with color coding.
 *
 * Color logic:
 * - Green: This is the best odds among all bookmakers
 * - Red: This is NOT the best and is worse than Betpawa by >3%
 * - Gray/strikethrough: Suspended selection
 * - Neutral: All other cases
 */
export function OddsBadge({
  odds,
  isBest,
  isWorst,
  isSuspended,
  betpawaOdds,
  onClick,
}: OddsBadgeProps) {
  if (odds === null) {
    return <span className="text-muted-foreground">-</span>
  }

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
