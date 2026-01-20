import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

interface StatusCardProps {
  title: string
  status: 'healthy' | 'degraded' | 'unhealthy' | 'running' | 'stopped'
  subtitle?: string
  children?: React.ReactNode
  isPending?: boolean
}

const statusColors = {
  healthy: 'bg-green-500',
  running: 'bg-green-500',
  degraded: 'bg-yellow-500',
  unhealthy: 'bg-red-500',
  stopped: 'bg-gray-500',
}

const statusLabels = {
  healthy: 'Healthy',
  running: 'Running',
  degraded: 'Degraded',
  unhealthy: 'Unhealthy',
  stopped: 'Stopped',
}

export function StatusCard({
  title,
  status,
  subtitle,
  children,
  isPending,
}: StatusCardProps) {
  if (isPending) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <Skeleton className="h-4 w-24" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-6 w-16 mb-2" />
          <Skeleton className="h-4 w-32" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-2 mb-1">
          <span className={cn('h-2 w-2 rounded-full', statusColors[status])} />
          <span className="text-lg font-semibold">{statusLabels[status]}</span>
        </div>
        {subtitle && (
          <p className="text-sm text-muted-foreground">{subtitle}</p>
        )}
        {children}
      </CardContent>
    </Card>
  )
}
