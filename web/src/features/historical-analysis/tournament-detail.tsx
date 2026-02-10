/**
 * Tournament detail page showing market statistics and margin timeline.
 *
 * @module tournament-detail
 */

import { useState, useMemo } from 'react'
import { useParams, Link } from 'react-router'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { ArrowLeft, X } from 'lucide-react'
import { useTournamentMarkets, type TournamentMarket } from './hooks'
import { MarginLineChart } from '@/features/matches/components/margin-line-chart'
import type { MarginHistoryPoint } from '@/types/api'

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

/**
 * Market card displaying margin statistics.
 */
function MarketCard({
  market,
  isSelected,
  onClick,
}: {
  market: TournamentMarket
  isSelected: boolean
  onClick: () => void
}) {
  const displayName = market.line !== null
    ? `${market.name} ${market.line}`
    : market.name

  return (
    <Card
      className={`cursor-pointer transition-colors hover:bg-muted/50 ${
        isSelected ? 'ring-2 ring-primary' : ''
      }`}
      onClick={onClick}
    >
      <CardContent className="p-4">
        <h3 className="font-medium truncate mb-2">{displayName}</h3>

        <div className="space-y-1 text-sm">
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
 * and interactive timeline charts.
 */
export function TournamentDetailPage() {
  const { tournamentId } = useParams<{ tournamentId: string }>()
  const parsedId = tournamentId ? parseInt(tournamentId, 10) : 0

  const { data, isPending, error } = useTournamentMarkets(parsedId)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedMarket, setSelectedMarket] = useState<TournamentMarket | null>(null)

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

  // Transform selected market's history to chart format
  const chartData = useMemo((): MarginHistoryPoint[] | undefined => {
    if (!selectedMarket?.marginHistory) return undefined

    return selectedMarket.marginHistory.map((point) => ({
      captured_at: point.capturedAt,
      margin: point.margin,
    }))
  }, [selectedMarket])

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
                isSelected={selectedMarket === market}
                onClick={() => setSelectedMarket(
                  selectedMarket === market ? null : market
                )}
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

      {/* Timeline chart section */}
      {selectedMarket && (
        <Card className="mt-6">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-medium">
                Margin Timeline:{' '}
                {selectedMarket.line !== null
                  ? `${selectedMarket.name} ${selectedMarket.line}`
                  : selectedMarket.name}
              </h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSelectedMarket(null)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <MarginLineChart data={chartData} height={300} />
          </CardContent>
        </Card>
      )}
    </div>
  )
}
