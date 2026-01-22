import { StatsCards, RecentRuns, StatusBar } from './components'

export function Dashboard() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          System status and scraping overview
        </p>
      </div>

      {/* Top row: Quick Stats */}
      <StatsCards />

      {/* Middle section: Recent Scrape Runs (with integrated scheduler controls) */}
      <RecentRuns />

      {/* Bottom row: Compact Status Bar */}
      <StatusBar />
    </div>
  )
}
