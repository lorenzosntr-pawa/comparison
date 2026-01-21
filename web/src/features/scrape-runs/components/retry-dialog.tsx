import { useState } from 'react'
import { useNavigate } from 'react-router'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { Loader2, RotateCcw } from 'lucide-react'
import { useRetry } from '../hooks/use-retry'
import { cn } from '@/lib/utils'

// Platform colors for visual distinction
const PLATFORM_COLORS: Record<string, string> = {
  betpawa: 'bg-amber-500',
  sportybet: 'bg-green-500',
  bet9ja: 'bg-blue-500',
}

interface FailedPlatform {
  name: string
  errorCount: number
}

interface RetryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  runId: number
  failedPlatforms: FailedPlatform[]
}

export function RetryDialog({
  open,
  onOpenChange,
  runId,
  failedPlatforms,
}: RetryDialogProps) {
  const navigate = useNavigate()
  const { mutate: retry, isPending, error } = useRetry()

  // Track which platforms are selected (all selected by default)
  const [selectedPlatforms, setSelectedPlatforms] = useState<Set<string>>(
    () => new Set(failedPlatforms.map((p) => p.name))
  )

  const togglePlatform = (platform: string) => {
    setSelectedPlatforms((prev) => {
      const next = new Set(prev)
      if (next.has(platform)) {
        next.delete(platform)
      } else {
        next.add(platform)
      }
      return next
    })
  }

  const handleRetry = () => {
    retry(
      { runId, platforms: Array.from(selectedPlatforms) },
      {
        onSuccess: (data) => {
          onOpenChange(false)
          // Navigate to new run's detail page
          navigate(`/scrape-runs/${data.new_run_id}`)
        },
      }
    )
  }

  const selectedCount = selectedPlatforms.size
  const canRetry = selectedCount > 0 && !isPending

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <RotateCcw className="h-5 w-5" />
            Retry Failed Platforms
          </DialogTitle>
          <DialogDescription>
            Select which platforms to retry. A new scrape run will be created.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3 py-4">
          {failedPlatforms.map((platform) => (
            <div
              key={platform.name}
              className={cn(
                'flex items-center justify-between rounded-lg border p-3',
                'hover:bg-muted/50 transition-colors cursor-pointer',
                selectedPlatforms.has(platform.name) && 'border-primary bg-primary/5'
              )}
              onClick={() => togglePlatform(platform.name)}
            >
              <div className="flex items-center gap-3">
                <Checkbox
                  checked={selectedPlatforms.has(platform.name)}
                  onCheckedChange={() => togglePlatform(platform.name)}
                  onClick={(e) => e.stopPropagation()}
                />
                <div className="flex items-center gap-2">
                  <div
                    className={cn(
                      'h-3 w-3 rounded-full',
                      PLATFORM_COLORS[platform.name] || 'bg-gray-500'
                    )}
                  />
                  <span className="font-medium capitalize">{platform.name}</span>
                </div>
              </div>
              {platform.errorCount > 0 && (
                <Badge variant="destructive" className="text-xs">
                  {platform.errorCount} error{platform.errorCount !== 1 ? 's' : ''}
                </Badge>
              )}
            </div>
          ))}

          {failedPlatforms.length === 0 && (
            <p className="text-center text-muted-foreground py-4">
              No failed platforms to retry.
            </p>
          )}
        </div>

        {error && (
          <p className="text-sm text-destructive">
            {error instanceof Error ? error.message : 'Retry failed'}
          </p>
        )}

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={isPending}
          >
            Cancel
          </Button>
          <Button onClick={handleRetry} disabled={!canRetry}>
            {isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            Retry {selectedCount > 0 ? `(${selectedCount})` : ''}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
