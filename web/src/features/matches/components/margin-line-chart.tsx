import { useMemo, useEffect, useCallback } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend,
} from 'recharts'
import { useChartLock, type ChartClickData } from '../hooks/use-chart-lock'
import { format } from 'date-fns'
import type { MarginHistoryPoint } from '@/types/api'
import type { MultiMarginHistoryData } from '../hooks/use-multi-margin-history'
import { ComparisonTable } from './comparison-table'

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

/**
 * Bucket a timestamp to the nearest minute for comparison mode data merging.
 * This allows bookmaker data captured at slightly different times to be grouped together.
 */
function bucketTimeToMinute(isoTimestamp: string): string {
  const d = new Date(isoTimestamp)
  d.setSeconds(0, 0) // Round down to the start of the minute
  return d.toISOString()
}

interface MarginLineChartProps {
  data?: MarginHistoryPoint[]
  multiData?: MultiMarginHistoryData
  comparisonMode?: boolean
  height?: number
  referenceValue?: number // Optional reference line (e.g., competitor margin)
  referenceLabel?: string
  onLockChange?: (lockedTime: string | null, lockedData: Record<string, unknown> | null) => void
}

export function MarginLineChart({
  data,
  multiData,
  comparisonMode = false,
  height = 200,
  referenceValue,
  referenceLabel,
  onLockChange,
}: MarginLineChartProps) {
  // Chart lock state
  const { lockedTime, lockedIndex, isLocked, handleChartClick, clearLock } = useChartLock()
  const chartData = useMemo(() => {
    if (comparisonMode && multiData) {
      // Comparison mode: merge all bookmaker data on a time axis
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
          // Only update if we don't have a value yet
          if (row[bookmakerSlug] === undefined) {
            row[bookmakerSlug] = point.margin
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
          const marginValue = values[slug]
          if (marginValue !== undefined && marginValue !== null && typeof marginValue === 'number') {
            lastKnown[slug] = marginValue
          }
          const availValue = values[`${slug}_available`]
          if (availValue !== undefined && typeof availValue === 'boolean') {
            lastKnownAvailable[slug] = availValue
          }
        }
        // Build row with forward-filled values
        const filledRow: Record<string, number | boolean | null> = {}
        for (const slug of allBookmakers) {
          const marginVal = values[slug]
          filledRow[slug] = (typeof marginVal === 'number' ? marginVal : null) ?? lastKnown[slug] ?? null
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

    return data.map((point) => ({
      time: point.captured_at,
      timeLabel: format(new Date(point.captured_at), 'HH:mm'),
      margin: point.margin,
      available: point.available ?? true,
      confirmed: point.confirmed ?? false,
    }))
  }, [data, multiData, comparisonMode])

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
      // For single mode, split margin data by availability
      return splitByAvailability(chartData as Record<string, unknown>[], 'margin', 'available')
    }
  }, [chartData, comparisonMode, bookmakerSlugs])

  // Check if there are any unavailable points
  const hasUnavailablePoints = useMemo(() => {
    if (comparisonMode) {
      return bookmakerSlugs.some((slug) =>
        processedChartData.some((point) => point[`${slug}_unavailable`] !== null)
      )
    }
    return processedChartData.some((point) => point.margin_unavailable !== null)
  }, [processedChartData, comparisonMode, bookmakerSlugs])

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
      <div className="flex items-center justify-center h-[200px] text-muted-foreground">
        No margin data available
      </div>
    )
  }

  return (
    <div>
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
          tickFormatter={(value) => typeof value === 'number' ? `${value.toFixed(1)}%` : ''}
          width={50}
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
              ? multiData[baseName]?.bookmakerName || 'Margin'
              : 'Margin'
            const suffix = isUnavailable ? ' (unavailable)' : ''
            return [
              typeof value === 'number' ? `${value.toFixed(2)}%` : '-',
              displayName + suffix
            ]
          }}
          cursor={{ strokeDasharray: '3 3' }}
          isAnimationActive={false}
        />
        {comparisonMode && <Legend
          formatter={(value) => {
            const valueStr = String(value)
            // Hide unavailable series from legend (they share the same visual identity)
            if (valueStr.endsWith('_unavailable')) return null
            return multiData?.[valueStr]?.bookmakerName || value
          }}
        />}

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
          // Single bookmaker mode: two lines (available solid, unavailable dashed)
          <>
            <Line
              type="monotone"
              dataKey="margin"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="margin_unavailable"
              stroke="#3b82f6"
              strokeWidth={2}
              strokeDasharray="5 5"
              dot={false}
              activeDot={{ r: 4 }}
              connectNulls
              isAnimationActive={false}
              legendType="none"
            />
          </>
        )}

        {referenceValue !== undefined && !comparisonMode && (
          <ReferenceLine
            y={referenceValue}
            stroke="#ef4444"
            strokeDasharray="5 5"
            label={{
              value: referenceLabel || `${referenceValue.toFixed(1)}%`,
              position: 'right',
              fill: '#ef4444',
              fontSize: 11,
            }}
          />
        )}

        {/* Lock indicator line */}
        {isLocked && lockedIndex !== null && lockedIndex < processedChartData.length && processedChartData[lockedIndex] && (
          <ReferenceLine
            x={processedChartData[lockedIndex]?.timeLabel as string}
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
              lockedData={{}}
              outcomeNames={[]}
              bookmakerSlugs={bookmakerSlugs}
              bookmakerNames={Object.fromEntries(
                Object.entries(multiData).map(([slug, data]) => [slug, data.bookmakerName])
              )}
              mode="comparison"
              showMargin={true}
              marginData={Object.fromEntries(
                bookmakerSlugs.map((slug) => {
                  const lockedPoint = chartData[lockedIndex] as Record<string, unknown>
                  const value = lockedPoint[slug]
                  return [slug, typeof value === 'number' ? value : null]
                })
              )}
            />
          ) : (
            // Single bookmaker mode: show margin value with availability indicator
            (() => {
              const lockedPoint = chartData[lockedIndex] as Record<string, unknown>
              const marginValue = lockedPoint.margin
              const isAvailable = lockedPoint.available !== false
              return (
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full flex-shrink-0"
                    style={{ backgroundColor: '#3b82f6' }}
                  />
                  <span className="text-sm">
                    Margin:{' '}
                    <strong>
                      {typeof marginValue === 'number'
                        ? `${marginValue.toFixed(2)}%`
                        : '-'}
                    </strong>
                    {!isAvailable && (
                      <span className="text-muted-foreground ml-1">(unavailable)</span>
                    )}
                  </span>
                </div>
              )
            })()
          )}
        </div>
      )}
    </div>
  )
}
