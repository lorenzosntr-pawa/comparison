import { useMemo, useState, useEffect } from 'react'
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

// Color palette for bookmakers (same as odds-line-chart for consistency)
const BOOKMAKER_COLORS: Record<string, string> = {
  betpawa: '#3b82f6', // Blue
  sportybet: '#22c55e', // Green
  bet9ja: '#f97316', // Orange
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
  const chartDataByOutcome = useMemo(() => {
    if (!multiData) return {}

    const result: Record<string, ChartDataPoint[]> = {}

    outcomeNames.forEach((outcomeName) => {
      const timeMap = new Map<string, Record<string, number | null>>()

      Object.entries(multiData).forEach(([bookmakerSlug, { history }]) => {
        history.forEach((point) => {
          const time = point.captured_at
          if (!timeMap.has(time)) {
            timeMap.set(time, {})
          }
          const row = timeMap.get(time)!

          // Find this outcome's odds
          const outcome = point.outcomes?.find((o) => o.name === outcomeName)
          row[bookmakerSlug] = outcome?.odds ?? null
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

  // Handle chart click - toggle lock at clicked time
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const handleChartClick = (data: Record<string, any>) => {
    const time = data.activePayload?.[0]?.payload?.time as string | undefined
    if (time) {
      setLockedTime((prev) => (prev === time ? null : time))
    }
  }

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
                onClick={handleChartClick}
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

      {/* Unlock indicator */}
      {isLocked && lockedTime && (
        <div
          className="text-xs text-muted-foreground text-center cursor-pointer hover:text-foreground"
          onClick={() => setLockedTime(null)}
        >
          Locked at {format(new Date(lockedTime), 'MMM d, HH:mm')} — Click to unlock
        </div>
      )}
    </div>
  )
}
