/**
 * Bar chart component showing margin difference between Betpawa and competitors.
 *
 * @module difference-bar-chart
 * @description Displays margin gaps by time bucket with colored bars:
 * green = Betpawa has lower margin (better for bettors),
 * red = Betpawa has higher margin (worse for bettors).
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts'
import type { BucketStats } from '../hooks/use-tournament-markets'

/**
 * Props for DifferenceBarChart component.
 */
export interface DifferenceBarChartProps {
  /** Betpawa's bucket statistics */
  betpawaBuckets: BucketStats[]
  /** Competitor bucket statistics keyed by bookmaker slug */
  competitorBuckets: Record<string, BucketStats[]>
  /** Which competitor to compare (default: 'best' for best competitor) */
  selectedCompetitor?: string
  /** Chart height in pixels */
  height?: number
}

/**
 * Data structure for a single difference bar.
 */
interface DifferenceBucket {
  /** Time bucket label */
  bucket: string
  /** Margin difference (Betpawa - Competitor) */
  difference: number
  /** Betpawa margin at this bucket */
  betpawaMargin: number
  /** Competitor margin at this bucket */
  competitorMargin: number
  /** Competitor name for tooltip */
  competitorName: string
}

/**
 * Format bucket label for display.
 */
function formatBucketLabel(bucket: string): string {
  switch (bucket) {
    case '7d+':
      return '7+ days'
    case '3-7d':
      return '3-7 days'
    case '24-72h':
      return '24-72h'
    case '<24h':
      return '< 24h'
    default:
      return bucket
  }
}

/** Bookmaker display labels */
const BOOKMAKER_LABELS: Record<string, string> = {
  sportybet: 'SportyBet',
  bet9ja: 'Bet9ja',
  best: 'Best Competitor',
}

/**
 * Custom tooltip for the difference chart.
 */
function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: Array<{ payload: DifferenceBucket }>
}) {
  if (!active || !payload?.length) return null

  const data = payload[0].payload
  const diffSign = data.difference >= 0 ? '+' : ''
  const diffLabel =
    data.difference >= 0
      ? 'Betpawa higher margin'
      : 'Betpawa lower margin'

  return (
    <div className="bg-popover border border-border rounded-md p-3 text-sm shadow-md">
      <div className="font-medium mb-2">{formatBucketLabel(data.bucket)}</div>
      <div className="space-y-1 text-muted-foreground">
        <div className="flex justify-between gap-4">
          <span>Betpawa:</span>
          <span className="font-medium text-foreground">
            {data.betpawaMargin.toFixed(1)}%
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span>{data.competitorName}:</span>
          <span className="font-medium text-foreground">
            {data.competitorMargin.toFixed(1)}%
          </span>
        </div>
        <div className="border-t pt-1 mt-1">
          <div className="flex justify-between gap-4">
            <span>Difference:</span>
            <span
              className={`font-semibold ${data.difference >= 0 ? 'text-red-600' : 'text-green-600'}`}
            >
              {diffSign}{data.difference.toFixed(1)}%
            </span>
          </div>
          <div className="text-xs mt-1 text-muted-foreground">
            ({diffLabel})
          </div>
        </div>
      </div>
    </div>
  )
}

/**
 * Bar chart showing Betpawa vs competitor margin difference by time bucket.
 *
 * Positive bars (red) = Betpawa has higher margin than competitor.
 * Negative bars (green) = Betpawa has lower margin (more competitive).
 */
export function DifferenceBarChart({
  betpawaBuckets,
  competitorBuckets,
  selectedCompetitor = 'best',
  height = 200,
}: DifferenceBarChartProps) {
  // Index Betpawa buckets by bucket name
  const betpawaByBucket = new Map<string, BucketStats>()
  for (const stat of betpawaBuckets) {
    betpawaByBucket.set(stat.bucket, stat)
  }

  // Calculate difference data
  const differenceData: DifferenceBucket[] = []
  const bucketOrder = ['7d+', '3-7d', '24-72h', '<24h']

  for (const bucket of bucketOrder) {
    const betpawaStat = betpawaByBucket.get(bucket)
    if (!betpawaStat || betpawaStat.pointCount === 0) continue

    let competitorMargin: number | null = null
    let competitorName: string

    if (selectedCompetitor === 'best') {
      // Find best (lowest) competitor margin for this bucket
      let bestMargin: number | null = null
      let bestName = 'Best Competitor'

      for (const [slug, stats] of Object.entries(competitorBuckets)) {
        const stat = stats.find((s) => s.bucket === bucket)
        if (stat && stat.pointCount > 0) {
          if (bestMargin === null || stat.avgMargin < bestMargin) {
            bestMargin = stat.avgMargin
            bestName = BOOKMAKER_LABELS[slug] || slug
          }
        }
      }

      competitorMargin = bestMargin
      competitorName = bestMargin !== null ? bestName : 'Best Competitor'
    } else {
      // Use specific competitor
      const stats = competitorBuckets[selectedCompetitor]
      const stat = stats?.find((s) => s.bucket === bucket)
      if (stat && stat.pointCount > 0) {
        competitorMargin = stat.avgMargin
      }
      competitorName = BOOKMAKER_LABELS[selectedCompetitor] || selectedCompetitor
    }

    // Only add bucket if we have both Betpawa and competitor data
    if (competitorMargin !== null) {
      differenceData.push({
        bucket,
        difference: betpawaStat.avgMargin - competitorMargin,
        betpawaMargin: betpawaStat.avgMargin,
        competitorMargin,
        competitorName,
      })
    }
  }

  if (differenceData.length === 0) {
    return (
      <div
        className="flex flex-col items-center justify-center text-muted-foreground gap-2"
        style={{ height }}
      >
        <span>No comparison data available</span>
        <span className="text-xs">
          (Need competitor data for at least one time bucket)
        </span>
      </div>
    )
  }

  // Calculate Y-axis domain with padding
  const maxDiff = Math.max(...differenceData.map((d) => Math.abs(d.difference)))
  const yPadding = Math.max(0.5, maxDiff * 0.2)

  return (
    <div className="space-y-3">
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={differenceData}
          margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis
            dataKey="bucket"
            tick={{ fontSize: 11 }}
            tickFormatter={formatBucketLabel}
            className="text-muted-foreground"
          />
          <YAxis
            tick={{ fontSize: 11 }}
            tickFormatter={(v) =>
              typeof v === 'number'
                ? `${v >= 0 ? '+' : ''}${v.toFixed(1)}%`
                : ''
            }
            domain={[-maxDiff - yPadding, maxDiff + yPadding]}
            width={55}
            className="text-muted-foreground"
          />
          <ReferenceLine y={0} stroke="#888" strokeDasharray="3 3" />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="difference" radius={[4, 4, 0, 0]}>
            {differenceData.map((entry, index) => (
              <Cell
                key={index}
                fill={entry.difference < 0 ? '#22c55e' : '#ef4444'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="flex justify-center gap-6 text-xs text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-green-500" />
          <span>Betpawa more competitive</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-3 h-3 rounded-sm bg-red-500" />
          <span>Competitor more competitive</span>
        </div>
      </div>
    </div>
  )
}
