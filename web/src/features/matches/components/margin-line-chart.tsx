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
} from 'recharts'
import { format } from 'date-fns'
import type { MarginHistoryPoint } from '@/types/api'

interface MarginLineChartProps {
  data: MarginHistoryPoint[]
  height?: number
  referenceValue?: number // Optional reference line (e.g., competitor margin)
  referenceLabel?: string
}

export function MarginLineChart({
  data,
  height = 200,
  referenceValue,
  referenceLabel,
}: MarginLineChartProps) {
  const chartData = useMemo(() => {
    return data.map((point) => ({
      time: point.captured_at,
      timeLabel: format(new Date(point.captured_at), 'HH:mm'),
      margin: point.margin,
    }))
  }, [data])

  if (!data.length) {
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
          tickFormatter={(value) => `${value.toFixed(1)}%`}
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
          formatter={(value) => [typeof value === 'number' ? `${value.toFixed(2)}%` : '-', 'Margin']}
        />
        <Line
          type="monotone"
          dataKey="margin"
          stroke="#3b82f6"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
        {referenceValue !== undefined && (
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
