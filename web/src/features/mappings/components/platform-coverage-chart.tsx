/**
 * Bar chart showing mapping counts by platform.
 *
 * @module platform-coverage-chart
 * @description Horizontal bar chart visualizing mapping coverage
 * across BetPawa, SportyBet, and Bet9ja platforms.
 */

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import type { PlatformCounts } from '../hooks'

interface PlatformCoverageChartProps {
  /** Platform mapping counts from useMappingStats */
  data: PlatformCounts | undefined
  /** Total mappings for percentage calculation */
  totalMappings: number
  /** Whether data is loading */
  isLoading?: boolean
  /** Chart height in pixels */
  height?: number
}

/** Platform colors matching the brand */
const PLATFORM_COLORS: Record<string, string> = {
  BetPawa: '#3b82f6', // Blue
  SportyBet: '#22c55e', // Green
  Bet9ja: '#f97316', // Orange
}

interface ChartDataPoint {
  platform: string
  count: number
  percentage: number
}

/**
 * Custom tooltip showing count and percentage.
 */
function CustomTooltip({
  active,
  payload,
}: {
  active?: boolean
  payload?: Array<{ payload: ChartDataPoint }>
}) {
  if (!active || !payload?.length) return null

  const data = payload[0].payload

  return (
    <div
      className="border rounded-md p-2 text-sm shadow-md"
      style={{
        backgroundColor: 'hsl(var(--popover))',
        borderColor: 'hsl(var(--border))',
      }}
    >
      <div className="font-medium">{data.platform}</div>
      <div className="text-muted-foreground">
        {data.count} mappings ({data.percentage.toFixed(1)}%)
      </div>
    </div>
  )
}

export function PlatformCoverageChart({
  data,
  totalMappings,
  isLoading = false,
  height = 200,
}: PlatformCoverageChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Platform Coverage</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="w-full" style={{ height }} />
        </CardContent>
      </Card>
    )
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Platform Coverage</CardTitle>
        </CardHeader>
        <CardContent>
          <div
            className="flex items-center justify-center text-muted-foreground"
            style={{ height }}
          >
            No data available
          </div>
        </CardContent>
      </Card>
    )
  }

  // Transform data for chart
  const chartData: ChartDataPoint[] = [
    {
      platform: 'BetPawa',
      count: data.betpawaCount,
      percentage: totalMappings > 0 ? (data.betpawaCount / totalMappings) * 100 : 0,
    },
    {
      platform: 'SportyBet',
      count: data.sportybetCount,
      percentage: totalMappings > 0 ? (data.sportybetCount / totalMappings) * 100 : 0,
    },
    {
      platform: 'Bet9ja',
      count: data.bet9JaCount,
      percentage: totalMappings > 0 ? (data.bet9JaCount / totalMappings) * 100 : 0,
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Platform Coverage</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={height}>
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 70, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              type="number"
              tick={{ fontSize: 11 }}
              className="text-muted-foreground"
            />
            <YAxis
              type="category"
              dataKey="platform"
              tick={{ fontSize: 12 }}
              className="text-muted-foreground"
              width={60}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'hsl(var(--muted))' }} />
            <Bar dataKey="count" radius={[0, 4, 4, 0]}>
              {chartData.map((entry, index) => (
                <Cell
                  key={index}
                  fill={PLATFORM_COLORS[entry.platform]}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
