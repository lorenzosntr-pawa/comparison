import { useState, useEffect, Component, type ReactNode } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { OddsLineChart } from './odds-line-chart'
import { MarginLineChart } from './margin-line-chart'
import { MarketHistoryPanel } from './market-history-panel'
import { useOddsHistory } from '../hooks/use-odds-history'
import { useMarginHistory } from '../hooks/use-margin-history'
import { useMultiOddsHistory } from '../hooks/use-multi-odds-history'
import { useMultiMarginHistory } from '../hooks/use-multi-margin-history'

// Error boundary to catch chart rendering errors
interface ErrorBoundaryProps {
  children: ReactNode
  fallback: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

class ChartErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Chart rendering error:', error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback
    }
    return this.props.children
  }
}

export interface BookmakerInfo {
  slug: string
  name: string
}

export interface HistoryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  eventId: number
  marketId: string
  line?: number | null
  bookmakerSlug: string
  marketName: string
  bookmakerName: string
  // All available bookmakers for comparison mode
  allBookmakers?: BookmakerInfo[]
}

export function HistoryDialog({
  open,
  onOpenChange,
  eventId,
  marketId,
  line,
  bookmakerSlug,
  marketName,
  bookmakerName,
  allBookmakers,
}: HistoryDialogProps) {
  const [activeTab, setActiveTab] = useState<'odds' | 'margin'>('odds')
  const [comparisonMode, setComparisonMode] = useState(false)
  const [fullMarketView, setFullMarketView] = useState(false)
  const [selectedBookmakers, setSelectedBookmakers] = useState<string[]>([])

  // Reset state when dialog opens with new bookmaker
  useEffect(() => {
    if (open) {
      setSelectedBookmakers([bookmakerSlug])
      setComparisonMode(false)
      setFullMarketView(false)
    }
  }, [open, bookmakerSlug])

  // Reset fullMarketView when comparison mode is turned off
  useEffect(() => {
    if (!comparisonMode) {
      setFullMarketView(false)
    }
  }, [comparisonMode])

  // Get available bookmakers for comparison (default to standard set if not provided)
  const availableBookmakers = allBookmakers || [
    { slug: 'betpawa', name: 'BetPawa' },
    { slug: 'sportybet', name: 'SportyBet' },
    { slug: 'bet9ja', name: 'Bet9ja' },
  ]

  // Ensure clicked bookmaker is always in the list
  const bookmakersToShow = availableBookmakers.some((b) => b.slug === bookmakerSlug)
    ? availableBookmakers
    : [{ slug: bookmakerSlug, name: bookmakerName }, ...availableBookmakers]

  // Single bookmaker hooks (non-comparison mode)
  const oddsHistory = useOddsHistory({
    eventId,
    marketId,
    bookmakerSlug,
    line,
    enabled: open && activeTab === 'odds' && !comparisonMode,
  })

  const marginHistory = useMarginHistory({
    eventId,
    marketId,
    bookmakerSlug,
    line,
    enabled: open && activeTab === 'margin' && !comparisonMode,
  })

  // Multi-bookmaker hooks (comparison mode)
  const multiOddsHistory = useMultiOddsHistory({
    eventId,
    marketId,
    bookmakerSlugs: selectedBookmakers,
    line,
    enabled: open && activeTab === 'odds' && comparisonMode && selectedBookmakers.length > 0,
  })

  const multiMarginHistory = useMultiMarginHistory({
    eventId,
    marketId,
    bookmakerSlugs: selectedBookmakers,
    line,
    enabled: open && activeTab === 'margin' && comparisonMode && selectedBookmakers.length > 0,
  })

  const handleBookmakerToggle = (slug: string, checked: boolean) => {
    if (checked) {
      setSelectedBookmakers((prev) => [...prev, slug])
    } else {
      // Don't allow deselecting all bookmakers
      if (selectedBookmakers.length > 1) {
        setSelectedBookmakers((prev) => prev.filter((s) => s !== slug))
      }
    }
  }

  // Include line value in market display name when present
  const marketDisplayName = line != null
    ? `${marketName} ${line}`
    : marketName

  const dialogTitle = comparisonMode
    ? fullMarketView
      ? `${marketDisplayName} - Full Market View`
      : `${marketDisplayName} - Compare Bookmakers`
    : `${marketDisplayName} - ${bookmakerName}`

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>{dialogTitle}</DialogTitle>
        </DialogHeader>

        {/* Comparison Mode Toggle */}
        {bookmakersToShow.length > 1 && (
          <div className="flex flex-col gap-3 pb-2 border-b">
            <div className="flex items-center gap-3">
              <Switch
                id="comparison-mode"
                checked={comparisonMode}
                onCheckedChange={setComparisonMode}
              />
              <Label htmlFor="comparison-mode" className="text-sm">
                Compare bookmakers
              </Label>
            </div>

            {/* Bookmaker Selection (visible in comparison mode) */}
            {comparisonMode && (
              <div className="space-y-3">
                <div className="flex flex-wrap gap-3">
                  {bookmakersToShow.map((bm) => (
                    <div key={bm.slug} className="flex items-center gap-2">
                      <Checkbox
                        id={`bm-${bm.slug}`}
                        checked={selectedBookmakers.includes(bm.slug)}
                        onCheckedChange={(checked) =>
                          handleBookmakerToggle(bm.slug, checked as boolean)
                        }
                      />
                      <Label htmlFor={`bm-${bm.slug}`} className="text-sm">
                        {bm.name}
                      </Label>
                    </div>
                  ))}
                </div>

                {/* Full Market View toggle */}
                <div className="flex items-center gap-3 pt-2 border-t">
                  <Switch
                    id="full-market-view"
                    checked={fullMarketView}
                    onCheckedChange={setFullMarketView}
                  />
                  <Label htmlFor="full-market-view" className="text-sm">
                    Show all outcomes
                  </Label>
                </div>
              </div>
            )}
          </div>
        )}

        <Tabs
          value={activeTab}
          onValueChange={(value) => setActiveTab(value as 'odds' | 'margin')}
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="odds">Odds</TabsTrigger>
            <TabsTrigger value="margin">Margin</TabsTrigger>
          </TabsList>

          <TabsContent value="odds" className="mt-4">
            {comparisonMode ? (
              // Comparison mode - multi-bookmaker chart
              multiOddsHistory.isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-[300px] w-full" />
                </div>
              ) : multiOddsHistory.isError ? (
                <div className="flex flex-col items-center justify-center h-[300px] gap-4">
                  <p className="text-destructive">Failed to load odds history</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => multiOddsHistory.refetch()}
                  >
                    Retry
                  </Button>
                </div>
              ) : fullMarketView ? (
                // Full Market View - small-multiples layout
                <ChartErrorBoundary
                  fallback={
                    <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                      Unable to render charts
                    </div>
                  }
                >
                  <MarketHistoryPanel multiData={multiOddsHistory.data} />
                </ChartErrorBoundary>
              ) : (
                <ChartErrorBoundary
                  fallback={
                    <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                      Unable to render chart
                    </div>
                  }
                >
                  <OddsLineChart
                    multiData={multiOddsHistory.data}
                    comparisonMode={true}
                  />
                </ChartErrorBoundary>
              )
            ) : (
              // Single bookmaker mode
              oddsHistory.isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-[300px] w-full" />
                </div>
              ) : oddsHistory.error ? (
                <div className="flex flex-col items-center justify-center h-[300px] gap-4">
                  <p className="text-destructive">
                    Failed to load odds history
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => oddsHistory.refetch()}
                  >
                    Retry
                  </Button>
                </div>
              ) : (
                <ChartErrorBoundary
                  fallback={
                    <div className="flex items-center justify-center h-[300px] text-muted-foreground">
                      Unable to render chart
                    </div>
                  }
                >
                  <OddsLineChart
                    data={oddsHistory.data?.history ?? []}
                    showMargin={false}
                  />
                </ChartErrorBoundary>
              )
            )}
          </TabsContent>

          <TabsContent value="margin" className="mt-4">
            {comparisonMode ? (
              // Comparison mode - multi-bookmaker chart
              multiMarginHistory.isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-[200px] w-full" />
                </div>
              ) : multiMarginHistory.isError ? (
                <div className="flex flex-col items-center justify-center h-[200px] gap-4">
                  <p className="text-destructive">Failed to load margin history</p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => multiMarginHistory.refetch()}
                  >
                    Retry
                  </Button>
                </div>
              ) : (
                <ChartErrorBoundary
                  fallback={
                    <div className="flex items-center justify-center h-[200px] text-muted-foreground">
                      Unable to render chart
                    </div>
                  }
                >
                  <MarginLineChart
                    multiData={multiMarginHistory.data}
                    comparisonMode={true}
                  />
                </ChartErrorBoundary>
              )
            ) : (
              // Single bookmaker mode
              marginHistory.isLoading ? (
                <div className="space-y-2">
                  <Skeleton className="h-[200px] w-full" />
                </div>
              ) : marginHistory.error ? (
                <div className="flex flex-col items-center justify-center h-[200px] gap-4">
                  <p className="text-destructive">
                    Failed to load margin history
                  </p>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => marginHistory.refetch()}
                  >
                    Retry
                  </Button>
                </div>
              ) : (
                <ChartErrorBoundary
                  fallback={
                    <div className="flex items-center justify-center h-[200px] text-muted-foreground">
                      Unable to render chart
                    </div>
                  }
                >
                  <MarginLineChart data={marginHistory.data?.history ?? []} />
                </ChartErrorBoundary>
              )
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
