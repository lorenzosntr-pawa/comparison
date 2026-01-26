import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Database, Loader2, AlertTriangle, CheckCircle2, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'
import { useSettings } from '../hooks'

const RETENTION_OPTIONS = [
  { value: '7', label: '7 days' },
  { value: '14', label: '14 days' },
  { value: '30', label: '30 days' },
  { value: '60', label: '60 days' },
  { value: '90', label: '90 days' },
  { value: '180', label: '180 days' },
  { value: '365', label: '1 year' },
]

function formatNumber(n: number): string {
  return n.toLocaleString()
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString()
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'just now'
  if (diffMins < 60) return `${diffMins} min ago`
  if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
}

function DataOverviewTab() {
  const { data: stats, isLoading, error } = useQuery({
    queryKey: ['cleanup', 'stats'],
    queryFn: () => api.getCleanupStats(),
  })

  if (isLoading) {
    return (
      <div className="space-y-3 py-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="flex justify-between items-center">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-20" />
          </div>
        ))}
      </div>
    )
  }

  if (error || !stats) {
    return (
      <div className="py-4 text-destructive">
        Failed to load data statistics
      </div>
    )
  }

  const tableData = [
    { label: 'Odds Snapshots', stats: stats.oddsSnapshots },
    { label: 'Competitor Odds', stats: stats.competitorOddsSnapshots },
    { label: 'Events', stats: stats.events },
    { label: 'Competitor Events', stats: stats.competitorEvents },
    { label: 'Tournaments', stats: stats.tournaments },
    { label: 'Competitor Tournaments', stats: stats.competitorTournaments },
    { label: 'Scrape Runs', stats: stats.scrapeRuns },
    { label: 'Scrape Batches', stats: stats.scrapeBatches },
  ]

  return (
    <div className="space-y-4 py-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Data Type</TableHead>
            <TableHead className="text-right">Records</TableHead>
            <TableHead className="text-right">Oldest</TableHead>
            <TableHead className="text-right">Newest</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {tableData.map((row) => (
            <TableRow key={row.label}>
              <TableCell className="font-medium">{row.label}</TableCell>
              <TableCell className="text-right">
                {formatNumber(row.stats.count)}
              </TableCell>
              <TableCell className="text-right text-muted-foreground text-sm">
                {formatDate(row.stats.oldest)}
              </TableCell>
              <TableCell className="text-right text-muted-foreground text-sm">
                {formatDate(row.stats.newest)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {stats.eventsByPlatform.length > 0 && (
        <div className="pt-2">
          <h4 className="text-sm font-medium mb-2">Events by Platform</h4>
          <div className="flex gap-2 flex-wrap">
            {stats.eventsByPlatform.map((p) => (
              <Badge key={p.platform} variant="secondary">
                {p.platform}: {formatNumber(p.count)}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function CleanupTab({ onClose }: { onClose: () => void }) {
  const { data: settings } = useSettings()
  const [oddsDays, setOddsDays] = useState<number | undefined>(undefined)
  const [matchDays, setMatchDays] = useState<number | undefined>(undefined)
  const [showPreview, setShowPreview] = useState(false)
  const queryClient = useQueryClient()

  // Use settings values as defaults when they load
  const effectiveOddsDays = oddsDays ?? settings?.oddsRetentionDays ?? 30
  const effectiveMatchDays = matchDays ?? settings?.matchRetentionDays ?? 30

  const previewQuery = useQuery({
    queryKey: ['cleanup', 'preview', effectiveOddsDays, effectiveMatchDays],
    queryFn: () => api.getCleanupPreview({
      oddsDays: effectiveOddsDays,
      matchDays: effectiveMatchDays
    }),
    enabled: showPreview,
  })

  const cleanupMutation = useMutation({
    mutationFn: () => api.executeCleanup({
      oddsDays: effectiveOddsDays,
      matchDays: effectiveMatchDays
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cleanup'] })
      onClose()
    },
  })

  const totalToDelete = previewQuery.data
    ? previewQuery.data.oddsSnapshotsCount +
      previewQuery.data.competitorOddsSnapshotsCount +
      previewQuery.data.scrapeRunsCount +
      previewQuery.data.eventsCount +
      previewQuery.data.competitorEventsCount +
      previewQuery.data.tournamentsCount +
      previewQuery.data.competitorTournamentsCount
    : 0

  return (
    <div className="space-y-4 py-4">
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Delete odds older than</label>
          <Select
            value={String(effectiveOddsDays)}
            onValueChange={(v) => {
              setOddsDays(Number(v))
              setShowPreview(false)
            }}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {RETENTION_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Delete matches older than</label>
          <Select
            value={String(effectiveMatchDays)}
            onValueChange={(v) => {
              setMatchDays(Number(v))
              setShowPreview(false)
            }}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {RETENTION_OPTIONS.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {!showPreview ? (
        <Button variant="outline" onClick={() => setShowPreview(true)}>
          Preview Cleanup
        </Button>
      ) : previewQuery.isLoading ? (
        <div className="flex items-center gap-2 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          Loading preview...
        </div>
      ) : previewQuery.error ? (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>Failed to load cleanup preview</AlertDescription>
        </Alert>
      ) : previewQuery.data ? (
        <div className="space-y-4">
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertTitle>Cleanup Preview</AlertTitle>
            <AlertDescription>
              <p className="mb-2">
                This will permanently delete <strong>{formatNumber(totalToDelete)}</strong> records:
              </p>
              <ul className="list-disc list-inside text-sm space-y-1">
                {previewQuery.data.oddsSnapshotsCount > 0 && (
                  <li>{formatNumber(previewQuery.data.oddsSnapshotsCount)} odds snapshots</li>
                )}
                {previewQuery.data.competitorOddsSnapshotsCount > 0 && (
                  <li>{formatNumber(previewQuery.data.competitorOddsSnapshotsCount)} competitor odds</li>
                )}
                {previewQuery.data.scrapeRunsCount > 0 && (
                  <li>{formatNumber(previewQuery.data.scrapeRunsCount)} scrape runs</li>
                )}
                {previewQuery.data.eventsCount > 0 && (
                  <li>{formatNumber(previewQuery.data.eventsCount)} events</li>
                )}
                {previewQuery.data.competitorEventsCount > 0 && (
                  <li>{formatNumber(previewQuery.data.competitorEventsCount)} competitor events</li>
                )}
                {previewQuery.data.tournamentsCount > 0 && (
                  <li>{formatNumber(previewQuery.data.tournamentsCount)} tournaments</li>
                )}
                {previewQuery.data.competitorTournamentsCount > 0 && (
                  <li>{formatNumber(previewQuery.data.competitorTournamentsCount)} competitor tournaments</li>
                )}
                {totalToDelete === 0 && (
                  <li className="text-muted-foreground">No records to delete</li>
                )}
              </ul>
            </AlertDescription>
          </Alert>

          <div className="flex gap-2">
            <Button
              variant="destructive"
              onClick={() => cleanupMutation.mutate()}
              disabled={cleanupMutation.isPending || totalToDelete === 0}
            >
              {cleanupMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Cleaning...
                </>
              ) : (
                'Delete Now'
              )}
            </Button>
            <Button variant="outline" onClick={() => setShowPreview(false)}>
              Cancel
            </Button>
          </div>

          {cleanupMutation.error && (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Cleanup Failed</AlertTitle>
              <AlertDescription>
                An error occurred during cleanup. Please try again.
              </AlertDescription>
            </Alert>
          )}
        </div>
      ) : null}
    </div>
  )
}

function CleanupHistoryTab() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['cleanup', 'history'],
    queryFn: () => api.getCleanupHistory(20),
  })

  if (isLoading) {
    return (
      <div className="space-y-3 py-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="flex justify-between items-center">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-20" />
          </div>
        ))}
      </div>
    )
  }

  if (error) {
    return (
      <div className="py-4 text-destructive">
        Failed to load cleanup history
      </div>
    )
  }

  if (!data || data.runs.length === 0) {
    return (
      <div className="py-8 text-center text-muted-foreground">
        No cleanup runs yet
      </div>
    )
  }

  return (
    <div className="py-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead>Trigger</TableHead>
            <TableHead className="text-right">Deleted</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.runs.map((run) => {
            const totalDeleted =
              run.oddsDeleted +
              run.competitorOddsDeleted +
              run.scrapeRunsDeleted +
              run.eventsDeleted +
              run.competitorEventsDeleted +
              run.tournamentsDeleted +
              run.competitorTournamentsDeleted

            return (
              <TableRow key={run.id}>
                <TableCell className="font-medium">
                  <span title={new Date(run.startedAt).toLocaleString()}>
                    {formatRelativeTime(run.startedAt)}
                  </span>
                </TableCell>
                <TableCell>
                  <Badge variant={run.trigger === 'manual' ? 'default' : 'secondary'}>
                    {run.trigger}
                  </Badge>
                </TableCell>
                <TableCell className="text-right">
                  {formatNumber(totalDeleted)}
                </TableCell>
                <TableCell>
                  {run.status === 'completed' ? (
                    <CheckCircle2 className="h-4 w-4 text-green-500" />
                  ) : run.status === 'failed' ? (
                    <span title={run.errorMessage ?? 'Unknown error'}>
                      <XCircle className="h-4 w-4 text-destructive" />
                    </span>
                  ) : (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  )}
                </TableCell>
              </TableRow>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}

export function ManageDataButton() {
  const [open, setOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<string>('overview')

  return (
    <>
      <Button
        variant="outline"
        className="w-full"
        onClick={() => setOpen(true)}
      >
        <Database className="mr-2 h-4 w-4" />
        Manage Data
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Manage Data</DialogTitle>
            <DialogDescription>
              View storage statistics and manage data retention
            </DialogDescription>
          </DialogHeader>

          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="cleanup">Clean Up</TabsTrigger>
              <TabsTrigger value="history">History</TabsTrigger>
            </TabsList>

            <TabsContent value="overview">
              <DataOverviewTab />
            </TabsContent>

            <TabsContent value="cleanup">
              <CleanupTab onClose={() => setOpen(false)} />
            </TabsContent>

            <TabsContent value="history">
              <CleanupHistoryTab />
            </TabsContent>
          </Tabs>
        </DialogContent>
      </Dialog>
    </>
  )
}
