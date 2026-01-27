import { useNavigate } from 'react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useScrapeRuns, type ScrapeRun } from '../hooks'
import { cn } from '@/lib/utils'
import { formatDistanceToNow } from 'date-fns'
import { ChevronRight } from 'lucide-react'

const statusVariants: Record<
  string,
  'default' | 'destructive' | 'secondary' | 'outline'
> = {
  completed: 'default',
  partial: 'secondary',
  failed: 'destructive',
  connection_failed: 'destructive',
  running: 'outline',
  pending: 'outline',
}

function formatStatus(status: string): string {
  if (status === 'connection_failed') return 'Connection Lost'
  return status
}

function formatDuration(run: ScrapeRun): string {
  if (!run.completed_at) return '-'
  const start = new Date(run.started_at).getTime()
  const end = new Date(run.completed_at).getTime()
  const seconds = Math.round((end - start) / 1000)
  if (seconds < 60) return `${seconds}s`
  const minutes = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${minutes}m ${secs}s`
}

function PlatformChips({
  timings,
}: {
  timings: ScrapeRun['platform_timings']
}) {
  if (!timings) return <span className="text-muted-foreground">-</span>

  return (
    <div className="flex flex-wrap gap-1">
      {Object.entries(timings).map(([platform, data]) => (
        <span
          key={platform}
          className="inline-flex items-center gap-1 rounded-md bg-secondary px-1.5 py-0.5 text-xs"
        >
          <span className="font-medium capitalize">{platform}</span>
          <span className="text-muted-foreground">
            {data.events_count}
          </span>
        </span>
      ))}
    </div>
  )
}

export function RunsTable() {
  const navigate = useNavigate()
  const { data, isPending, error } = useScrapeRuns(50)

  if (isPending) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Run History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle>Run History</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">Failed to load run history</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Run History</CardTitle>
      </CardHeader>
      <CardContent>
        {data?.length === 0 ? (
          <p className="text-sm text-muted-foreground">No scrape runs yet</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Duration</TableHead>
                <TableHead>Events</TableHead>
                <TableHead>Trigger</TableHead>
                <TableHead>Platforms</TableHead>
                <TableHead className="w-8"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.map((run) => (
                <TableRow
                  key={run.id}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => navigate(`/scrape-runs/${run.id}`)}
                >
                  <TableCell className="font-medium">
                    {formatDistanceToNow(new Date(run.started_at), {
                      addSuffix: true,
                    })}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={statusVariants[run.status]}
                      className={cn(
                        run.status === 'completed' &&
                          'bg-green-500 hover:bg-green-600'
                      )}
                    >
                      {formatStatus(run.status)}
                    </Badge>
                  </TableCell>
                  <TableCell>{formatDuration(run)}</TableCell>
                  <TableCell>
                    <span className="font-medium">{run.events_scraped}</span>
                    {run.events_failed > 0 && (
                      <span className="text-destructive">
                        {' '}
                        ({run.events_failed} failed)
                      </span>
                    )}
                  </TableCell>
                  <TableCell className="text-muted-foreground">
                    {run.trigger || '-'}
                  </TableCell>
                  <TableCell>
                    <PlatformChips timings={run.platform_timings} />
                  </TableCell>
                  <TableCell>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}
