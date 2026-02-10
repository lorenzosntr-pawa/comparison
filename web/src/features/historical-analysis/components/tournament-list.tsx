import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import type { TournamentWithCount } from '../hooks'

// Country flag emoji mapping (basic set for common countries)
const countryFlags: Record<string, string> = {
  England: 'England',
  Spain: 'Spain',
  Germany: 'Germany',
  Italy: 'Italy',
  France: 'France',
  Netherlands: 'Netherlands',
  Portugal: 'Portugal',
  Brazil: 'Brazil',
  Argentina: 'Argentina',
  Kenya: 'Kenya',
  Nigeria: 'Nigeria',
  Ghana: 'Ghana',
  'South Africa': 'South Africa',
  Uganda: 'Uganda',
  Tanzania: 'Tanzania',
}

interface TournamentListProps {
  tournaments: TournamentWithCount[]
  isLoading: boolean
}

function TournamentCard({ tournament }: { tournament: TournamentWithCount }) {
  const handleClick = () => {
    // Placeholder for Phase 84 drill-down
    console.log('Tournament clicked:', tournament.id, tournament.name)
  }

  return (
    <Card
      className="cursor-pointer transition-colors hover:bg-muted/50"
      onClick={handleClick}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0 flex-1">
            <h3 className="font-medium truncate">{tournament.name}</h3>
            <p className="text-sm text-muted-foreground">
              {tournament.country
                ? countryFlags[tournament.country] || tournament.country
                : 'International'}
            </p>
          </div>
          <Badge variant="secondary" className="shrink-0">
            {tournament.eventCount} event{tournament.eventCount !== 1 ? 's' : ''}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}

function SkeletonCard() {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1 space-y-2">
            <Skeleton className="h-5 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </div>
          <Skeleton className="h-5 w-16" />
        </div>
      </CardContent>
    </Card>
  )
}

export function TournamentList({ tournaments, isLoading }: TournamentListProps) {
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    )
  }

  if (tournaments.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-muted-foreground">
            No tournaments with data in selected period
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
      {tournaments.map((tournament) => (
        <TournamentCard key={tournament.id} tournament={tournament} />
      ))}
    </div>
  )
}
