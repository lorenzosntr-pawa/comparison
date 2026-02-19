import { Link, useNavigate } from 'react-router'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { EventDetailResponse } from '@/types/api'

interface MatchHeaderProps {
  event: EventDetailResponse
  /** Number of risk alerts for this event */
  alertCount?: number
  /** Maximum severity of alerts */
  maxSeverity?: 'warning' | 'elevated' | 'critical' | null
}

function formatKickoff(kickoff: string): string {
  const date = new Date(kickoff)
  return date.toLocaleString('en-GB', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/** Severity-based alert styles */
const ALERT_STYLES = {
  warning: 'border-yellow-500/50 bg-yellow-50 dark:bg-yellow-950/20',
  elevated: 'border-orange-500/50 bg-orange-50 dark:bg-orange-950/20',
  critical: 'border-red-500/50 bg-red-50 dark:bg-red-950/20',
} as const

export function MatchHeader({ event, alertCount, maxSeverity }: MatchHeaderProps) {
  const navigate = useNavigate()
  const showAlertBanner = alertCount !== undefined && alertCount > 0 && maxSeverity

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <Button variant="outline" size="sm" asChild>
            <Link to="/">Back to Odds Comparison</Link>
          </Button>
          <span className="text-sm text-muted-foreground">
            {event.sport_name}
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <h1 className="text-2xl font-bold mb-2">
            {event.home_team} vs {event.away_team}
          </h1>
          <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
            <span>{event.tournament_name}</span>
            <span>|</span>
            <span>{formatKickoff(event.kickoff)}</span>
          </div>
        </div>

        {/* Alert banner */}
        {showAlertBanner && (
          <Alert
            className={cn(
              'flex items-center justify-between',
              ALERT_STYLES[maxSeverity]
            )}
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription className="font-medium">
                {alertCount} risk alert{alertCount !== 1 ? 's' : ''} detected
              </AlertDescription>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => navigate(`/risk-monitoring?event_id=${event.id}`)}
            >
              View Alerts
            </Button>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}
