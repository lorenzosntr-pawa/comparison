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
import { ComparisonTable } from './comparison-table'

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

/**
 * Split chart data into available and unavailable segments for a given data key.
 * Points where availability is false get their value moved to `${key}_unavailable`
 * to allow rendering separate line series with different styling.
 */
function splitByAvailability<T extends Record<string, unknown>>(
  data: T[],
  dataKey: string,
  availabilityKey: string = 'available'
): T[] {
  return data.map((point) => {
    const available = point[availabilityKey] !== false
    const unavailableKey = `${dataKey}_unavailable`
    return {
      ...point,
      [dataKey]: available ? point[dataKey] : null,
      [unavailableKey]: available ? null : point[dataKey],
    } as T
  })
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
      const timeMap = new Map<string, Record<string, number | boolean | null>>()
      const allBookmakers = Object.keys(multiData)

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
            // Store availability as a separate field per bookmaker
            row[`${bookmakerSlug}_available`] = point.available ?? true
          }
        })
      })

      // Sort by time and apply forward-fill so every row has values for all bookmakers
      const sortedEntries = Array.from(timeMap.entries())
        .sort((a, b) => new Date(a[0]).getTime() - new Date(b[0]).getTime())

      // Forward-fill: carry forward the last known value for each bookmaker
      const lastKnown: Record<string, number | null> = {}
      const lastKnownAvailable: Record<string, boolean> = {}
      const filledData = sortedEntries.map(([time, values]) => {
        // Update last known values with any new data at this timestamp
        for (const slug of allBookmakers) {
          const oddsValue = values[slug]
          if (oddsValue !== undefined && oddsValue !== null && typeof oddsValue === 'number') {
            lastKnown[slug] = oddsValue
          }
          const availValue = values[`${slug}_available`]
          if (availValue !== undefined && typeof availValue === 'boolean') {
            lastKnownAvailable[slug] = availValue
          }
        }
        // Build row with forward-filled values
        const filledRow: Record<string, number | boolean | null> = {}
        for (const slug of allBookmakers) {
          const oddsVal = values[slug]
          filledRow[slug] = (typeof oddsVal === 'number' ? oddsVal : null) ?? lastKnown[slug] ?? null
          const availVal = values[`${slug}_available`]
          filledRow[`${slug}_available`] = (typeof availVal === 'boolean' ? availVal : undefined) ?? lastKnownAvailable[slug] ?? true
        }
        return {
          time,
          timeLabel: format(new Date(time), 'HH:mm'),
          ...filledRow,
        }
      })

      return filledData
    }

    // Single bookmaker mode (original behavior)
    if (!data?.length) return []

    return data.map((point) => {
      const row: Record<string, number | string | boolean | null> = {
        time: point.captured_at,
        timeLabel: format(new Date(point.captured_at), 'HH:mm'),
        margin: point.margin,
        available: point.available ?? true,
        confirmed: point.confirmed ?? false,
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

  // Process chart data to split available/unavailable values for visualization
  const processedChartData = useMemo(() => {
    if (!chartData.length) return []

    if (comparisonMode) {
      // For comparison mode, split each bookmaker's data
      let result = chartData as Record<string, unknown>[]
      for (const slug of bookmakerSlugs) {
        result = splitByAvailability(result, slug, `${slug}_available`)
      }
      return result
    } else {
      // For single mode, split each outcome's data
      let result = chartData as Record<string, unknown>[]
      for (const name of outcomeNames) {
        result = splitByAvailability(result, name, 'available')
      }
      return result
    }
  }, [chartData, comparisonMode, bookmakerSlugs, outcomeNames])

  // Check if there are any unavailable points
  const hasUnavailablePoints = useMemo(() => {
    if (comparisonMode) {
      return bookmakerSlugs.some((slug) =>
        processedChartData.some((point) => point[`${slug}_unavailable`] !== null)
      )
    }
    return processedChartData.some((point) =>
      outcomeNames.some((name) => point[`${name}_unavailable`] !== null)
    )
  }, [processedChartData, comparisonMode, bookmakerSlugs, outcomeNames])

  // Check if there are any confirmation points (stability points)
  const hasConfirmationPoints = useMemo(() => {
    return processedChartData.some((point) => point.confirmed === true)
  }, [processedChartData])

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

      {/* Legend notes for unavailable data and confirmation points */}
      {(hasUnavailablePoints || hasConfirmationPoints) && (
        <div className="text-xs text-muted-foreground mb-2 flex flex-col gap-1">
          {hasUnavailablePoints && (
            <div className="flex items-center gap-2">
              <span className="inline-block w-6 border-t-2 border-dashed border-muted-foreground"></span>
              <span>Dashed line = market unavailable</span>
            </div>
          )}
          {hasConfirmationPoints && (
            <div className="flex items-center gap-2">
              <span className="text-green-500">&#10003;</span>
              <span>Final point shows last verification time (odds stable)</span>
            </div>
          )}
        </div>
      )}

      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={processedChartData}
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
                const isConfirmed = payload[0].payload?.confirmed
                const timeStr = format(new Date(payload[0].payload.time), 'MMM d, HH:mm')
                return isConfirmed ? `${timeStr} (stable)` : timeStr
              }
              return label
            }}
            formatter={(value, name) => {
              // Handle unavailable series - show with marker
              const nameStr = String(name)
              const isUnavailable = nameStr.endsWith('_unavailable')
              const baseName = isUnavailable ? nameStr.replace('_unavailable', '') : nameStr
              const displayName = comparisonMode && multiData
                ? multiData[baseName]?.bookmakerName || baseName
                : baseName
              const suffix = isUnavailable ? ' (unavailable)' : ''
              return [
                typeof value === 'number' ? value.toFixed(2) : '-',
                displayName + suffix
              ]
            }}
            cursor={{ strokeDasharray: '3 3' }}
            isAnimationActive={false}
          />
          <Legend
            formatter={(value) => {
              const valueStr = String(value)
              // Hide unavailable series from legend (they share the same visual identity)
              if (valueStr.endsWith('_unavailable')) return null
              return comparisonMode && multiData
                ? multiData[valueStr]?.bookmakerName || value
                : value
            }}
          />

          {comparisonMode ? (
            // Comparison mode: two lines per bookmaker (available solid, unavailable dashed)
            bookmakerSlugs.flatMap((slug) => [
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
              />,
              <Line
                key={`${slug}_unavailable`}
                type="monotone"
                dataKey={`${slug}_unavailable`}
                stroke={BOOKMAKER_COLORS[slug] || '#888'}
                strokeWidth={2}
                strokeDasharray="5 5"
                dot={false}
                activeDot={{ r: 4 }}
                connectNulls
                isAnimationActive={false}
                legendType="none"
              />
            ])
          ) : (
            // Single bookmaker mode: two lines per outcome (available solid, unavailable dashed)
            <>
              {outcomeNames.flatMap((name, index) => [
                <Line
                  key={name}
                  type="monotone"
                  dataKey={name}
                  stroke={OUTCOME_COLORS[index % OUTCOME_COLORS.length]}
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 4 }}
                  isAnimationActive={false}
                />,
                <Line
                  key={`${name}_unavailable`}
                  type="monotone"
                  dataKey={`${name}_unavailable`}
                  stroke={OUTCOME_COLORS[index % OUTCOME_COLORS.length]}
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  activeDot={{ r: 4 }}
                  connectNulls
                  isAnimationActive={false}
                  legendType="none"
                />
              ])}
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
          {isLocked && lockedIndex !== null && lockedIndex < processedChartData.length && processedChartData[lockedIndex] && (
            <ReferenceLine
              x={processedChartData[lockedIndex].timeLabel as string}
              stroke="hsl(var(--primary))"
              strokeWidth={2}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      {/* Locked comparison panel */}
      {isLocked && lockedIndex !== null && lockedIndex < processedChartData.length && processedChartData[lockedIndex] && (
        <div className="mt-3 p-3 border rounded-lg bg-muted/50">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">
              Locked at {format(new Date(processedChartData[lockedIndex].time as string), 'MMM d, HH:mm')}
            </span>
            <button
              onClick={clearLock}
              className="text-xs text-muted-foreground hover:text-foreground underline"
            >
              Unlock
            </button>
          </div>
          {comparisonMode && multiData ? (
            <ComparisonTable
              lockedData={chartData[lockedIndex] as Record<string, unknown>}
              outcomeNames={selectedOutcome ? [selectedOutcome] : []}
              bookmakerSlugs={bookmakerSlugs}
              bookmakerNames={Object.fromEntries(
                Object.entries(multiData).map(([slug, data]) => [slug, data.bookmakerName])
              )}
              mode="comparison"
              showMargin={false}
            />
          ) : (
            <ComparisonTable
              lockedData={chartData[lockedIndex] as Record<string, unknown>}
              outcomeNames={outcomeNames}
              bookmakerSlugs={['betpawa']}
              bookmakerNames={{ betpawa: 'Betpawa' }}
              mode="single"
              showMargin={showMargin}
            />
          )}
        </div>
      )}
    </div>
  )
}
