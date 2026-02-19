/**
 * Risk Monitoring page for viewing and managing odds movement alerts.
 *
 * @module risk-monitoring
 */

import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { useAlerts, type AlertFilters } from './hooks'
import { AlertTable } from './components'

type StatusTab = 'new' | 'acknowledged' | 'past'
type SeverityFilter = 'all' | 'warning' | 'elevated' | 'critical'
type TypeFilter = 'all' | 'price_change' | 'direction_disagreement' | 'availability'

const PAGE_SIZE = 50

export function RiskMonitoringPage() {
  const [statusTab, setStatusTab] = useState<StatusTab>('new')
  const [severity, setSeverity] = useState<SeverityFilter>('all')
  const [alertType, setAlertType] = useState<TypeFilter>('all')
  const [offset, setOffset] = useState(0)

  // Build filters from state
  const filters: AlertFilters = {
    status: statusTab,
    severity: severity === 'all' ? null : severity,
    alertType: alertType === 'all' ? null : alertType,
    limit: PAGE_SIZE,
    offset,
  }

  const { data, isLoading, error } = useAlerts(filters)

  // Reset offset when filters change
  const handleStatusChange = (value: string) => {
    setStatusTab(value as StatusTab)
    setOffset(0)
  }

  const handleSeverityChange = (value: string) => {
    setSeverity(value as SeverityFilter)
    setOffset(0)
  }

  const handleTypeChange = (value: string) => {
    setAlertType(value as TypeFilter)
    setOffset(0)
  }

  // Pagination
  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1

  const handleNextPage = () => {
    if (data && offset + PAGE_SIZE < data.total) {
      setOffset(offset + PAGE_SIZE)
    }
  }

  const handlePrevPage = () => {
    if (offset > 0) {
      setOffset(Math.max(0, offset - PAGE_SIZE))
    }
  }

  // Total count for badge
  const totalAlerts = (data?.newCount ?? 0) + (data?.acknowledgedCount ?? 0) + (data?.pastCount ?? 0)

  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Risk Monitoring</h1>
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">
              Failed to load alerts. Please try again later.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3">
        <h1 className="text-2xl font-bold">Risk Monitoring</h1>
        {totalAlerts > 0 && (
          <Badge variant="secondary">{totalAlerts} total</Badge>
        )}
      </div>

      {/* Status Tabs */}
      <Tabs value={statusTab} onValueChange={handleStatusChange}>
        <TabsList>
          <TabsTrigger value="new" className="gap-2">
            New
            {data && data.newCount > 0 && (
              <Badge variant="destructive" className="ml-1">
                {data.newCount}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="acknowledged" className="gap-2">
            Acknowledged
            {data && data.acknowledgedCount > 0 && (
              <Badge variant="secondary" className="ml-1">
                {data.acknowledgedCount}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="past" className="gap-2">
            Past
            {data && data.pastCount > 0 && (
              <Badge variant="outline" className="ml-1">
                {data.pastCount}
              </Badge>
            )}
          </TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="w-40">
          <Select value={severity} onValueChange={handleSeverityChange}>
            <SelectTrigger>
              <SelectValue placeholder="Severity" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Severities</SelectItem>
              <SelectItem value="warning">Warning</SelectItem>
              <SelectItem value="elevated">Elevated</SelectItem>
              <SelectItem value="critical">Critical</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div className="w-48">
          <Select value={alertType} onValueChange={handleTypeChange}>
            <SelectTrigger>
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="price_change">Price Change</SelectItem>
              <SelectItem value="direction_disagreement">Direction Disagreement</SelectItem>
              <SelectItem value="availability">Availability</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="pt-4">
          {isLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : (
            <AlertTable alerts={data?.alerts ?? []} />
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {data && data.total > PAGE_SIZE && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            Showing {offset + 1}-{Math.min(offset + PAGE_SIZE, data.total)} of{' '}
            {data.total} alerts
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePrevPage}
              disabled={offset === 0}
            >
              Previous
            </Button>
            <span className="flex items-center px-2 text-sm">
              Page {currentPage} of {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={handleNextPage}
              disabled={offset + PAGE_SIZE >= data.total}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
