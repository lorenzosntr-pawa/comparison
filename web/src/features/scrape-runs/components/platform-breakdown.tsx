import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'

interface PlatformTiming {
  duration_ms: number
  events_count: number
}

interface PlatformBreakdownProps {
  timings: Record<string, PlatformTiming> | null
}

export function PlatformBreakdown({ timings }: PlatformBreakdownProps) {
  if (!timings || Object.keys(timings).length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Platform Breakdown</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            No platform timing data available
          </p>
        </CardContent>
      </Card>
    )
  }

  // Calculate total duration for bar proportions
  const totalDuration = Object.values(timings).reduce(
    (sum, t) => sum + t.duration_ms,
    0
  )
  const totalEvents = Object.values(timings).reduce(
    (sum, t) => sum + t.events_count,
    0
  )

  const platformColors: Record<string, string> = {
    betpawa: 'bg-green-500',
    sportybet: 'bg-blue-500',
    bet9ja: 'bg-orange-500',
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Platform Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {Object.entries(timings).map(([platform, data]) => {
          const percentage =
            totalDuration > 0
              ? Math.round((data.duration_ms / totalDuration) * 100)
              : 0
          const durationSecs = (data.duration_ms / 1000).toFixed(1)

          return (
            <div key={platform} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-medium capitalize">{platform}</span>
                <span className="text-sm text-muted-foreground">
                  {data.events_count} events · {durationSecs}s
                </span>
              </div>
              <div className="h-2 w-full rounded-full bg-secondary">
                <div
                  className={cn(
                    'h-2 rounded-full transition-all',
                    platformColors[platform] || 'bg-primary'
                  )}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          )
        })}

        <div className="border-t pt-4">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">Total</span>
            <span className="text-muted-foreground">
              {totalEvents} events · {(totalDuration / 1000).toFixed(1)}s
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
