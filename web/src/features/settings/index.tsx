import type { ReactNode } from 'react'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useSettings } from './hooks'
import {
  CleanupFrequencySelector,
  IntervalSelector,
  ManageDataButton,
  PlatformToggles,
  RetentionSelector,
  SchedulerControl,
} from './components'

interface CompactCardProps {
  title: string
  description: string
  children: ReactNode
}

function CompactCard({ title, description, children }: CompactCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2 pt-4 px-4">
        <CardTitle className="text-base">{title}</CardTitle>
        <CardDescription className="text-xs">{description}</CardDescription>
      </CardHeader>
      <CardContent className="px-4 pb-4 pt-0">{children}</CardContent>
    </Card>
  )
}

export function Settings() {
  const { isLoading, error } = useSettings()

  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Settings</h1>
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">
              Failed to load settings. Please try again later.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Settings</h1>
        <div className="grid grid-cols-2 gap-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-2 pt-4 px-4">
                <Skeleton className="h-5 w-24" />
                <Skeleton className="h-3 w-32" />
              </CardHeader>
              <CardContent className="px-4 pb-4 pt-0">
                <Skeleton className="h-9 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Settings</h1>

      {/* Row 1: Scheduler + Interval */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <CompactCard title="Scheduler" description="Pause/resume scraping">
          <SchedulerControl />
        </CompactCard>
        <CompactCard title="Interval" description="Scrape frequency">
          <IntervalSelector />
        </CompactCard>
      </div>

      {/* Row 2: Platforms (full width) */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Platforms</CardTitle>
          <CardDescription className="text-xs">
            Enable or disable scraping for specific bookmakers
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-0">
          <PlatformToggles horizontal />
        </CardContent>
      </Card>

      {/* Row 3: Retention settings */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <CompactCard title="Odds Retention" description="Days to keep snapshots">
          <RetentionSelector field="oddsRetentionDays" />
        </CompactCard>
        <CompactCard
          title="Match Retention"
          description="Days to keep matches"
        >
          <RetentionSelector field="matchRetentionDays" />
        </CompactCard>
      </div>

      {/* Row 4: Cleanup + Manage */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <CompactCard title="Cleanup" description="Auto-cleanup frequency">
          <CleanupFrequencySelector />
        </CompactCard>
        <CompactCard title="Data" description="View and manage stored data">
          <ManageDataButton />
        </CompactCard>
      </div>
    </div>
  )
}
