import { cn } from '@/lib/utils'

interface OddsCellProps {
  betpawaOdds: number | null
  competitorOdds: number | null
  showDelta?: boolean
}

/**
 * OddsCell displays an odds value with color coding based on comparison.
 *
 * Color logic:
 * - Green gradient: Betpawa odds > competitor (better for punter)
 * - Red gradient: Betpawa odds < competitor (worse for punter)
 * - Neutral: Equal or within 0.02 tolerance
 *
 * Gradient intensity based on delta magnitude.
 */
export function OddsCell({ betpawaOdds, competitorOdds, showDelta = false }: OddsCellProps) {
  if (betpawaOdds === null) {
    return <span className="text-muted-foreground">-</span>
  }

  // Calculate delta if competitor odds available
  const delta = competitorOdds !== null ? betpawaOdds - competitorOdds : 0
  const tolerance = 0.02

  // Determine color based on comparison
  let bgClass = ''
  if (competitorOdds !== null && Math.abs(delta) > tolerance) {
    // Calculate intensity: min(|delta| * 20, 100) -> 0-100 range
    // Map to Tailwind opacity: 10, 20, 30, 40, 50
    const intensity = Math.min(Math.abs(delta) * 20, 1)
    const opacityLevel = Math.ceil(intensity * 5) * 10 // 10, 20, 30, 40, 50

    if (delta > tolerance) {
      // Betpawa better (higher odds = better for punter)
      bgClass = `bg-green-500/${opacityLevel}`
    } else if (delta < -tolerance) {
      // Betpawa worse
      bgClass = `bg-red-500/${opacityLevel}`
    }
  }

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center px-2 py-1 rounded text-sm font-medium min-w-[3rem]',
        bgClass
      )}
    >
      {betpawaOdds.toFixed(2)}
      {showDelta && competitorOdds !== null && Math.abs(delta) > tolerance && (
        <span className="ml-1 text-xs opacity-70">
          ({delta > 0 ? '+' : ''}{delta.toFixed(2)})
        </span>
      )}
    </span>
  )
}

interface ComparisonOddsCellProps {
  odds: number | null
  isBetpawa?: boolean
}

/**
 * Simple odds cell for displaying a single odds value.
 * Used in the comparison table for each bookmaker.
 */
export function ComparisonOddsCell({ odds, isBetpawa = false }: ComparisonOddsCellProps) {
  if (odds === null) {
    return <span className="text-muted-foreground">-</span>
  }

  return (
    <span
      className={cn(
        'inline-flex items-center justify-center px-2 py-1 rounded text-sm font-medium min-w-[3rem]',
        isBetpawa && 'font-bold'
      )}
    >
      {odds.toFixed(2)}
    </span>
  )
}
