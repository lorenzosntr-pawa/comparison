import { useState } from 'react'
import {
  StatsSummary,
  RunsTable,
  DurationTrendChart,
  SuccessRateChart,
  PlatformHealthChart,
} from './components'
import { useAnalytics } from './hooks'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

export { ScrapeRunDetailPage } from './detail'

type PeriodOption = '7' | '14' | '30'

export function ScrapeRunsPage() {
  const [period, setPeriod] = useState<PeriodOption>('14')
  const { data: analytics, isPending: isAnalyticsLoading } = useAnalytics({
    days: parseInt(period, 10),
  })

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Scrape Runs</h1>
        <p className="text-muted-foreground">
          Scraping history and performance
        </p>
      </div>

      <StatsSummary />

      {/* Analytics Section */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-medium">Analytics</h2>
          <Select value={period} onValueChange={(v) => setPeriod(v as PeriodOption)}>
            <SelectTrigger className="w-[120px]">
              <SelectValue placeholder="Period" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="14">Last 14 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="grid gap-3 md:grid-cols-3">
          <DurationTrendChart
            data={analytics?.daily_metrics ?? []}
            isLoading={isAnalyticsLoading}
          />
          <SuccessRateChart
            data={analytics?.daily_metrics ?? []}
            isLoading={isAnalyticsLoading}
          />
          <PlatformHealthChart
            data={analytics?.platform_metrics ?? []}
            isLoading={isAnalyticsLoading}
          />
        </div>
      </div>

      <RunsTable />
    </div>
  )
}
