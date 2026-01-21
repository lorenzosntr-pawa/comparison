import { Routes, Route } from 'react-router'
import { Dashboard } from '@/features/dashboard'
import { MatchList, MatchDetail } from '@/features/matches'
import { ScrapeRunsPage, ScrapeRunDetailPage } from '@/features/scrape-runs'
import { Settings } from '@/features/settings'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/matches" element={<MatchList />} />
      <Route path="/matches/:id" element={<MatchDetail />} />
      <Route path="/scrape-runs" element={<ScrapeRunsPage />} />
      <Route path="/scrape-runs/:id" element={<ScrapeRunDetailPage />} />
      <Route path="/settings" element={<Settings />} />
    </Routes>
  )
}
