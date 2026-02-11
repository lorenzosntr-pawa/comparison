/**
 * Tournament detail page showing market statistics and margin timeline dialog.
 *
 * @module tournament-detail
 */

import { useState, useMemo } from 'react'
import { useParams, Link } from 'react-router'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { ArrowLeft, LineChart } from 'lucide-react'
import { useTournamentMarkets, type TournamentMarket } from './hooks'
import { TRACKED_MARKETS } from './hooks/use-tournaments'
import { TimelineDialog } from './components'

/**
 * Fuzzy subsequence matching - query chars appear in target in order.
 */
function fuzzyMatch(query: string, target: string): boolean {
  if (!query) return true

  const normalizedQuery = query.toLowerCase().replace(/\s/g, '')
  const normalizedTarget = target.toLowerCase().replace(/\s/g, '')

  let queryIndex = 0
  for (let i = 0; i < normalizedTarget.length && queryIndex < normalizedQuery.length; i++) {
    if (normalizedTarget[i] === normalizedQuery[queryIndex]) {
      queryIndex++
    }
  }

  return queryIndex === normalizedQuery.length
}

/** Set of tracked market IDs for quick lookup */
const TRACKED_MARKET_IDS: Set<string> = new Set(TRACKED_MARKETS.map((m) => m.id))

/**
 * Check if a market is one of the tracked main markets.
 */
function isTrackedMarket(marketId: string): boolean {
  return TRACKED_MARKET_IDS.has(marketId)
}

/**
 * Market card displaying margin statistics.
 * Shows opening/closing delta for tracked markets.
 */
function MarketCard({
  market,
  onTimelineClick,
}: {
  market: TournamentMarket
  onTimelineClick: () => void
}) {
  const displayName = market.line !== null
    ? `${market.name} ${market.line}`
    : market.name

  const isTracked = isTrackedMarket(market.id)

  // Delta styling
  const deltaColor =
    market.marginDelta < 0
      ? 'text-green-600' // Margin improved (decreased)
      : market.marginDelta > 0
        ? 'text-red-600' // Margin worsened (increased)
        : 'text-muted-foreground'
  const deltaSign = market.marginDelta > 0 ? '+' : ''

  return (
    <Card className="hover:bg-muted/30 transition-colors">
      <CardContent className="p-4">
        <h3 className="font-medium truncate mb-2">{displayName}</h3>

        <div className="space-y-1 text-sm">
          {/* Show opening/closing for tracked markets */}
          {isTracked && (
            <div className="flex items-center gap-1 text-xs pb-1 border-b mb-1">
              <span className="text-muted-foreground">Opening:</span>
              <span>{market.openingMargin.toFixed(1)}%</span>
              <span className="text-muted-foreground mx-0.5">→</span>
              <span>{market.closingMargin.toFixed(1)}%</span>
              <span className={`${deltaColor} ml-1`}>
                ({deltaSign}{market.marginDelta.toFixed(1)}%)
              </span>
            </div>
          )}

          <div className="flex justify-between">
            <span className="text-muted-foreground">Avg margin:</span>
            <span className="font-medium">{market.avgMargin.toFixed(1)}%</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Range:</span>
            <span>
              {market.minMargin.toFixed(1)}% - {market.maxMargin.toFixed(1)}%
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">Events:</span>
            <span>{market.eventCount}</span>
          </div>
        </div>

        {/* Timeline button */}
        <Button
          variant="ghost"
          size="sm"
          className="w-full mt-3 text-xs"
          onClick={(e) => {
            e.stopPropagation()
            onTimelineClick()
          }}
        >
          <LineChart className="h-3 w-3 mr-1" />
          Timeline
        </Button>
      </CardContent>
    </Card>
  )
}

/**
 * Skeleton card for loading state.
 */
function SkeletonCard() {
  return (
    <Card>
      <CardContent className="p-4">
        <Skeleton className="h-5 w-3/4 mb-2" />
        <div className="space-y-1">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-1/2" />
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * Tournament detail page - displays market cards with margin stats
 * and timeline dialog for detailed time-to-kickoff analysis.
 */
export function TournamentDetailPage() {
  const { tournamentId } = useParams<{ tournamentId: string }>()
  const parsedId = tournamentId ? parseInt(tournamentId, 10) : 0

  const { data, isPending, error } = useTournamentMarkets(parsedId)
  const [searchQuery, setSearchQuery] = useState('')

  // Timeline dialog state
  const [timelineOpen, setTimelineOpen] = useState(false)
  const [timelineMarket, setTimelineMarket] = useState<TournamentMarket | null>(null)
  const [isMultiMarketMode, setIsMultiMarketMode] = useState(false)

  // Filter markets by search query
  const filteredMarkets = useMemo(() => {
    if (!data?.markets) return []

    return data.markets.filter((market) => {
      const searchTarget = market.line !== null
        ? `${market.name} ${market.line}`
        : market.name
      return fuzzyMatch(searchQuery, searchTarget)
    })
  }, [data?.markets, searchQuery])

  // Open dialog for single market
  const handleMarketTimelineClick = (market: TournamentMarket) => {
    setTimelineMarket(market)
    setIsMultiMarketMode(false)
    setTimelineOpen(true)
  }

  // Open dialog for all markets
  const handleViewAllTimelines = () => {
    setTimelineMarket(null)
    setIsMultiMarketMode(true)
    setTimelineOpen(true)
  }

  // Loading state
  if (isPending) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <Link to="/historical-analysis">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
          </Link>
          <Skeleton className="h-8 w-64" />
        </div>

        <Skeleton className="h-10 w-full max-w-sm" />

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <Link to="/historical-analysis">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
          </Link>
        </div>

        <div className="p-4 text-red-500 bg-red-50 rounded-md">
          Failed to load tournament data: {error.message}
        </div>
      </div>
    )
  }

  // Empty/not found state
  if (!data?.tournament) {
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <Link to="/historical-analysis">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
          </Link>
        </div>

        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground">
              No tournament data found
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const { tournament, markets } = data

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link to="/historical-analysis">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4 mr-1" />
              Back
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">{tournament.name}</h1>
            <p className="text-muted-foreground">
              {tournament.country || 'International'} — {tournament.eventCount} event{tournament.eventCount !== 1 ? 's' : ''}
            </p>
          </div>
        </div>

        {/* Page-level timeline button */}
        {markets.length > 0 && (
          <Button variant="outline" onClick={handleViewAllTimelines}>
            <LineChart className="h-4 w-4 mr-2" />
            View All Timelines
          </Button>
        )}
      </div>

      {/* Search filter */}
      <div className="max-w-sm">
        <Input
          placeholder="Search markets..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Empty markets state */}
      {markets.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground">
              No market data found for this tournament
            </p>
          </CardContent>
        </Card>
      )}

      {/* Market cards grid */}
      {filteredMarkets.length > 0 && (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredMarkets.map((market) => {
            const key = market.line !== null
              ? `${market.id}:${market.line}`
              : market.id

            return (
              <MarketCard
                key={key}
                market={market}
                onTimelineClick={() => handleMarketTimelineClick(market)}
              />
            )
          })}
        </div>
      )}

      {/* No search results */}
      {markets.length > 0 && filteredMarkets.length === 0 && (
        <Card>
          <CardContent className="p-8 text-center">
            <p className="text-muted-foreground">
              No markets match "{searchQuery}"
            </p>
          </CardContent>
        </Card>
      )}

      {/* Timeline Dialog */}
      <TimelineDialog
        open={timelineOpen}
        onOpenChange={setTimelineOpen}
        market={timelineMarket}
        tournamentName={tournament.name}
        allMarkets={isMultiMarketMode ? markets : undefined}
      />
    </div>
  )
}
