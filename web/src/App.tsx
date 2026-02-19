import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { BrowserRouter } from 'react-router'
import { ThemeProvider } from '@/components/theme-provider'
import { AppLayout } from '@/components/layout'
import { AppRoutes } from '@/routes'
import { useOddsUpdates } from '@/hooks'
import { useRiskAlertUpdates } from '@/features/risk-monitoring/hooks'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,  // 5 minutes
      gcTime: 1000 * 60 * 10,    // 10 minutes (NOT cacheTime - v5 renamed it)
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

/**
 * Inner app component that has access to QueryClient context.
 * Enables hooks that depend on React Query (like useOddsUpdates).
 */
function AppContent() {
  // Subscribe to real-time odds updates via WebSocket
  // Hook's side effect automatically invalidates queries on updates
  useOddsUpdates()
  // Subscribe to real-time risk alerts via WebSocket
  useRiskAlertUpdates()

  return (
    <BrowserRouter>
      <ThemeProvider defaultTheme="system" storageKey="betpawa-ui-theme">
        <AppLayout>
          <AppRoutes />
        </AppLayout>
      </ThemeProvider>
    </BrowserRouter>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
