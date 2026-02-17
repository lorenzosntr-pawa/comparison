/**
 * Area chart showing storage size trend over time.
 *
 * @module size-trend-chart
 * @description Visualizes database size growth using recharts.
 */

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { format } from 'date-fns'
import type { StorageSample } from '../hooks'

/**
 * Format bytes to GB for display.
 */
function bytesToGB(bytes: number): number {
  return bytes / (1024 * 1024 * 1024)
}

/**
 * Format bytes to human-readable string.
 */
function formatBytes(bytes: number): string {
  const gb = bytesToGB(bytes)
  if (gb >= 1) {
    return `${gb.toFixed(2)} GB`
  }
  const mb = bytes / (1024 * 1024)
  return `${mb.toFixed(2)} MB`
}

interface SizeTrendChartProps {
  /** Storage history samples */
  data: StorageSample[]
  /** Chart height in pixels */
  height?: number
}

/**
 * Area chart showing database size trend over time.
 */
export function SizeTrendChart({ data, height = 250 }: SizeTrendChartProps) {
  if (!data.length) {
    return (
      <div
        className="flex items-center justify-center text-muted-foreground"
        style={{ height }}
      >
        No history data yet
      </div>
    )
  }

  // Transform data for chart (convert to GB and format date)
  const chartData = data
    .slice()
    .sort((a, b) => new Date(a.sampled_at).getTime() - new Date(b.sampled_at).getTime())
    .map((sample) => ({
      date: new Date(sample.sampled_at).getTime(),
      sizeGB: bytesToGB(sample.total_bytes),
      rawBytes: sample.total_bytes,
    }))

  // Calculate domain for Y-axis with some padding
  const minSize = Math.min(...chartData.map((d) => d.sizeGB))
  const maxSize = Math.max(...chartData.map((d) => d.sizeGB))
  const yPadding = (maxSize - minSize) * 0.1 || 0.5
  const yDomain: [number, number] = [
    Math.max(0, minSize - yPadding),
    maxSize + yPadding,
  ]

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart
        data={chartData}
        margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
      >
        <defs>
          <linearGradient id="sizeGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05} />
          </linearGradient>
        </defs>

        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />

        <XAxis
          dataKey="date"
          type="number"
          scale="time"
          domain={['dataMin', 'dataMax']}
          tick={{ fontSize: 11 }}
          tickFormatter={(value) => format(new Date(value), 'MMM d')}
          className="text-muted-foreground"
        />

        <YAxis
          domain={yDomain}
          tick={{ fontSize: 11 }}
          tickFormatter={(value) => `${value.toFixed(1)} GB`}
          width={55}
          className="text-muted-foreground"
        />

        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--popover))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '6px',
            fontSize: '12px',
          }}
          labelFormatter={(value) =>
            format(new Date(value as number), 'MMM d, yyyy HH:mm')
          }
          formatter={(_value, _name, props) => {
            const bytes = props.payload.rawBytes
            return [formatBytes(bytes), 'Database Size']
          }}
          cursor={{ strokeDasharray: '3 3' }}
          isAnimationActive={false}
        />

        <Area
          type="monotone"
          dataKey="sizeGB"
          stroke="#3b82f6"
          strokeWidth={2}
          fill="url(#sizeGradient)"
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
