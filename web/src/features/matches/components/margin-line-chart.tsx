import { useMemo } from 'react'
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
import { format } from 'date-fns'
import type { MarginHistoryPoint } from '@/types/api'
import type { MultiMarginHistoryData } from '../hooks/use-multi-margin-history'

// Color palette for bookmakers in comparison mode
const BOOKMAKER_COLORS: Record<string, string> = {
  betpawa: '#3b82f6',    // Blue
  sportybet: '#22c55e',  // Green
  bet9ja: '#f97316',     // Orange
}

interface MarginLineChartProps {
  data?: MarginHistoryPoint[]
  multiData?: MultiMarginHistoryData
  comparisonMode?: boolean
  height?: number
  referenceValue?: number // Optional reference line (e.g., competitor margin)
  referenceLabel?: string
}

export function MarginLineChart({
  data,
  multiData,
  comparisonMode = false,
  height = 200,
  referenceValue,
  referenceLabel,
}: MarginLineChartProps) {
  const chartData = useMemo(() => {
    if (comparisonMode && multiData) {
      // Comparison mode: merge all bookmaker data on a time axis
      const timeMap = new Map<string, Record<string, number | null>>()

      Object.entries(multiData).forEach(([bookmakerSlug, { history }]) => {
        history.forEach((point) => {
          const time = point.captured_at
          if (!timeMap.has(time)) {
            timeMap.set(time, {})
          }
          const row = timeMap.get(time)!
          row[bookmakerSlug] = point.margin
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
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
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
      </LineChart>
    </ResponsiveContainer>
  )
}
