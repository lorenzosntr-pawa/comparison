import { useMemo, useState, useEffect, useRef, useCallback } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts'
import { format } from 'date-fns'
import type { MultiOddsHistoryData } from '../hooks/use-multi-odds-history'
import { ComparisonTable } from './comparison-table'

// Color palette for bookmakers (same as odds-line-chart for consistency)
const BOOKMAKER_COLORS: Record<string, string> = {
  betpawa: '#3b82f6', // Blue
  sportybet: '#22c55e', // Green
  bet9ja: '#f97316', // Orange
}

/**
 * Bucket a timestamp to the nearest minute for comparison mode data merging.
 * This allows bookmaker data captured at slightly different times to be grouped together.
 */
function bucketTimeToMinute(isoTimestamp: string): string {
  const d = new Date(isoTimestamp)
  d.setSeconds(0, 0) // Round down to the start of the minute
  return d.toISOString()
}

interface MarketHistoryPanelProps {
  multiData?: MultiOddsHistoryData
  height?: number
  onLockChange?: (lockedTime: string | null) => void
}

interface ChartDataPoint {
  time: string
  timeLabel: string
  [bookmakerSlug: string]: string | number | null
}

export function MarketHistoryPanel({
  multiData,
  height = 180,
  onLockChange,
}: MarketHistoryPanelProps) {
  // Shared lock state for synchronized crosshairs across all mini-charts
  const [lockedTime, setLockedTime] = useState<string | null>(null)
  const isLocked = lockedTime !== null
  // Extract all unique outcome names from the data
  const outcomeNames = useMemo(() => {
    if (!multiData) return []
    const allOutcomes = new Set<string>()
    Object.values(multiData).forEach(({ history }) => {
      history.forEach((point) => {
        point.outcomes?.forEach((o) => allOutcomes.add(o.name))
      })
    })
    return Array.from(allOutcomes)
  }, [multiData])

  // Get bookmaker slugs
  const bookmakerSlugs = useMemo(() => {
    if (!multiData) return []
    return Object.keys(multiData)
  }, [multiData])

  // Transform data for each outcome's chart
  // Timestamps are bucketed to the nearest minute so data from different
  // bookmakers captured at similar times gets merged together
  const chartDataByOutcome = useMemo(() => {
    if (!multiData) return {}

    const result: Record<string, ChartDataPoint[]> = {}

    outcomeNames.forEach((outcomeName) => {
      const timeMap = new Map<string, Record<string, number | null>>()

      Object.entries(multiData).forEach(([bookmakerSlug, { history }]) => {
        history.forEach((point) => {
          // Bucket to nearest minute for merging
          const bucketedTime = bucketTimeToMinute(point.captured_at)
          if (!timeMap.has(bucketedTime)) {
            timeMap.set(bucketedTime, {})
          }
          const row = timeMap.get(bucketedTime)!

          // Find this outcome's odds
          const outcome = point.outcomes?.find((o) => o.name === outcomeName)
          // Only update if we don't have a value yet
          if (row[bookmakerSlug] === undefined) {
            row[bookmakerSlug] = outcome?.odds ?? null
          }
        })
      })

      // Convert to array sorted by time
      result[outcomeName] = Array.from(timeMap.entries())
        .sort((a, b) => new Date(a[0]).getTime() - new Date(b[0]).getTime())
        .map(([time, values]) => ({
          time,
          timeLabel: format(new Date(time), 'HH:mm'),
          ...values,
        }))
    })

    return result
  }, [multiData, outcomeNames])

  // Get locked index for a specific outcome's chart data
  const getLockedIndex = (data: ChartDataPoint[]) => {
    if (!lockedTime) return null
    return data.findIndex((d) => d.time === lockedTime)
  }

  // Track last click time to debounce rapid clicks
  const lastClickRef = useRef<number>(0)

  // Create click handler for a specific outcome's chart
  // Needs chartData to find time when activePayload is not available
  const createChartClickHandler = useCallback(
    (outcomeChartData: ChartDataPoint[]) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return (data: Record<string, any>) => {
        // Debounce: ignore clicks within 100ms of last click
        const now = Date.now()
        if (now - lastClickRef.current < 100) {
          return
        }
        lastClickRef.current = now

        // Try to get time from activePayload first
        let time = data.activePayload?.[0]?.payload?.time as string | undefined

        // Fallback: if activeTooltipIndex is available, get time from chartData
        if (!time && typeof data.activeTooltipIndex === 'number') {
          const idx = data.activeTooltipIndex
          if (idx >= 0 && idx < outcomeChartData.length) {
            time = outcomeChartData[idx].time
          }
        }

        if (time) {
          setLockedTime((prev) => (prev === time ? null : time))
        }
      }
    },
    []
  )

  // Call onLockChange when lock state changes
  useEffect(() => {
    if (onLockChange) {
      onLockChange(lockedTime)
    }
  }, [lockedTime, onLockChange])

  // Check for empty data
  if (!multiData || Object.keys(multiData).length === 0 || outcomeNames.length === 0) {
    return (
      <div className="flex items-center justify-center h-[300px] text-muted-foreground">
        No historical data available
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Small-multiples grid - one chart per outcome */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {outcomeNames.map((outcomeName) => (
          <div key={outcomeName} className="border rounded-lg p-3">
            <h4 className="text-sm font-medium text-center mb-2">{outcomeName}</h4>
            <ResponsiveContainer width="100%" height={height}>
              <LineChart
                data={chartDataByOutcome[outcomeName] || []}
                margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
                onClick={createChartClickHandler(chartDataByOutcome[outcomeName] || [])}
              >
                <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                <XAxis
                  dataKey="timeLabel"
                  tick={{ fontSize: 10 }}
                  className="text-muted-foreground"
                  interval="preserveStartEnd"
                />
                <YAxis
                  domain={['auto', 'auto']}
                  tick={{ fontSize: 10 }}
                  className="text-muted-foreground"
                  tickFormatter={(value) =>
                    typeof value === 'number' ? value.toFixed(2) : ''
                  }
                  width={40}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '6px',
                    fontSize: '12px',
                  }}
                  labelFormatter={(label, payload) => {
                    if (payload?.[0]?.payload?.time) {
                      return format(new Date(payload[0].payload.time), 'MMM d, HH:mm')
                    }
                    return label
                  }}
                  formatter={(value, name) => [
                    typeof value === 'number' ? value.toFixed(2) : '-',
                    multiData[name as string]?.bookmakerName || name,
                  ]}
                  cursor={{ strokeDasharray: '3 3' }}
                  isAnimationActive={false}
                />
                {bookmakerSlugs.map((slug) => (
                  <Line
                    key={slug}
                    type="monotone"
                    dataKey={slug}
                    stroke={BOOKMAKER_COLORS[slug] || '#888'}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 3 }}
                    connectNulls
                    isAnimationActive={false}
                  />
                ))}

                {/* Synchronized lock indicator line */}
                {isLocked && (() => {
                  const idx = getLockedIndex(chartDataByOutcome[outcomeName] || [])
                  if (idx === null || idx < 0) return null
                  const chartData = chartDataByOutcome[outcomeName]
                  if (!chartData || !chartData[idx]) return null
                  return (
                    <ReferenceLine
                      x={chartData[idx].timeLabel}
                      stroke="hsl(var(--primary))"
                      strokeWidth={2}
                    />
                  )
                })()}
              </LineChart>
            </ResponsiveContainer>
          </div>
        ))}
      </div>

      {/* Shared legend at bottom */}
      <div className="flex justify-center gap-4 pt-2 border-t">
        {bookmakerSlugs.map((slug) => (
          <div key={slug} className="flex items-center gap-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: BOOKMAKER_COLORS[slug] || '#888' }}
            />
            <span className="text-xs text-muted-foreground">
              {multiData[slug]?.bookmakerName || slug}
            </span>
          </div>
        ))}
      </div>

      {/* Locked comparison panel */}
      {isLocked && lockedTime && multiData && (
        <div className="mt-3 p-3 border rounded-lg bg-muted/50">
          <div className="flex items-center justify-between mb-3">
            <span className="text-sm font-medium">
              Locked at {format(new Date(lockedTime), 'MMM d, HH:mm')}
            </span>
            <button
              onClick={() => setLockedTime(null)}
              className="text-xs text-muted-foreground hover:text-foreground underline"
            >
              Unlock
            </button>
          </div>

          {/* Comparison table with best/worst highlighting */}
          <ComparisonTable
            lockedData={{}}
            outcomeNames={outcomeNames}
            bookmakerSlugs={bookmakerSlugs}
            bookmakerNames={Object.fromEntries(
              Object.entries(multiData).map(([slug, data]) => [slug, data.bookmakerName])
            )}
            mode="comparison"
            showMargin={false}
            oddsDataByOutcome={(() => {
              // Build odds data by outcome from chartDataByOutcome at locked time
              const result: Record<string, Record<string, number | null>> = {}
              outcomeNames.forEach((outcomeName) => {
                const chartData = chartDataByOutcome[outcomeName] || []
                const idx = getLockedIndex(chartData)
                const lockedPoint = idx !== null && idx >= 0 ? chartData[idx] : null

                result[outcomeName] = {}
                bookmakerSlugs.forEach((slug) => {
                  const value = lockedPoint?.[slug]
                  result[outcomeName][slug] = typeof value === 'number' ? value : null
                })
              })
              return result
            })()}
          />
        </div>
      )}
    </div>
  )
}
