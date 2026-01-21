import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
} from 'recharts'

// Types for the analytics data
export interface DailyMetric {
  date: string
  avg_duration_seconds: number
  total_events: number
  success_count: number
  failure_count: number
  partial_count: number
}

export interface PlatformMetric {
  platform: string
  success_rate: number
  avg_duration_seconds: number
  total_events: number
}

interface DurationTrendChartProps {
  data: DailyMetric[]
  isLoading?: boolean
}

interface SuccessRateChartProps {
  data: DailyMetric[]
  isLoading?: boolean
}

interface PlatformHealthChartProps {
  data: PlatformMetric[]
  isLoading?: boolean
}

// Platform color mapping
const platformColors: Record<string, string> = {
  betpawa: '#22c55e', // green
  sportybet: '#3b82f6', // blue
  bet9ja: '#f97316', // orange
}

// Format date for display (MMM DD)
function formatDate(dateStr: string): string {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

// Format duration for tooltip
function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}s`
  const minutes = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${minutes}m ${secs}s`
}

export function DurationTrendChart({ data, isLoading }: DurationTrendChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Duration Trend</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[200px] w-full" />
        </CardContent>
      </Card>
    )
  }

  const chartData = data.map((d) => ({
    date: formatDate(d.date),
    duration: d.avg_duration_seconds,
  }))

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Duration Trend</CardTitle>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="flex h-[200px] items-center justify-center text-sm text-muted-foreground">
            No data for selected period
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `${Math.round(value)}s`}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="rounded-lg border bg-background p-2 shadow-sm">
                        <div className="text-xs text-muted-foreground">
                          {payload[0].payload.date}
                        </div>
                        <div className="text-sm font-medium">
                          {formatDuration(payload[0].value as number)}
                        </div>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Line
                type="monotone"
                dataKey="duration"
                stroke="#8884d8"
                strokeWidth={2}
                dot={{ r: 3 }}
                activeDot={{ r: 5 }}
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}

export function SuccessRateChart({ data, isLoading }: SuccessRateChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Run Status</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[200px] w-full" />
        </CardContent>
      </Card>
    )
  }

  const chartData = data.map((d) => ({
    date: formatDate(d.date),
    success: d.success_count,
    partial: d.partial_count,
    failure: d.failure_count,
  }))

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Run Status</CardTitle>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="flex h-[200px] items-center justify-center text-sm text-muted-foreground">
            No data for selected period
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <YAxis
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                allowDecimals={false}
              />
              <Tooltip
                content={({ active, payload, label }) => {
                  if (active && payload && payload.length) {
                    return (
                      <div className="rounded-lg border bg-background p-2 shadow-sm">
                        <div className="text-xs text-muted-foreground">{label}</div>
                        {payload.map((entry) => (
                          <div
                            key={entry.name}
                            className="flex items-center gap-2 text-sm"
                          >
                            <div
                              className="h-2 w-2 rounded-full"
                              style={{ backgroundColor: entry.color }}
                            />
                            <span className="capitalize">{entry.name}</span>
                            <span className="font-medium">{entry.value}</span>
                          </div>
                        ))}
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Legend
                iconType="circle"
                wrapperStyle={{ fontSize: '12px' }}
              />
              <Bar dataKey="success" stackId="a" fill="#22c55e" name="Success" />
              <Bar dataKey="partial" stackId="a" fill="#eab308" name="Partial" />
              <Bar dataKey="failure" stackId="a" fill="#ef4444" name="Failed" />
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}

export function PlatformHealthChart({ data, isLoading }: PlatformHealthChartProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Platform Health</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="h-[150px] w-full" />
        </CardContent>
      </Card>
    )
  }

  const chartData = data.map((d) => ({
    platform: d.platform.charAt(0).toUpperCase() + d.platform.slice(1),
    success_rate: d.success_rate,
    total_events: d.total_events,
    avg_duration: d.avg_duration_seconds,
    fill: platformColors[d.platform.toLowerCase()] || '#8884d8',
  }))

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Platform Health</CardTitle>
      </CardHeader>
      <CardContent>
        {chartData.length === 0 ? (
          <div className="flex h-[150px] items-center justify-center text-sm text-muted-foreground">
            No data for selected period
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={150}>
            <BarChart data={chartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
              <XAxis
                type="number"
                domain={[0, 100]}
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(value) => `${value}%`}
              />
              <YAxis
                type="category"
                dataKey="platform"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                width={80}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload
                    return (
                      <div className="rounded-lg border bg-background p-2 shadow-sm">
                        <div className="text-sm font-medium">{data.platform}</div>
                        <div className="text-xs text-muted-foreground">
                          Success Rate: {data.success_rate.toFixed(1)}%
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Avg Duration: {formatDuration(data.avg_duration)}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Total Events: {data.total_events.toLocaleString()}
                        </div>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Bar
                dataKey="success_rate"
                radius={[0, 4, 4, 0]}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  )
}
