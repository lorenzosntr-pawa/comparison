import { cn } from '@/lib/utils'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  CheckCircle2,
  Circle,
  Loader2,
  XCircle,
  Search,
  Download,
  Database,
  Package,
} from 'lucide-react'
import type { PlatformProgress } from '../hooks/use-scrape-progress'

// Platform styling
const PLATFORM_STYLES: Record<string, { border: string; text: string; bg: string }> = {
  betpawa: {
    border: 'border-green-500/30',
    text: 'text-green-500',
    bg: 'bg-green-500',
  },
  sportybet: {
    border: 'border-blue-500/30',
    text: 'text-blue-500',
    bg: 'bg-blue-500',
  },
  bet9ja: {
    border: 'border-orange-500/30',
    text: 'text-orange-500',
    bg: 'bg-orange-500',
  },
}

// Steps in order for each platform's workflow
const PLATFORM_STEPS = [
  { id: 'discovering', label: 'Discover', icon: Search },
  { id: 'scraping', label: 'Scrape', icon: Download },
  { id: 'mapping', label: 'Map', icon: Package },
  { id: 'storing', label: 'Store', icon: Database },
] as const

type StepId = (typeof PLATFORM_STEPS)[number]['id']

// Determine step status based on current phase
function getStepStatus(
  stepId: StepId,
  currentPhase: string | undefined,
  isComplete: boolean,
  isFailed: boolean,
): 'done' | 'active' | 'pending' | 'failed' {
  if (isFailed) {
    // Find which step failed
    const stepIndex = PLATFORM_STEPS.findIndex((s) => s.id === stepId)
    const failedIndex = PLATFORM_STEPS.findIndex((s) => currentPhase?.includes(s.id))
    if (failedIndex >= 0 && stepIndex <= failedIndex) {
      return stepIndex === failedIndex ? 'failed' : 'done'
    }
    return 'pending'
  }

  if (isComplete) return 'done'

  if (!currentPhase) return 'pending'

  // Map phase to step
  const stepIndex = PLATFORM_STEPS.findIndex((s) => s.id === stepId)
  const currentIndex = PLATFORM_STEPS.findIndex(
    (s) => currentPhase.includes(s.id) || currentPhase === s.id,
  )

  // Special case: completed phase means all done
  if (currentPhase === 'completed' || currentPhase === 'storing_complete') {
    return 'done'
  }

  if (currentIndex < 0) return stepIndex === 0 ? 'active' : 'pending'

  if (stepIndex < currentIndex) return 'done'
  if (stepIndex === currentIndex) return 'active'
  return 'pending'
}

interface PlatformProgressCardProps {
  platform: string
  progress?: PlatformProgress
  timing?: { duration_ms: number; events_count: number } | null
  isActive: boolean
}

export function PlatformProgressCard({
  platform,
  progress,
  timing,
  isActive,
}: PlatformProgressCardProps) {
  const styles = PLATFORM_STYLES[platform] || PLATFORM_STYLES.betpawa
  const isComplete = progress?.isComplete || !!timing
  const isFailed = progress?.isFailed ?? false
  const currentPhase = progress?.phase
  const eventsCount = progress?.eventsCount ?? timing?.events_count ?? 0

  // Calculate overall progress percentage
  const getProgressPercent = () => {
    if (isComplete) return 100
    if (isFailed) return 100
    if (!currentPhase) return 0

    const stepIndex = PLATFORM_STEPS.findIndex(
      (s) => currentPhase.includes(s.id) || currentPhase === s.id,
    )
    if (stepIndex < 0) return 0
    return ((stepIndex + 0.5) / PLATFORM_STEPS.length) * 100
  }

  return (
    <Card
      className={cn(
        'transition-all duration-300',
        isActive && styles.border,
        isComplete && 'opacity-80',
        isFailed && 'border-red-500/30',
      )}
    >
      <CardHeader className="pb-2 pt-3 px-4">
        <div className="flex items-center justify-between">
          <CardTitle className={cn('text-sm font-medium capitalize', isActive && styles.text)}>
            {platform}
            {isActive && <Loader2 className="ml-1.5 inline h-3 w-3 animate-spin" />}
          </CardTitle>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            {isComplete && (
              <>
                <CheckCircle2 className="h-3.5 w-3.5 text-green-500" />
                <span>{eventsCount} events</span>
              </>
            )}
            {isFailed && (
              <>
                <XCircle className="h-3.5 w-3.5 text-red-500" />
                <span>Failed</span>
              </>
            )}
            {!isComplete && !isFailed && eventsCount > 0 && <span>{eventsCount} events</span>}
          </div>
        </div>
      </CardHeader>
      <CardContent className="px-4 pb-3">
        {/* Progress bar */}
        <div className="h-1 w-full rounded-full bg-secondary mb-3">
          <div
            className={cn(
              'h-1 rounded-full transition-all duration-500',
              isComplete && styles.bg,
              isFailed && 'bg-red-500',
              !isComplete && !isFailed && isActive && `${styles.bg} animate-pulse`,
              !isComplete && !isFailed && !isActive && 'bg-muted-foreground/30',
            )}
            style={{ width: `${getProgressPercent()}%` }}
          />
        </div>

        {/* Steps */}
        <div className="flex justify-between">
          {PLATFORM_STEPS.map((step) => {
            const status = getStepStatus(step.id, currentPhase, isComplete, isFailed)
            const Icon = step.icon

            return (
              <div key={step.id} className="flex flex-col items-center gap-1">
                <div
                  className={cn(
                    'flex h-6 w-6 items-center justify-center rounded-full',
                    status === 'done' && 'bg-green-500/10 text-green-500',
                    status === 'active' && `${styles.bg}/10 ${styles.text}`,
                    status === 'pending' && 'bg-muted text-muted-foreground',
                    status === 'failed' && 'bg-red-500/10 text-red-500',
                  )}
                >
                  {status === 'done' && <CheckCircle2 className="h-3.5 w-3.5" />}
                  {status === 'active' && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                  {status === 'pending' && <Circle className="h-3 w-3" />}
                  {status === 'failed' && <XCircle className="h-3.5 w-3.5" />}
                </div>
                <span
                  className={cn(
                    'text-[10px]',
                    status === 'done' && 'text-green-500',
                    status === 'active' && styles.text,
                    status === 'pending' && 'text-muted-foreground',
                    status === 'failed' && 'text-red-500',
                  )}
                >
                  {step.label}
                </span>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
