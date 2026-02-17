/**
 * Alerts banner component for displaying storage alerts.
 *
 * Shows active storage alerts at the top of the Storage page with
 * visual distinction between warning and critical alerts.
 */

import { formatDistanceToNow } from 'date-fns'
import { AlertTriangle, AlertCircle, X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import type { StorageAlert } from '../hooks'

interface AlertsBannerProps {
  alerts: StorageAlert[]
  onDismiss: (alertId: number) => void
  dismissingId?: number | null
}

/**
 * Get styling based on alert type.
 */
function getAlertStyles(alertType: StorageAlert['alertType']) {
  if (alertType === 'size_critical') {
    return {
      bg: 'bg-red-50 border-red-200 dark:bg-red-950 dark:border-red-900',
      icon: <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />,
      badge: <Badge variant="destructive">Critical</Badge>,
    }
  }
  return {
    bg: 'bg-amber-50 border-amber-200 dark:bg-amber-950 dark:border-amber-900',
    icon: <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400" />,
    badge: <Badge variant="outline" className="border-amber-500 text-amber-700 dark:text-amber-400">Warning</Badge>,
  }
}

/**
 * Format growth percentage for display.
 */
function formatGrowth(percent: number): string {
  if (percent === 0) return ''
  const sign = percent > 0 ? '+' : ''
  return `${sign}${percent.toFixed(1)}%`
}

export function AlertsBanner({ alerts, onDismiss, dismissingId }: AlertsBannerProps) {
  // Don't render if no alerts
  if (alerts.length === 0) {
    return null
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert) => {
        const styles = getAlertStyles(alert.alertType)
        const isDismissing = dismissingId === alert.id

        return (
          <div
            key={alert.id}
            className={cn(
              'flex items-start gap-3 p-4 rounded-lg border',
              styles.bg
            )}
          >
            <div className="flex-shrink-0 mt-0.5">
              {styles.icon}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                {styles.badge}
                {alert.growthPercent > 0 && (
                  <span className="text-sm font-medium text-muted-foreground">
                    {formatGrowth(alert.growthPercent)}
                  </span>
                )}
                <span className="text-xs text-muted-foreground">
                  {formatDistanceToNow(new Date(alert.createdAt), { addSuffix: true })}
                </span>
              </div>
              <p className="text-sm text-foreground">{alert.message}</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="flex-shrink-0 h-8 w-8 p-0"
              onClick={() => onDismiss(alert.id)}
              disabled={isDismissing}
              aria-label="Dismiss alert"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        )
      })}
    </div>
  )
}
