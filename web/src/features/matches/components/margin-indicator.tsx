import { cn } from '@/lib/utils'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'

interface MarginIndicatorProps {
  margin: number
  betpawaMargin: number | null
  onClick?: (e: React.MouseEvent) => void
}

/**
 * MarginIndicator displays a market's margin percentage with comparison to Betpawa.
 *
 * Color logic:
 * - Green: Lower margin than Betpawa (better for punter)
 * - Red: Higher margin than Betpawa (worse for punter)
 * - Neutral: Within 0.5% of Betpawa
 */
export function MarginIndicator({
  margin,
  betpawaMargin,
  onClick,
}: MarginIndicatorProps) {
  // Calculate difference from Betpawa
  const marginDiff =
    betpawaMargin !== null ? margin - betpawaMargin : null

  // Determine color based on comparison
  let textClass = 'text-muted-foreground'
  if (marginDiff !== null) {
    if (marginDiff < -0.5) {
      // Lower margin = better value for punter
      textClass = 'text-green-600 dark:text-green-400'
    } else if (marginDiff > 0.5) {
      // Higher margin = worse value for punter
      textClass = 'text-red-600 dark:text-red-400'
    }
  }

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span
            className={cn(
              'text-xs',
              textClass,
              onClick ? 'cursor-pointer hover:ring-1 hover:ring-primary/50' : 'cursor-help'
            )}
            onClick={(e) => {
              if (onClick) {
                e.stopPropagation()
                onClick(e)
              }
            }}
          >
            {margin.toFixed(1)}%
          </span>
        </TooltipTrigger>
        <TooltipContent>
          <p className="text-sm">
            Margin: {margin.toFixed(2)}%
            {marginDiff !== null && (
              <>
                <br />
                vs Betpawa: {marginDiff > 0 ? '+' : ''}
                {marginDiff.toFixed(2)}%
                <br />
                <span className="text-xs text-muted-foreground">
                  Lower margin = better value
                </span>
              </>
            )}
          </p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
