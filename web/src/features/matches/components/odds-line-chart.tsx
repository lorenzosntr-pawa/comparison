import { useMemo, useState, useEffect, useCallback } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  ReferenceLine,
} from 'recharts'
import { useChartLock, type ChartClickData } from '../hooks/use-chart-lock'
import { format } from 'date-fns'
import type { OddsHistoryPoint } from '@/types/api'
import type { MultiOddsHistoryData } from '../hooks/use-multi-odds-history'

// Color palette for outcome lines (up to 4 outcomes typical)
const OUTCOME_COLORS = ['#3b82f6', '#22c55e', '#f97316', '#8b5cf6']

/**
 * Bucket a timestamp to the nearest minute for comparison mode data merging.
 * This allows bookmaker data captured at slightly different times to be grouped together.
 */
function bucketTimeToMinute(isoTimestamp: string): string {
  const d = new Date(isoTimestamp)
  d.setSeconds(0, 0) // Round down to the start of the minute
  return d.toISOString()
}

// Color palette for bookmakers in comparison mode
const BOOKMAKER_COLORS: Record<string, string> = {
  betpawa: '#3b82f6',    // Blue
  sportybet: '#22c55e',  // Green
  bet9ja: '#f97316',     // Orange
}

interface OddsLineChartProps {
  data?: OddsHistoryPoint[]
  multiData?: MultiOddsHistoryData
  comparisonMode?: boolean
  height?: number
  showMargin?: boolean
  onLockChange?: (lockedTime: string | null, lockedData: Record<string, unknown> | null) => void
}

export function OddsLineChart({
  data,
  multiData,
  comparisonMode = false,
  height = 300,
  showMargin = false,
  onLockChange,
}: OddsLineChartProps) {
  // Chart lock state
  const { lockedTime, lockedIndex, isLocked, handleChartClick, clearLock } = useChartLock()
  // In comparison mode, we show one outcome at a time with a selector
  const [selectedOutcome, setSelectedOutcome] = useState<string | null>(null)

  // Get all unique outcome names for the outcome selector (comparison mode)
  const outcomeNames = useMemo(() => {
    if (comparisonMode && multiData) {
      const allOutcomes = new Set<string>()
      Object.values(multiData).forEach(({ history }) => {
        history.forEach((point) => {
          point.outcomes?.forEach((o) => allOutcomes.add(o.name))
        })
      })
      return Array.from(allOutcomes)
    }
    if (data?.length && data[0]?.outcomes?.length) {
      return data[0].outcomes.map((o) => o.name)
    }
    return []
  }, [data, multiData, comparisonMode])

  // Set default selected outcome
  useMemo(() => {
    if (comparisonMode && outcomeNames.length && !selectedOutcome) {
      setSelectedOutcome(outcomeNames[0])
    }
  }, [comparisonMode, outcomeNames, selectedOutcome])

  // Transform data for recharts
  const chartData = useMemo(() => {
    if (comparisonMode && multiData) {
      // Comparison mode: merge all bookmaker data on a time axis
      // Create a map of bucketed time -> { bookmaker: odds }
      // Timestamps are bucketed to the nearest minute so data from different
      // bookmakers captured at similar times gets merged together
      const timeMap = new Map<string, Record<string, number | null>>()

      Object.entries(multiData).forEach(([bookmakerSlug, { history }]) => {
        history.forEach((point) => {
          // Bucket to nearest minute for merging
          const bucketedTime = bucketTimeToMinute(point.captured_at)
          if (!timeMap.has(bucketedTime)) {
            timeMap.set(bucketedTime, {})
          }
          const row = timeMap.get(bucketedTime)!

          // Find the selected outcome's odds
          const outcome = point.outcomes?.find((o) => o.name === selectedOutcome)
          // Only update if we don't have a value yet or if this is a newer data point
          // (later entries in history array are typically newer)
          if (row[bookmakerSlug] === undefined) {
            row[bookmakerSlug] = outcome?.odds ?? null
          }
        })
      })

      // Convert to array sorted by time
      return Array.from(timeMap.entries())
        .sort((a, b) => new Date(a[0]).getTime() - new Date(b[0]).getTime())
        .map(([time, values]) => ({
          time,
          timeLabel: format(new Date(time), 'HH:mm'),
          ...values,
        }))
    }

    // Single bookmaker mode (original behavior)
    if (!data?.length) return []

    return data.map((point) => {
      const row: Record<string, number | string | null> = {
        time: point.captured_at,
        timeLabel: format(new Date(point.captured_at), 'HH:mm'),
        margin: point.margin,
      }
      point.outcomes?.forEach((outcome) => {
        row[outcome.name] = outcome.odds
      })
      return row
    })
  }, [data, multiData, comparisonMode, selectedOutcome])

  // Get bookmaker slugs for comparison mode
  const bookmakerSlugs = useMemo(() => {
    if (comparisonMode && multiData) {
      return Object.keys(multiData)
    }
    return []
  }, [multiData, comparisonMode])

  // Wrapper for handleChartClick that passes chartData for index lookup
  const onChartClick = useCallback(
    (data: ChartClickData) => {
      handleChartClick(data, chartData as { time: string; [key: string]: unknown }[])
    },
    [handleChartClick, chartData]
  )

  // Call onLockChange when lock state changes
  // Note: Only depends on lock state, not chartData (to avoid retriggering on data updates)
  useEffect(() => {
    if (!onLockChange) return

    if (isLocked && lockedIndex !== null && lockedIndex < chartData.length && chartData[lockedIndex]) {
      onLockChange(lockedTime, chartData[lockedIndex] as Record<string, unknown>)
    } else {
      onLockChange(null, null)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- chartData excluded intentionally to prevent effect re-fire on data updates
  }, [lockedTime, lockedIndex, isLocked, onLockChange])

  // Check for empty data
  const isEmpty = comparisonMode
    ? !multiData || Object.keys(multiData).length === 0
    : !data?.length

  if (isEmpty) {
    return (
      <div className="flex items-center justify-center h-[300px] text-muted-foreground">
        No historical data available
      </div>
    )
  }

  return (
    <div>
      {/* Outcome selector for comparison mode */}
      {comparisonMode && outcomeNames.length > 0 && (
        <div className="flex items-center gap-2 mb-4">
          <span className="text-sm text-muted-foreground">Outcome:</span>
          <div className="flex gap-1">
            {outcomeNames.map((name) => (
              <button
                key={name}
                onClick={() => setSelectedOutcome(name)}
                className={`px-2 py-1 text-xs rounded border ${
                  selectedOutcome === name
                    ? 'bg-primary text-primary-foreground border-primary'
                    : 'bg-background border-border hover:bg-muted'
                }`}
              >
                {name}
              </button>
            ))}
          </div>
        </div>
      )}

      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
          onClick={onChartClick}
        >
          <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
          <XAxis
            dataKey="timeLabel"
            tick={{ fontSize: 12 }}
            className="text-muted-foreground"
          />
          <YAxis
            domain={['auto', 'auto']}
            tick={{ fontSize: 12 }}
            className="text-muted-foreground"
            tickFormatter={(value) => typeof value === 'number' ? value.toFixed(2) : ''}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: 'hsl(var(--popover))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '6px',
            }}
            labelFormatter={(label, payload) => {
              if (payload?.[0]?.payload?.time) {
                return format(new Date(payload[0].payload.time), 'MMM d, HH:mm')
              }
              return label
            }}
            formatter={(value, name) => [
              typeof value === 'number' ? value.toFixed(2) : '-',
              comparisonMode && multiData
                ? multiData[name as string]?.bookmakerName || name
                : name
            ]}
            cursor={{ strokeDasharray: '3 3' }}
            isAnimationActive={false}
          />
          <Legend
            formatter={(value) =>
              comparisonMode && multiData
                ? multiData[value as string]?.bookmakerName || value
                : value
            }
          />

          {comparisonMode ? (
            // Comparison mode: one line per bookmaker for the selected outcome
            bookmakerSlugs.map((slug) => (
              <Line
                key={slug}
                type="monotone"
                dataKey={slug}
                stroke={BOOKMAKER_COLORS[slug] || '#888'}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
                connectNulls
                isAnimationActive={false}
              />
            ))
          ) : (
            // Single bookmaker mode: one line per outcome
            <>
              {outcomeNames.map((name, index) => (
                <Line
                  key={name}
                  type="monotone"
                  dataKey={name}
                  stroke={OUTCOME_COLORS[index % OUTCOME_COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                  isAnimationActive={false}
                />
              ))}
              {showMargin && (
                <Line
                  type="monotone"
                  dataKey="margin"
                  stroke="#ef4444"
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Margin %"
                  isAnimationActive={false}
                />
              )}
            </>
          )}

          {/* Lock indicator line */}
          {isLocked && lockedIndex !== null && lockedIndex < chartData.length && chartData[lockedIndex] && (
            <ReferenceLine
              x={chartData[lockedIndex].timeLabel as string}
              stroke="hsl(var(--primary))"
              strokeWidth={2}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      {/* Locked comparison panel */}
      {isLocked && lockedIndex !== null && lockedIndex < chartData.length && chartData[lockedIndex] && (
        <div className="mt-3 p-3 border rounded-lg bg-muted/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">
              Locked at {format(new Date(chartData[lockedIndex].time as string), 'MMM d, HH:mm')}
            </span>
            <button
              onClick={clearLock}
              className="text-xs text-muted-foreground hover:text-foreground underline"
            >
              Unlock
            </button>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
            {comparisonMode ? (
              // Comparison mode: show each bookmaker's value
              bookmakerSlugs.map((slug) => {
                const lockedPoint = chartData[lockedIndex] as Record<string, unknown>
                const value = lockedPoint[slug]
                return (
                  <div key={slug} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: BOOKMAKER_COLORS[slug] || '#888' }}
                    />
                    <span className="text-sm">
                      {multiData?.[slug]?.bookmakerName || slug}:{' '}
                      <strong>{typeof value === 'number' ? value.toFixed(2) : '-'}</strong>
                    </span>
                  </div>
                )
              })
            ) : (
              // Single bookmaker mode: show each outcome's value
              outcomeNames.map((name, index) => {
                const lockedPoint = chartData[lockedIndex] as Record<string, unknown>
                const value = lockedPoint[name]
                return (
                  <div key={name} className="flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full flex-shrink-0"
                      style={{ backgroundColor: OUTCOME_COLORS[index % OUTCOME_COLORS.length] }}
                    />
                    <span className="text-sm">
                      {name}: <strong>{typeof value === 'number' ? value.toFixed(2) : '-'}</strong>
                    </span>
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
