import { formatDistanceToNow } from 'date-fns'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useAuditLog } from '../hooks/use-audit-log'

/**
 * Get badge variant based on action type.
 */
function getActionVariant(
  action: string
): 'default' | 'secondary' | 'destructive' | 'outline' {
  switch (action.toUpperCase()) {
    case 'CREATE':
      return 'default' // green-ish default
    case 'UPDATE':
      return 'secondary' // blue-ish
    case 'DELETE':
    case 'DEACTIVATE':
      return 'destructive' // red
    case 'ACTIVATE':
      return 'outline'
    default:
      return 'secondary'
  }
}

/**
 * Get custom classes for action badges.
 */
function getActionClasses(action: string): string {
  switch (action.toUpperCase()) {
    case 'CREATE':
      return 'bg-green-500 hover:bg-green-600 text-white'
    case 'UPDATE':
      return 'bg-blue-500 hover:bg-blue-600 text-white'
    case 'DELETE':
    case 'DEACTIVATE':
      return 'bg-red-500 hover:bg-red-600 text-white'
    case 'ACTIVATE':
      return 'bg-emerald-500 hover:bg-emerald-600 text-white'
    default:
      return ''
  }
}

export function RecentChanges() {
  const { data, isLoading, error } = useAuditLog({ page: 1, pageSize: 10 })

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Changes</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-500">Failed to load audit log</p>
        </CardContent>
      </Card>
    )
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recent Changes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Skeleton className="h-5 w-16" />
                <Skeleton className="h-4 w-32" />
              </div>
              <Skeleton className="h-4 w-20" />
            </div>
          ))}
        </CardContent>
      </Card>
    )
  }

  const items = data?.items ?? []

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Recent Changes</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-4">
            No changes yet
          </p>
        ) : (
          <div className="space-y-3">
            {items.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between text-sm"
              >
                <div className="flex items-center gap-2 min-w-0">
                  <Badge className={getActionClasses(item.action)}>
                    {item.action}
                  </Badge>
                  <span className="font-mono text-xs truncate">
                    {item.canonicalId}
                  </span>
                </div>
                <span className="text-muted-foreground text-xs whitespace-nowrap ml-2">
                  {formatDistanceToNow(new Date(item.createdAt), {
                    addSuffix: true,
                  })}
                </span>
              </div>
            ))}
          </div>
        )}
        {items.length > 0 && data && data.total > 10 && (
          <div className="mt-4 pt-3 border-t">
            <button
              type="button"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              View All ({data.total})
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
