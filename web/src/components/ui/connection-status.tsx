import { cn } from '@/lib/utils'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip'
import { Button } from '@/components/ui/button'
import type { WebSocketState } from '@/hooks/use-websocket'

export interface ConnectionStatusIndicatorProps {
  /** Current WebSocket connection state */
  state: WebSocketState
  /** Optional callback for manual reconnection (shows Retry button in error state) */
  onReconnect?: () => void
  /** Whether to show a text label next to the indicator */
  showLabel?: boolean
  /** Optional error message to show in tooltip */
  error?: string | null
  /** Optional className for the container */
  className?: string
}

/**
 * Compact connection status indicator with optional retry button.
 *
 * Visual states:
 * - connected: green dot
 * - connecting: yellow dot with pulse animation
 * - disconnected: gray dot
 * - error: red dot with optional Retry button
 */
export function ConnectionStatusIndicator({
  state,
  onReconnect,
  showLabel = false,
  error,
  className,
}: ConnectionStatusIndicatorProps) {
  const getStateConfig = () => {
    switch (state) {
      case 'connected':
        return {
          color: 'bg-green-500',
          pulse: false,
          label: 'Connected',
          tooltip: 'WebSocket connected',
        }
      case 'connecting':
        return {
          color: 'bg-yellow-500',
          pulse: true,
          label: 'Connecting',
          tooltip: 'Connecting to WebSocket...',
        }
      case 'disconnected':
        return {
          color: 'bg-gray-500',
          pulse: false,
          label: 'Disconnected',
          tooltip: 'WebSocket disconnected',
        }
      case 'error':
        return {
          color: 'bg-red-500',
          pulse: false,
          label: 'Error',
          tooltip: error ?? 'Connection error',
        }
      default:
        return {
          color: 'bg-gray-500',
          pulse: false,
          label: 'Unknown',
          tooltip: 'Unknown state',
        }
    }
  }

  const config = getStateConfig()

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className={cn('flex items-center gap-1.5', className)}>
            {/* Status dot */}
            <span
              className={cn(
                'h-2 w-2 rounded-full',
                config.color,
                config.pulse && 'animate-pulse'
              )}
            />

            {/* Optional label */}
            {showLabel && (
              <span className="text-xs text-muted-foreground">{config.label}</span>
            )}

            {/* Retry button for error state */}
            {state === 'error' && onReconnect && (
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  onReconnect()
                }}
                className="h-5 px-1.5 text-xs"
              >
                Retry
              </Button>
            )}
          </div>
        </TooltipTrigger>
        <TooltipContent side="bottom">
          <p>{config.tooltip}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
