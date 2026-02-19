import { Routes, Route } from 'react-router'
import { MatchList, MatchDetail } from '@/features/matches'
import { CoveragePage } from '@/features/coverage'
import { HistoricalAnalysisPage, TournamentDetailPage } from '@/features/historical-analysis'
import { ScrapeRunsPage, ScrapeRunDetailPage } from '@/features/scrape-runs'
import { RiskMonitoringPage } from '@/features/risk-monitoring'
import { Settings } from '@/features/settings'
import { StoragePage } from '@/features/storage'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<MatchList />} />
      <Route path="/odds-comparison/:id" element={<MatchDetail />} />
      <Route path="/coverage" element={<CoveragePage />} />
      <Route path="/historical-analysis" element={<HistoricalAnalysisPage />} />
      <Route path="/historical-analysis/:tournamentId" element={<TournamentDetailPage />} />
      <Route path="/scrape-runs" element={<ScrapeRunsPage />} />
      <Route path="/scrape-runs/:id" element={<ScrapeRunDetailPage />} />
      <Route path="/risk-monitoring" element={<RiskMonitoringPage />} />
      <Route path="/settings" element={<Settings />} />
      <Route path="/storage" element={<StoragePage />} />
    </Routes>
  )
}
