import { useNavigate } from 'react-router'
import { Check, X, ExternalLink } from 'lucide-react'
import { TableCell, TableRow } from '@/components/ui/table'
import { cn } from '@/lib/utils'
import type { PalimpsestEvent } from '@/types/api'

const PLATFORMS = ['betpawa', 'sportybet', 'bet9ja'] as const

interface EventRowsProps {
  events: PalimpsestEvent[]
  isExpanded: boolean
}

/**
 * Format kickoff time for display.
 */
function formatKickoff(kickoff: string): string {
  const date = new Date(kickoff)
  const now = new Date()
  const isToday = date.toDateString() === now.toDateString()
  const isTomorrow =
    date.toDateString() === new Date(now.getTime() + 86400000).toDateString()

  const timeStr = date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })

  if (isToday) {
    return `Today ${timeStr}`
  }
  if (isTomorrow) {
    return `Tomorrow ${timeStr}`
  }

  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  })
}

/**
 * Get row styling class based on event availability.
 */
function getRowClass(availability: PalimpsestEvent['availability']): string {
  switch (availability) {
    case 'betpawa-only':
      return 'border-l-2 border-l-blue-500/30'
    case 'competitor-only':
      return 'border-l-2 border-l-orange-500/30'
    default:
      return ''
  }
}

/**
 * Platform indicator showing check or X icon.
 */
function PlatformIndicator({ hasPlatform }: { hasPlatform: boolean }) {
  if (hasPlatform) {
    return <Check className="h-4 w-4 text-green-600 mx-auto" />
  }
  return <X className="h-4 w-4 text-orange-500 mx-auto" />
}

export function EventRows({ events, isExpanded }: EventRowsProps) {
  const navigate = useNavigate()

  if (!isExpanded) {
    return null
  }

  return (
    <>
      {events.map((event) => (
        <TableRow
          key={event.id}
          className={cn(
            'bg-muted/20 hover:bg-muted/40 cursor-pointer',
            getRowClass(event.availability)
          )}
          onClick={() => navigate(`/odds-comparison/${event.id}`)}
        >
          <TableCell className="pl-10">
            <div className="text-sm">
              <span className="font-medium">{event.home_team}</span>
              <span className="text-muted-foreground"> vs </span>
              <span className="font-medium">{event.away_team}</span>
            </div>
            <div className="text-xs text-muted-foreground">
              {formatKickoff(event.kickoff)}
            </div>
          </TableCell>
          {PLATFORMS.map((platform) => (
            <TableCell key={platform} className="text-center">
              <PlatformIndicator hasPlatform={event.platforms.includes(platform)} />
            </TableCell>
          ))}
          <TableCell className="text-right pr-4">
            <ExternalLink className="h-3.5 w-3.5 text-muted-foreground" />
          </TableCell>
          <TableCell />
        </TableRow>
      ))}
    </>
  )
}
