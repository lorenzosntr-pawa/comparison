import { useMemo } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts'
import { format } from 'date-fns'
import type { OddsHistoryPoint } from '@/types/api'

// Color palette for outcome lines (up to 4 outcomes typical)
const OUTCOME_COLORS = ['#3b82f6', '#22c55e', '#f97316', '#8b5cf6']

interface OddsLineChartProps {
  data: OddsHistoryPoint[]
  height?: number
  showMargin?: boolean
}

export function OddsLineChart({
  data,
  height = 300,
  showMargin = false,
}: OddsLineChartProps) {
  // Transform data for recharts - flatten outcomes into columns
  const chartData = useMemo(() => {
    if (!data.length) return []

    return data.map((point) => {
      const row: Record<string, number | string | null> = {
        time: point.captured_at,
        timeLabel: format(new Date(point.captured_at), 'HH:mm'),
        margin: point.margin,
      }
      // Add each outcome as a separate column
      point.outcomes.forEach((outcome) => {
        row[outcome.name] = outcome.odds
      })
      return row
    })
  }, [data])

  // Get unique outcome names from first data point
  const outcomeNames = useMemo(() => {
    if (!data.length || !data[0].outcomes.length) return []
    return data[0].outcomes.map((o) => o.name)
  }, [data])

  if (!data.length) {
    return (
      <div className="flex items-center justify-center h-[300px] text-muted-foreground">
        No historical data available
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
          tickFormatter={(value) => value.toFixed(2)}
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
          formatter={(value) => [typeof value === 'number' ? value.toFixed(2) : '-', '']}
        />
        <Legend />
        {outcomeNames.map((name, index) => (
          <Line
            key={name}
            type="monotone"
            dataKey={name}
            stroke={OUTCOME_COLORS[index % OUTCOME_COLORS.length]}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
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
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  )
}
