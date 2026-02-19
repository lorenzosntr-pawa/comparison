/**
 * Alert table component with expandable rows for risk monitoring.
 *
 * @module alert-table
 */

import { useState } from 'react'
import { format, formatDistanceToNow } from 'date-fns'
import { ChevronDown, ChevronRight, Check } from 'lucide-react'
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

interface AlertTableProps {
  alerts: RiskAlert[]
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
  return `${sign}${change.toFixed(1)}%`
}

/** Format odds value */
function formatOdds(value: number | null): string {
  if (value === null) return '-'
  return value.toFixed(2)
}

export function AlertTable({ alerts }: AlertTableProps) {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set())
  const acknowledgeAlert = useAcknowledgeAlert()

  const toggleRow = (id: number) => {
    setExpandedRows((prev) => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
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

  if (alerts.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No alerts match the current filters
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead className="w-8"></TableHead>
          <TableHead>Event</TableHead>
          <TableHead>Market</TableHead>
          <TableHead>Type</TableHead>
          <TableHead className="text-right">Change</TableHead>
          <TableHead>Severity</TableHead>
          <TableHead>Detected</TableHead>
          <TableHead className="text-right">Actions</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {alerts.map((alert) => {
          const isExpanded = expandedRows.has(alert.id)
          const isAcknowledged = alert.status === 'acknowledged'
          const isPast = alert.status === 'past'

          return (
            <>
              <TableRow
                key={alert.id}
                className={cn(
                  'cursor-pointer hover:bg-muted/50',
                  isExpanded && 'bg-muted/30'
                )}
                onClick={() => toggleRow(alert.id)}
              >
                <TableCell className="w-8">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </TableCell>
                <TableCell className="font-medium">
                  Event #{alert.eventId}
                </TableCell>
                <TableCell>
                  <div className="flex flex-col">
                    <span>{alert.marketName}</span>
                    {alert.line && (
                      <span className="text-xs text-muted-foreground">
                        Line: {alert.line}
                      </span>
                    )}
                  </div>
                </TableCell>
                <TableCell>{getTypeBadge(alert.alertType)}</TableCell>
                <TableCell className="text-right font-mono">
                  <span
                    className={cn(
                      alert.changePercent >= 10
                        ? 'text-red-600'
                        : alert.changePercent >= 5
                        ? 'text-orange-600'
                        : 'text-yellow-600'
                    )}
                  >
                    {formatChange(alert.changePercent)}
                  </span>
                </TableCell>
                <TableCell>{getSeverityBadge(alert.severity)}</TableCell>
                <TableCell>
                  <span title={format(new Date(alert.detectedAt), 'PPpp')}>
                    {formatDistanceToNow(new Date(alert.detectedAt), {
                      addSuffix: true,
                    })}
                  </span>
                </TableCell>
                <TableCell className="text-right">
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
                </TableCell>
              </TableRow>
              {isExpanded && (
                <TableRow key={`${alert.id}-expanded`} className="bg-muted/20">
                  <TableCell colSpan={8} className="py-4">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Bookmaker:</span>
                        <div className="font-medium capitalize">
                          {alert.bookmakerSlug}
                        </div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Outcome:</span>
                        <div className="font-medium">
                          {alert.outcomeName || '-'}
                        </div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Old → New:</span>
                        <div className="font-medium font-mono">
                          {formatOdds(alert.oldValue)} → {formatOdds(alert.newValue)}
                        </div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Kickoff:</span>
                        <div className="font-medium">
                          {format(new Date(alert.eventKickoff), 'MMM d, HH:mm')}
                        </div>
                      </div>
                      {alert.competitorDirection && (
                        <div>
                          <span className="text-muted-foreground">
                            Competitor Direction:
                          </span>
                          <div className="font-medium">
                            {alert.competitorDirection}
                          </div>
                        </div>
                      )}
                      {alert.acknowledgedAt && (
                        <div>
                          <span className="text-muted-foreground">
                            Acknowledged:
                          </span>
                          <div className="font-medium">
                            {format(
                              new Date(alert.acknowledgedAt),
                              'MMM d, HH:mm'
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              )}
            </>
          )
        })}
      </TableBody>
    </Table>
  )
}
