import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useHealth } from '../hooks'
import { cn } from '@/lib/utils'

export function PlatformHealth() {
  const { data, isPending, error } = useHealth()

  if (isPending) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Platform Health</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-8 w-full" />
          ))}
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Platform Health</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-destructive">
            Failed to load platform health
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">Platform Health</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {data?.platforms.map((platform) => (
          <div
            key={platform.platform}
            className="flex items-center justify-between"
          >
            <span className="text-sm font-medium capitalize">
              {platform.platform}
            </span>
            <div className="flex items-center gap-2">
              {platform.response_time_ms && (
                <span className="text-xs text-muted-foreground">
                  {platform.response_time_ms}ms
                </span>
              )}
              <Badge
                variant={
                  platform.status === 'healthy' ? 'default' : 'destructive'
                }
                className={cn(
                  platform.status === 'healthy' &&
                    'bg-green-500 hover:bg-green-600'
                )}
              >
                {platform.status}
              </Badge>
            </div>
          </div>
        ))}
        <div className="pt-2 border-t">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Database</span>
            <Badge
              variant={
                data?.database === 'connected' ? 'default' : 'destructive'
              }
              className={cn(
                data?.database === 'connected' &&
                  'bg-green-500 hover:bg-green-600'
              )}
            >
              {data?.database}
            </Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
