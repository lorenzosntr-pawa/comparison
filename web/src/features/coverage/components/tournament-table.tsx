import { useState } from 'react'
import { ChevronRight, ChevronDown, Check, X } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { TournamentGroup, PalimpsestEvent } from '@/types/api'
import { EventRows } from './event-rows'

const PLATFORMS = ['betpawa', 'sportybet', 'bet9ja'] as const
const PLATFORM_LABELS: Record<string, string> = {
  betpawa: 'BetPawa',
  sportybet: 'SportyBet',
  bet9ja: 'Bet9ja',
}

interface TournamentTableProps {
  tournaments: TournamentGroup[]
  isLoading?: boolean
}

/**
 * Count events that have a specific platform in their platforms array.
 */
function countPlatformEvents(events: PalimpsestEvent[], platform: string): number {
  return events.filter((e) => e.platforms.includes(platform)).length
}

/**
 * Platform coverage cell showing check/count or X icon.
 */
function PlatformCell({ count }: { count: number }) {
  if (count > 0) {
    return (
      <div className="flex items-center gap-1 text-green-600">
        <Check className="h-4 w-4" />
        <span className="text-sm font-medium">{count}</span>
      </div>
    )
  }

  return (
    <div className="flex items-center text-orange-500">
      <X className="h-4 w-4" />
    </div>
  )
}

export function TournamentTable({ tournaments, isLoading }: TournamentTableProps) {
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set())

  const toggleExpanded = (tournamentId: number) => {
    setExpandedIds((prev) => {
      const next = new Set(prev)
      if (next.has(tournamentId)) {
        next.delete(tournamentId)
      } else {
        next.add(tournamentId)
      }
      return next
    })
  }

  if (isLoading) {
    return (
      <div className="border rounded-md">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[300px]">Tournament</TableHead>
              {PLATFORMS.map((p) => (
                <TableHead key={p} className="text-center">
                  {PLATFORM_LABELS[p]}
                </TableHead>
              ))}
              <TableHead className="text-center">Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {[...Array(5)].map((_, i) => (
              <TableRow key={i}>
                <TableCell>
                  <Skeleton className="h-5 w-48" />
                </TableCell>
                {PLATFORMS.map((p) => (
                  <TableCell key={p} className="text-center">
                    <Skeleton className="h-5 w-12 mx-auto" />
                  </TableCell>
                ))}
                <TableCell className="text-center">
                  <Skeleton className="h-5 w-8 mx-auto" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    )
  }

  if (tournaments.length === 0) {
    return (
      <div className="border rounded-md p-8 text-center text-muted-foreground">
        No events found. Try adjusting your filters.
      </div>
    )
  }

  return (
    <div className="border rounded-md">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[300px]">Tournament</TableHead>
            {PLATFORMS.map((p) => (
              <TableHead key={p} className="text-center">
                {PLATFORM_LABELS[p]}
              </TableHead>
            ))}
            <TableHead className="text-center">Total</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tournaments.map((tournament) => {
            const isExpanded = expandedIds.has(tournament.tournament_id)
            const totalEvents = tournament.events.length

            return (
              <>
                <TableRow
                  key={tournament.tournament_id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => toggleExpanded(tournament.tournament_id)}
                >
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {isExpanded ? (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      )}
                      <div>
                        <div className="font-medium">{tournament.tournament_name}</div>
                        {tournament.tournament_country && (
                          <div className="text-xs text-muted-foreground">
                            {tournament.tournament_country}
                          </div>
                        )}
                      </div>
                    </div>
                  </TableCell>
                  {PLATFORMS.map((platform) => {
                    const count = countPlatformEvents(tournament.events, platform)
                    return (
                      <TableCell key={platform} className="text-center">
                        <PlatformCell count={count} />
                      </TableCell>
                    )
                  })}
                  <TableCell className="text-center font-medium">
                    {totalEvents}
                  </TableCell>
                </TableRow>
                <EventRows
                  key={`${tournament.tournament_id}-events`}
                  events={tournament.events}
                  isExpanded={isExpanded}
                />
              </>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
