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
          <span className={cn('text-xs cursor-help', textClass)}>
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
