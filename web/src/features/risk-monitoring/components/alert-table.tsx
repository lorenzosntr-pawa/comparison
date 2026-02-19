/**
 * Alert table component with event grouping and expandable alert rows.
 *
 * @module alert-table
 */

import { useState } from 'react'
import { format, formatDistanceToNow } from 'date-fns'
import { ChevronDown, ChevronRight, Check, LineChart } from 'lucide-react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { RiskAlert } from '../hooks'
import { useAcknowledgeAlert } from '../hooks'
import { HistoryDialog } from '@/features/matches/components/history-dialog'

interface AlertTableProps {
  alerts: RiskAlert[]
}

/** Group alerts by event */
interface EventGroup {
  eventId: number
  eventName: string
  homeTeam: string
  awayTeam: string
  kickoff: string
  alerts: RiskAlert[]
  maxSeverity: 'warning' | 'elevated' | 'critical'
}

function groupAlertsByEvent(alerts: RiskAlert[]): EventGroup[] {
  const groups = new Map<number, EventGroup>()

  for (const alert of alerts) {
    const existing = groups.get(alert.eventId)
    if (existing) {
      existing.alerts.push(alert)
      // Update max severity
      if (
        alert.severity === 'critical' ||
        (alert.severity === 'elevated' && existing.maxSeverity === 'warning')
      ) {
        existing.maxSeverity = alert.severity
      }
    } else {
      groups.set(alert.eventId, {
        eventId: alert.eventId,
        eventName: alert.eventName || `Event #${alert.eventId}`,
        homeTeam: alert.homeTeam || 'Unknown',
        awayTeam: alert.awayTeam || 'Unknown',
        kickoff: alert.eventKickoff,
        alerts: [alert],
        maxSeverity: alert.severity,
      })
    }
  }

  return Array.from(groups.values())
}

/** Map severity to badge color */
function getSeverityBadge(severity: RiskAlert['severity']) {
  switch (severity) {
    case 'critical':
      return <Badge variant="destructive">Critical</Badge>
    case 'elevated':
      return <Badge className="bg-orange-500 hover:bg-orange-600">Elevated</Badge>
    case 'warning':
      return <Badge className="bg-yellow-500 hover:bg-yellow-600 text-black">Warning</Badge>
    default:
      return <Badge variant="outline">{severity}</Badge>
  }
}

/** Map alert type to display badge */
function getTypeBadge(alertType: RiskAlert['alertType']) {
  switch (alertType) {
    case 'price_change':
      return <Badge variant="outline">Price Change</Badge>
    case 'direction_disagreement':
      return <Badge variant="outline" className="border-purple-500 text-purple-700">Direction</Badge>
    case 'availability':
      return <Badge variant="outline" className="border-blue-500 text-blue-700">Availability</Badge>
    default:
      return <Badge variant="outline">{alertType}</Badge>
  }
}

/** Format change percent with sign */
function formatChange(change: number): string {
  const sign = change >= 0 ? '+' : ''
  return `${sign}${change.toFixed(2)}%`
}

/** Parse competitor direction string (e.g., "sportybet:up") into readable format */
function parseCompetitorDirection(direction: string | null): { bookmaker: string; movement: string } | null {
  if (!direction) return null
  const [slug, movement] = direction.split(':')
  const bookmakerNames: Record<string, string> = {
    betpawa: 'BetPawa',
    sportybet: 'SportyBet',
    bet9ja: 'Bet9ja',
  }
  return {
    bookmaker: bookmakerNames[slug] || slug,
    movement: movement || 'unknown',
  }
}

/** Get direction arrow */
function getDirectionArrow(movement: string): string {
  switch (movement) {
    case 'up':
      return '↑'
    case 'down':
      return '↓'
    default:
      return ''
  }
}

/** Format odds value */
function formatOdds(value: number | null): string {
  if (value === null) return '-'
  return value.toFixed(2)
}

/** Get bookmaker display name */
function getBookmakerName(slug: string): string {
  const names: Record<string, string> = {
    betpawa: 'BetPawa',
    sportybet: 'SportyBet',
    bet9ja: 'Bet9ja',
  }
  return names[slug] || slug
}

export function AlertTable({ alerts }: AlertTableProps) {
  const [expandedEvents, setExpandedEvents] = useState<Set<number>>(new Set())
  const [historyDialog, setHistoryDialog] = useState<{
    open: boolean
    eventId: number
    marketId: string
    line: number | null
    bookmakerSlug: string
    marketName: string
    bookmakerName: string
  } | null>(null)
  const acknowledgeAlert = useAcknowledgeAlert()

  const eventGroups = groupAlertsByEvent(alerts)

  const toggleEvent = (eventId: number) => {
    setExpandedEvents((prev) => {
      const next = new Set(prev)
      if (next.has(eventId)) {
        next.delete(eventId)
      } else {
        next.add(eventId)
      }
      return next
    })
  }

  const handleAcknowledge = (alertId: number, currentlyAcknowledged: boolean) => {
    acknowledgeAlert.mutate({
      alertId,
      acknowledged: !currentlyAcknowledged,
    })
  }

  const openHistory = (alert: RiskAlert) => {
    setHistoryDialog({
      open: true,
      eventId: alert.eventId,
      marketId: alert.marketId,
      line: alert.line,
      bookmakerSlug: alert.bookmakerSlug,
      marketName: alert.marketName,
      bookmakerName: getBookmakerName(alert.bookmakerSlug),
    })
  }

  if (eventGroups.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No alerts match the current filters
      </div>
    )
  }

  return (
    <>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-8"></TableHead>
            <TableHead>Event</TableHead>
            <TableHead>Kickoff</TableHead>
            <TableHead className="text-center">Alerts</TableHead>
            <TableHead>Max Severity</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {eventGroups.map((group) => {
            const isExpanded = expandedEvents.has(group.eventId)

            return (
              <>
                {/* Event Row */}
                <TableRow
                  key={group.eventId}
                  className={cn(
                    'cursor-pointer hover:bg-muted/50',
                    isExpanded && 'bg-muted/30'
                  )}
                  onClick={() => toggleEvent(group.eventId)}
                >
                  <TableCell className="w-8">
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </TableCell>
                  <TableCell className="font-medium">
                    {group.homeTeam} vs {group.awayTeam}
                  </TableCell>
                  <TableCell>
                    <span title={format(new Date(group.kickoff), 'PPpp')}>
                      {format(new Date(group.kickoff), 'MMM d, HH:mm')}
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    <Badge variant="secondary">{group.alerts.length}</Badge>
                  </TableCell>
                  <TableCell>{getSeverityBadge(group.maxSeverity)}</TableCell>
                </TableRow>

                {/* Expanded Alert Rows */}
                {isExpanded && group.alerts.map((alert) => {
                  const isAcknowledged = alert.status === 'acknowledged'
                  const isPast = alert.status === 'past'

                  return (
                    <TableRow
                      key={alert.id}
                      className="bg-muted/10 hover:bg-muted/20"
                    >
                      <TableCell></TableCell>
                      <TableCell colSpan={4}>
                        <div className="flex items-center justify-between py-2">
                          <div className="flex items-center gap-4">
                            <div className="flex flex-col">
                              <div className="flex items-center gap-2">
                                <span className="font-medium">{alert.marketName}</span>
                                {alert.line && (
                                  <span className="text-xs text-muted-foreground">
                                    ({alert.line})
                                  </span>
                                )}
                                {getTypeBadge(alert.alertType)}
                                {getSeverityBadge(alert.severity)}
                              </div>
                              <div className="flex items-center gap-3 text-sm text-muted-foreground mt-1">
                                {/* Alert type specific display */}
                                {alert.alertType === 'price_change' && (
                                  <>
                                    <span className="capitalize">{getBookmakerName(alert.bookmakerSlug)}</span>
                                    {alert.outcomeName && (
                                      <>
                                        <span>•</span>
                                        <span>{alert.outcomeName}</span>
                                      </>
                                    )}
                                    <span>•</span>
                                    <span className="font-mono">
                                      {formatOdds(alert.oldValue)} → {formatOdds(alert.newValue)}
                                    </span>
                                    <span>•</span>
                                    <span
                                      className={cn(
                                        'font-mono',
                                        alert.changePercent >= 10
                                          ? 'text-red-600'
                                          : alert.changePercent >= 5
                                          ? 'text-orange-600'
                                          : 'text-yellow-600'
                                      )}
                                    >
                                      {formatChange(alert.changePercent)}
                                    </span>
                                  </>
                                )}
                                {alert.alertType === 'direction_disagreement' && (() => {
                                  const competitor = parseCompetitorDirection(alert.competitorDirection)
                                  // For direction alerts, we show BetPawa's movement vs competitor's movement
                                  // If competitor went UP, BetPawa went DOWN (or vice versa)
                                  const competitorMovement = competitor?.movement || 'unknown'
                                  const betpawaMovement = competitorMovement === 'up' ? 'down' : 'up'
                                  return (
                                    <>
                                      <span className="capitalize">{getBookmakerName(alert.bookmakerSlug)}</span>
                                      {alert.outcomeName && (
                                        <>
                                          <span>•</span>
                                          <span>{alert.outcomeName}</span>
                                        </>
                                      )}
                                      <span>•</span>
                                      <span className="text-purple-600 font-medium">
                                        BetPawa {getDirectionArrow(betpawaMovement)} while {competitor?.bookmaker} {getDirectionArrow(competitorMovement)}
                                      </span>
                                      <span>•</span>
                                      <span className="font-mono text-muted-foreground">
                                        Gap: {alert.changePercent.toFixed(2)}%
                                      </span>
                                    </>
                                  )
                                })()}
                                {alert.alertType === 'availability' && (() => {
                                  const statusText = alert.competitorDirection === 'suspended'
                                    ? 'Market suspended'
                                    : alert.competitorDirection === 'returned'
                                    ? 'Market returned'
                                    : alert.competitorDirection || 'Status changed'
                                  return (
                                    <>
                                      <span className="capitalize">{getBookmakerName(alert.bookmakerSlug)}</span>
                                      {alert.outcomeName && (
                                        <>
                                          <span>•</span>
                                          <span>{alert.outcomeName}</span>
                                        </>
                                      )}
                                      <span>•</span>
                                      <span className={cn(
                                        'font-medium',
                                        alert.competitorDirection === 'suspended' ? 'text-red-600' : 'text-green-600'
                                      )}>
                                        {statusText}
                                      </span>
                                    </>
                                  )
                                })()}
                              </div>
                              <div className="text-xs text-muted-foreground mt-1">
                                Detected {formatDistanceToNow(new Date(alert.detectedAt), { addSuffix: true })}
                                {alert.acknowledgedAt && (
                                  <> • Acknowledged {format(new Date(alert.acknowledgedAt), 'MMM d, HH:mm')}</>
                                )}
                              </div>
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={(e) => {
                                e.stopPropagation()
                                openHistory(alert)
                              }}
                              title="View odds history"
                            >
                              <LineChart className="h-4 w-4" />
                            </Button>

                            {isPast ? (
                              <Badge variant="secondary">Past</Badge>
                            ) : isAcknowledged ? (
                              <Button
                                variant="ghost"
                                size="sm"
                                className="text-green-600"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleAcknowledge(alert.id, true)
                                }}
                                disabled={acknowledgeAlert.isPending}
                              >
                                <Check className="h-4 w-4 mr-1" />
                                Ack'd
                              </Button>
                            ) : (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={(e) => {
                                  e.stopPropagation()
                                  handleAcknowledge(alert.id, false)
                                }}
                                disabled={acknowledgeAlert.isPending}
                              >
                                Acknowledge
                              </Button>
                            )}
                          </div>
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </>
            )
          })}
        </TableBody>
      </Table>

      {/* History Dialog */}
      {historyDialog && (
        <HistoryDialog
          open={historyDialog.open}
          onOpenChange={(open) => {
            if (!open) setHistoryDialog(null)
          }}
          eventId={historyDialog.eventId}
          marketId={historyDialog.marketId}
          line={historyDialog.line}
          bookmakerSlug={historyDialog.bookmakerSlug}
          marketName={historyDialog.marketName}
          bookmakerName={historyDialog.bookmakerName}
        />
      )}
    </>
  )
}
