import { Routes, Route } from 'react-router'
import { Dashboard } from '@/features/dashboard'
import { MatchList, MatchDetail } from '@/features/matches'
import { CoveragePage } from '@/features/coverage'
import { HistoricalAnalysisPage, TournamentDetailPage } from '@/features/historical-analysis'
import { ScrapeRunsPage, ScrapeRunDetailPage } from '@/features/scrape-runs'
import { Settings } from '@/features/settings'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/odds-comparison" element={<MatchList />} />
      <Route path="/odds-comparison/:id" element={<MatchDetail />} />
      <Route path="/coverage" element={<CoveragePage />} />
      <Route path="/historical-analysis" element={<HistoricalAnalysisPage />} />
      <Route path="/historical-analysis/:tournamentId" element={<TournamentDetailPage />} />
      <Route path="/scrape-runs" element={<ScrapeRunsPage />} />
      <Route path="/scrape-runs/:id" element={<ScrapeRunDetailPage />} />
      <Route path="/settings" element={<Settings />} />
    </Routes>
  )
}
