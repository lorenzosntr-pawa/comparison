import { useMemo, useState, useEffect } from 'react'
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
import { useChartLock } from '../hooks/use-chart-lock'
import { format } from 'date-fns'
import type { OddsHistoryPoint } from '@/types/api'
import type { MultiOddsHistoryData } from '../hooks/use-multi-odds-history'

// Color palette for outcome lines (up to 4 outcomes typical)
const OUTCOME_COLORS = ['#3b82f6', '#22c55e', '#f97316', '#8b5cf6']

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
      // Create a map of time -> { bookmaker: odds }
      const timeMap = new Map<string, Record<string, number | null>>()

      Object.entries(multiData).forEach(([bookmakerSlug, { history }]) => {
        history.forEach((point) => {
          const time = point.captured_at
          if (!timeMap.has(time)) {
            timeMap.set(time, {})
          }
          const row = timeMap.get(time)!

          // Find the selected outcome's odds
          const outcome = point.outcomes?.find((o) => o.name === selectedOutcome)
          row[bookmakerSlug] = outcome?.odds ?? null
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

  // Call onLockChange when lock state changes
  useEffect(() => {
    if (onLockChange) {
      const lockedData = isLocked && lockedIndex !== null ? chartData[lockedIndex] : null
      onLockChange(lockedTime, lockedData as Record<string, unknown> | null)
    }
  }, [lockedTime, lockedIndex, isLocked, chartData, onLockChange])

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
          onClick={handleChartClick}
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
          {isLocked && lockedIndex !== null && chartData[lockedIndex] && (
            <ReferenceLine
              x={chartData[lockedIndex]?.timeLabel}
              stroke="hsl(var(--primary))"
              strokeWidth={2}
            />
          )}
        </LineChart>
      </ResponsiveContainer>

      {/* Unlock indicator */}
      {isLocked && (
        <div
          className="text-xs text-muted-foreground text-center mt-1 cursor-pointer hover:text-foreground"
          onClick={clearLock}
        >
          Click chart or here to unlock
        </div>
      )}
    </div>
  )
}
