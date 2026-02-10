import { useMemo } from 'react'
import { cn } from '@/lib/utils'

interface ComparisonTableProps {
  /** The locked data point from chart (keys are bookmaker slugs or outcome names) */
  lockedData: Record<string, unknown>
  /** List of outcome names (rows in comparison mode, columns in single mode) */
  outcomeNames: string[]
  /** List of bookmaker slugs */
  bookmakerSlugs: string[]
  /** Bookmaker slug -> display name mapping */
  bookmakerNames: Record<string, string>
  /** Mode: 'comparison' for multi-bookmaker, 'single' for one bookmaker multi-outcome */
  mode: 'comparison' | 'single'
  /** Whether to show margin row at bottom */
  showMargin?: boolean
  /** Margin data keyed by bookmaker slug (for comparison mode) */
  marginData?: Record<string, number | null>
}

/**
 * ComparisonTable displays locked timestamp data with best/worst highlighting.
 *
 * In comparison mode: outcomes as rows, bookmakers as columns, with delta vs Betpawa.
 * In single mode: outcomes with their odds values.
 *
 * Color logic:
 * - Green background: Best value for that row (highest odds / lowest margin)
 * - Red background: Significantly worse than Betpawa (>3% lower odds / >0.5% higher margin)
 */
export function ComparisonTable({
  lockedData,
  outcomeNames,
  bookmakerSlugs,
  bookmakerNames,
  mode,
  showMargin = false,
  marginData,
}: ComparisonTableProps) {
  // Order bookmakers: betpawa first, then alphabetically
  const orderedSlugs = useMemo(() => {
    const sorted = [...bookmakerSlugs].sort((a, b) => {
      if (a === 'betpawa') return -1
      if (b === 'betpawa') return 1
      return a.localeCompare(b)
    })
    return sorted
  }, [bookmakerSlugs])

  // Helper to get odds value from locked data
  const getOddsValue = (key: string): number | null => {
    const value = lockedData[key]
    return typeof value === 'number' ? value : null
  }

  // Find best (highest) and worst (lowest) odds for an outcome across bookmakers
  const getOutcomeStats = (outcomeName: string) => {
    const values: { slug: string; odds: number }[] = []

    if (mode === 'comparison') {
      // In comparison mode, lockedData keys are bookmaker slugs
      orderedSlugs.forEach((slug) => {
        const odds = getOddsValue(slug)
        if (odds !== null) {
          values.push({ slug, odds })
        }
      })
    }

    if (values.length === 0) {
      return { bestSlug: null, worstSlug: null, betpawaOdds: null }
    }

    const best = values.reduce((a, b) => (a.odds > b.odds ? a : b))
    const worst = values.reduce((a, b) => (a.odds < b.odds ? a : b))
    const betpawaOdds = values.find((v) => v.slug === 'betpawa')?.odds ?? null

    return { bestSlug: best.slug, worstSlug: worst.slug, betpawaOdds }
  }

  // Find best (lowest) and worst (highest) margin across bookmakers
  const getMarginStats = () => {
    if (!marginData) return { bestSlug: null, worstSlug: null, betpawaMargin: null }

    const values: { slug: string; margin: number }[] = []
    orderedSlugs.forEach((slug) => {
      const margin = marginData[slug]
      if (margin !== null && margin !== undefined) {
        values.push({ slug, margin })
      }
    })

    if (values.length === 0) {
      return { bestSlug: null, worstSlug: null, betpawaMargin: null }
    }

    // Best margin is LOWEST
    const best = values.reduce((a, b) => (a.margin < b.margin ? a : b))
    // Worst margin is HIGHEST
    const worst = values.reduce((a, b) => (a.margin > b.margin ? a : b))
    const betpawaMargin = values.find((v) => v.slug === 'betpawa')?.margin ?? null

    return { bestSlug: best.slug, worstSlug: worst.slug, betpawaMargin }
  }

  // Get cell styling based on whether it's best/worst/significantly worse than Betpawa
  const getOddsCellStyle = (
    odds: number | null,
    isBest: boolean,
    betpawaOdds: number | null,
    isBetpawa: boolean
  ) => {
    if (odds === null) return ''

    // Betpawa column never gets colored
    if (isBetpawa) return ''

    // Check if significantly worse than Betpawa (>3% lower odds)
    const isSignificantlyWorse =
      betpawaOdds !== null && odds < betpawaOdds * 0.97

    if (isBest) {
      return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
    }
    if (isSignificantlyWorse) {
      return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
    }
    return ''
  }

  // Get cell styling for margin values
  const getMarginCellStyle = (
    margin: number | null,
    isBest: boolean,
    betpawaMargin: number | null,
    isBetpawa: boolean
  ) => {
    if (margin === null) return ''

    // Betpawa column never gets colored
    if (isBetpawa) return ''

    // Check if significantly worse than Betpawa (>0.5% higher margin)
    const isSignificantlyWorse =
      betpawaMargin !== null && margin > betpawaMargin + 0.5

    if (isBest) {
      return 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400'
    }
    if (isSignificantlyWorse) {
      return 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400'
    }
    return ''
  }

  // Format delta value
  const formatDelta = (value: number | null, reference: number | null): string => {
    if (value === null || reference === null) return '-'
    const delta = value - reference
    if (delta === 0) return '-'
    return delta > 0 ? `+${delta.toFixed(2)}` : delta.toFixed(2)
  }

  // Format margin delta
  const formatMarginDelta = (value: number | null, reference: number | null): string => {
    if (value === null || reference === null) return '-'
    const delta = value - reference
    if (Math.abs(delta) < 0.01) return '-'
    return delta > 0 ? `+${delta.toFixed(1)}%` : `${delta.toFixed(1)}%`
  }

  if (mode === 'single') {
    // Single bookmaker mode: simple list of outcomes
    return (
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-1 pr-4 font-medium">Outcome</th>
              <th className="text-right py-1 px-2 font-medium">Odds</th>
            </tr>
          </thead>
          <tbody>
            {outcomeNames.map((outcomeName) => {
              const value = lockedData[outcomeName]
              return (
                <tr key={outcomeName} className="border-b last:border-0">
                  <td className="py-1 pr-4 text-muted-foreground">{outcomeName}</td>
                  <td className="text-right py-1 px-2 font-medium">
                    {typeof value === 'number' ? value.toFixed(2) : '-'}
                  </td>
                </tr>
              )
            })}
            {showMargin && (
              <tr className="border-t-2">
                <td className="py-1 pr-4 text-muted-foreground font-medium">Margin</td>
                <td className="text-right py-1 px-2 font-medium">
                  {typeof lockedData.margin === 'number'
                    ? `${(lockedData.margin as number).toFixed(1)}%`
                    : '-'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    )
  }

  // Comparison mode: bookmakers as columns with delta columns
  const marginStats = getMarginStats()

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b">
            <th className="text-left py-1.5 pr-4 font-medium sticky left-0 bg-inherit">
              Outcome
            </th>
            {orderedSlugs.map((slug) => (
              <th
                key={slug}
                colSpan={slug === 'betpawa' ? 1 : 2}
                className="text-center py-1.5 px-2 font-medium"
              >
                {bookmakerNames[slug] || slug}
              </th>
            ))}
          </tr>
          <tr className="border-b text-xs text-muted-foreground">
            <th className="sticky left-0 bg-inherit"></th>
            {orderedSlugs.map((slug) =>
              slug === 'betpawa' ? (
                <th key={slug} className="py-1 px-2">Odds</th>
              ) : (
                <th key={slug} colSpan={2} className="py-1 px-2">
                  <div className="flex justify-center gap-3">
                    <span>Odds</span>
                    <span className="text-muted-foreground/70">vs BP</span>
                  </div>
                </th>
              )
            )}
          </tr>
        </thead>
        <tbody>
          {outcomeNames.map((outcomeName) => {
            // For now we only have one outcome's data in the locked point
            // Each row shows odds for that outcome from each bookmaker
            const stats = getOutcomeStats(outcomeName)

            return (
              <tr key={outcomeName} className="border-b last:border-0">
                <td className="py-1.5 pr-4 text-muted-foreground sticky left-0 bg-inherit">
                  {outcomeName}
                </td>
                {orderedSlugs.map((slug) => {
                  const odds = getOddsValue(slug)
                  const isBest = stats.bestSlug === slug
                  const isBetpawa = slug === 'betpawa'
                  const cellStyle = getOddsCellStyle(odds, isBest, stats.betpawaOdds, isBetpawa)

                  if (isBetpawa) {
                    return (
                      <td
                        key={slug}
                        className={cn(
                          'text-center py-1.5 px-2 font-medium',
                          cellStyle
                        )}
                      >
                        {odds !== null ? odds.toFixed(2) : '-'}
                        {isBest && odds !== null && (
                          <span className="ml-1 text-green-600 dark:text-green-400">*</span>
                        )}
                      </td>
                    )
                  }

                  return (
                    <td
                      key={slug}
                      colSpan={2}
                      className={cn('text-center py-1.5 px-2', cellStyle)}
                    >
                      <div className="flex justify-center gap-3 items-center">
                        <span className="font-medium">
                          {odds !== null ? odds.toFixed(2) : '-'}
                          {isBest && odds !== null && (
                            <span className="ml-1 text-green-600 dark:text-green-400">*</span>
                          )}
                        </span>
                        <span className="text-xs text-muted-foreground min-w-[3rem]">
                          {formatDelta(odds, stats.betpawaOdds)}
                        </span>
                      </div>
                    </td>
                  )
                })}
              </tr>
            )
          })}

          {/* Margin row */}
          {showMargin && marginData && (
            <tr className="border-t-2 bg-muted/30">
              <td className="py-1.5 pr-4 font-medium sticky left-0 bg-inherit">
                Margin
              </td>
              {orderedSlugs.map((slug) => {
                const margin = marginData[slug]
                const isBest = marginStats.bestSlug === slug
                const isBetpawa = slug === 'betpawa'
                const cellStyle = getMarginCellStyle(
                  margin ?? null,
                  isBest,
                  marginStats.betpawaMargin,
                  isBetpawa
                )

                if (isBetpawa) {
                  return (
                    <td
                      key={slug}
                      className={cn(
                        'text-center py-1.5 px-2 font-medium',
                        cellStyle
                      )}
                    >
                      {margin !== null && margin !== undefined
                        ? `${margin.toFixed(1)}%`
                        : '-'}
                      {isBest && margin !== null && (
                        <span className="ml-1 text-green-600 dark:text-green-400">*</span>
                      )}
                    </td>
                  )
                }

                return (
                  <td
                    key={slug}
                    colSpan={2}
                    className={cn('text-center py-1.5 px-2', cellStyle)}
                  >
                    <div className="flex justify-center gap-3 items-center">
                      <span className="font-medium">
                        {margin !== null && margin !== undefined
                          ? `${margin.toFixed(1)}%`
                          : '-'}
                        {isBest && margin !== null && (
                          <span className="ml-1 text-green-600 dark:text-green-400">*</span>
                        )}
                      </span>
                      <span className="text-xs text-muted-foreground min-w-[3rem]">
                        {formatMarginDelta(margin ?? null, marginStats.betpawaMargin)}
                      </span>
                    </div>
                  </td>
                )
              })}
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
