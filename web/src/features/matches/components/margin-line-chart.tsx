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
      const timeMap = new Map<string, Record<string, number | null>>()
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
          }
        })
      })

      // Sort by time and apply forward-fill so every row has values for all bookmakers
      const sortedEntries = Array.from(timeMap.entries())
        .sort((a, b) => new Date(a[0]).getTime() - new Date(b[0]).getTime())

      // Forward-fill: carry forward the last known value for each bookmaker
      const lastKnown: Record<string, number | null> = {}
      const filledData = sortedEntries.map(([time, values]) => {
        // Update last known values with any new data at this timestamp
        for (const slug of allBookmakers) {
          if (values[slug] !== undefined && values[slug] !== null) {
            lastKnown[slug] = values[slug]
          }
        }
        // Build row with forward-filled values
        const filledRow: Record<string, number | null> = {}
        for (const slug of allBookmakers) {
          filledRow[slug] = values[slug] ?? lastKnown[slug] ?? null
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
    }))
  }, [data, multiData, comparisonMode])

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
      <div className="flex items-center justify-center h-[200px] text-muted-foreground">
        No margin data available
      </div>
    )
  }

  return (
    <div>
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
              return format(new Date(payload[0].payload.time), 'MMM d, HH:mm')
            }
            return label
          }}
          formatter={(value, name) => [
            typeof value === 'number' ? `${value.toFixed(2)}%` : '-',
            comparisonMode && multiData
              ? multiData[name as string]?.bookmakerName || 'Margin'
              : 'Margin'
          ]}
          cursor={{ strokeDasharray: '3 3' }}
          isAnimationActive={false}
        />
        {comparisonMode && <Legend
          formatter={(value) =>
            multiData?.[value as string]?.bookmakerName || value
          }
        />}

        {comparisonMode ? (
          // Comparison mode: one line per bookmaker
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
          // Single bookmaker mode
          <Line
            type="monotone"
            dataKey="margin"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
          />
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
        {isLocked && lockedIndex !== null && lockedIndex < chartData.length && chartData[lockedIndex] && (
          <ReferenceLine
            x={chartData[lockedIndex]?.timeLabel}
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
            // Single bookmaker mode: show margin value
            (() => {
              const lockedPoint = chartData[lockedIndex] as Record<string, unknown>
              const marginValue = lockedPoint.margin
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
