/**
 * Dialog for displaying market margin timeline with time-to-kickoff visualization.
 *
 * @module timeline-dialog
 * @description Shows summary stats (opening/closing margin with delta),
 * bucket breakdown table, and TimeToKickoffChart.
 */

import { useState, useMemo } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { TimeToKickoffChart } from './time-to-kickoff-chart'
import type { TournamentMarket, BucketStats } from '../hooks/use-tournament-markets'

/**
 * Props for TimelineDialog component.
 */
export interface TimelineDialogProps {
  /** Whether the dialog is open */
  open: boolean
  /** Callback when open state changes */
  onOpenChange: (open: boolean) => void
  /** Single market to display (for card-level access) */
  market: TournamentMarket | null
  /** Tournament name for dialog title context */
  tournamentName: string
  /** All markets for multi-market mode (page-level access) */
  allMarkets?: TournamentMarket[]
}

/**
 * Format a bucket label for display.
 */
function formatBucketLabel(bucket: string): string {
  switch (bucket) {
    case '7d+':
      return '7+ days'
    case '3-7d':
      return '3-7 days'
    case '24-72h':
      return '24-72 hours'
    case '<24h':
      return '< 24 hours'
    default:
      return bucket
  }
}

/**
 * Find the bucket with the largest margin change.
 */
function findLargestChangeBucket(stats: BucketStats[]): string | null {
  if (stats.length < 2) return null

  let maxChange = 0
  let maxBucket: string | null = null

  for (let i = 1; i < stats.length; i++) {
    const change = Math.abs(stats[i].avgMargin - stats[i - 1].avgMargin)
    if (change > maxChange) {
      maxChange = change
      maxBucket = stats[i].bucket
    }
  }

  return maxBucket
}

/**
 * Summary stats component showing opening/closing margin with delta.
 */
function SummaryStats({ market }: { market: TournamentMarket }) {
  const deltaColor =
    market.marginDelta < 0
      ? 'text-green-600' // Margin improved (decreased)
      : market.marginDelta > 0
        ? 'text-red-600' // Margin worsened (increased)
        : 'text-muted-foreground'

  const deltaSign = market.marginDelta > 0 ? '+' : ''

  return (
    <div className="flex items-center gap-2 text-sm bg-muted/50 rounded-md p-3">
      <span className="text-muted-foreground">Opening:</span>
      <span className="font-medium">{market.openingMargin.toFixed(1)}%</span>
      <span className="text-muted-foreground mx-1">→</span>
      <span className="text-muted-foreground">Closing:</span>
      <span className="font-medium">{market.closingMargin.toFixed(1)}%</span>
      <span className={`font-medium ${deltaColor} ml-2`}>
        (Δ {deltaSign}{market.marginDelta.toFixed(1)}%)
      </span>
    </div>
  )
}

/**
 * Bucket breakdown table showing per-time-bucket statistics.
 */
function BucketBreakdownTable({ stats }: { stats: BucketStats[] }) {
  const largestChangeBucket = useMemo(() => findLargestChangeBucket(stats), [stats])

  if (stats.length === 0) {
    return (
      <div className="text-sm text-muted-foreground text-center py-4">
        No bucket data available
      </div>
    )
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Time Bucket</TableHead>
          <TableHead className="text-right">Avg Margin</TableHead>
          <TableHead className="text-right">Points</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {stats.map((stat) => {
          const isHighlighted = stat.bucket === largestChangeBucket
          return (
            <TableRow
              key={stat.bucket}
              className={isHighlighted ? 'bg-amber-50 dark:bg-amber-950/30' : ''}
            >
              <TableCell className="font-medium">
                {formatBucketLabel(stat.bucket)}
              </TableCell>
              <TableCell className="text-right">
                {stat.avgMargin.toFixed(1)}%
              </TableCell>
              <TableCell className="text-right">{stat.pointCount}</TableCell>
            </TableRow>
          )
        })}
      </TableBody>
    </Table>
  )
}

/**
 * Get display name for a market including line value if present.
 */
function getMarketDisplayName(market: TournamentMarket): string {
  return market.line !== null ? `${market.name} ${market.line}` : market.name
}

/**
 * Dialog component for displaying market margin timeline with time-to-kickoff chart.
 *
 * Supports two modes:
 * - Single market mode: Display one market (when opened from card button)
 * - Multi-market mode: Dropdown to switch between markets (when opened from page button)
 */
export function TimelineDialog({
  open,
  onOpenChange,
  market,
  tournamentName,
  allMarkets,
}: TimelineDialogProps) {
  // For multi-market mode, track selected market
  const [selectedMarketKey, setSelectedMarketKey] = useState<string | null>(null)

  // Determine effective market to display
  const effectiveMarket = useMemo(() => {
    // Multi-market mode
    if (allMarkets && allMarkets.length > 0) {
      if (selectedMarketKey) {
        const found = allMarkets.find(
          (m) => `${m.id}:${m.line ?? 'null'}` === selectedMarketKey
        )
        if (found) return found
      }
      // Default to first market
      return allMarkets[0]
    }
    // Single market mode
    return market
  }, [market, allMarkets, selectedMarketKey])

  // Reset selection when dialog opens
  const handleOpenChange = (newOpen: boolean) => {
    if (newOpen) {
      setSelectedMarketKey(null)
    }
    onOpenChange(newOpen)
  }

  // Build dialog title
  const isMultiMarketMode = allMarkets && allMarkets.length > 0
  const dialogTitle = isMultiMarketMode
    ? `${tournamentName} - Margin Timeline`
    : effectiveMarket
      ? `${getMarketDisplayName(effectiveMarket)} - Timeline`
      : 'Margin Timeline'

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{dialogTitle}</DialogTitle>
        </DialogHeader>

        {/* Multi-market mode: market selector */}
        {isMultiMarketMode && allMarkets && (
          <div className="mb-4">
            <Select
              value={selectedMarketKey ?? `${allMarkets[0].id}:${allMarkets[0].line ?? 'null'}`}
              onValueChange={setSelectedMarketKey}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select market" />
              </SelectTrigger>
              <SelectContent>
                {allMarkets.map((m) => {
                  const key = `${m.id}:${m.line ?? 'null'}`
                  return (
                    <SelectItem key={key} value={key}>
                      {getMarketDisplayName(m)} ({m.eventCount} events)
                    </SelectItem>
                  )
                })}
              </SelectContent>
            </Select>
          </div>
        )}

        {effectiveMarket ? (
          <div className="space-y-4">
            {/* Summary stats */}
            <SummaryStats market={effectiveMarket} />

            {/* Bucket breakdown table */}
            <div className="border rounded-md">
              <BucketBreakdownTable stats={effectiveMarket.bucketStats} />
            </div>

            {/* Time-to-kickoff chart */}
            <div className="border rounded-md p-4">
              <h3 className="text-sm font-medium mb-3 text-muted-foreground">
                Margin Over Time (Hours to Kickoff)
              </h3>
              <TimeToKickoffChart
                data={effectiveMarket.timeToKickoffHistory}
                height={300}
                showBucketZones={true}
              />
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-48 text-muted-foreground">
            No market data available
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
