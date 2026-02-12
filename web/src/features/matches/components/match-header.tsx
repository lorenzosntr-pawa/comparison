import { Link } from 'react-router'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import type { EventDetailResponse } from '@/types/api'

interface MatchHeaderProps {
  event: EventDetailResponse
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

export function MatchHeader({ event }: MatchHeaderProps) {
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
      <CardContent>
        <h1 className="text-2xl font-bold mb-2">
          {event.home_team} vs {event.away_team}
        </h1>
        <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
          <span>{event.tournament_name}</span>
          <span>|</span>
          <span>{formatKickoff(event.kickoff)}</span>
        </div>
      </CardContent>
    </Card>
  )
}
