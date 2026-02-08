import { useState, useMemo, useEffect, useRef } from 'react'
import { ArrowUp } from 'lucide-react'
import type { BookmakerMarketData, MarketOddsDetail } from '@/types/api'
import { MarketRow } from './market-row'
import { MarketFilterBar } from './market-filter-bar'
import { HistoryDialog, type BookmakerInfo } from './history-dialog'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { mergeMarketOutcomes } from '../lib/market-utils'

// Bookmaker slugs in display order
const BOOKMAKER_ORDER = ['betpawa', 'sportybet', 'bet9ja']
const BOOKMAKER_NAMES: Record<string, string> = {
  betpawa: 'Betpawa',
  sportybet: 'SportyBet',
  bet9ja: 'Bet9ja',
}

// Tab display order and names - includes all BetPawa market group categories
const TAB_ORDER = ['all', 'popular', 'goals', 'handicaps', 'combos', 'halves', 'corners', 'cards', 'specials', 'other']
const TAB_NAMES: Record<string, string> = {
  all: 'All',
  popular: 'Popular',
  goals: 'Goals',
  handicaps: 'Handicaps',
  combos: 'Combos',
  halves: 'Halves',
  corners: 'Corners',
  cards: 'Cards',
  specials: 'Specials',
  other: 'Other',
}

interface MarketGridProps {
  marketsByBookmaker: BookmakerMarketData[]
  eventId: number
}

interface HistoryDialogState {
  eventId: number
  marketId: string
  bookmakerSlug: string
  marketName: string
  bookmakerName: string
  allBookmakers: BookmakerInfo[]
}

interface UnifiedMarket {
  id: string
  name: string
  line: number | null
  marketGroups: string[]
  bookmakerMarkets: Map<string, MarketOddsDetail | null>
}

/**
 * Build a unified list of markets from all bookmakers.
 * Uses Betpawa as the reference taxonomy.
 */
function buildUnifiedMarkets(
  marketsByBookmaker: BookmakerMarketData[]
): UnifiedMarket[] {
  // Create a map of bookmaker slug -> markets by market key
  // Markets with the same key have their outcomes merged
  const bookmakerMaps = new Map<string, Map<string, MarketOddsDetail>>()

  for (const bookmakerData of marketsByBookmaker) {
    const marketMap = new Map<string, MarketOddsDetail>()
    for (const market of bookmakerData.markets) {
      // Create a unique key for each market (id + line)
      const key =
        market.line !== null
          ? `${market.betpawa_market_id}_${market.line}`
          : market.betpawa_market_id

      // Merge outcomes if market already exists (same id+line)
      const existing = marketMap.get(key)
      if (existing) {
        marketMap.set(key, mergeMarketOutcomes(existing, market))
      } else {
        marketMap.set(key, market)
      }
    }
    bookmakerMaps.set(bookmakerData.bookmaker_slug, marketMap)
  }

  // Collect all unique market keys across all bookmakers
  const allMarketKeys = new Set<string>()
  for (const [, marketMap] of bookmakerMaps) {
    for (const key of marketMap.keys()) {
      allMarketKeys.add(key)
    }
  }

  const unifiedMarkets: UnifiedMarket[] = []

  // First add Betpawa markets (they define the reference)
  // Use the deduplicated map instead of raw markets to avoid duplicate rows
  const betpawaMap = bookmakerMaps.get('betpawa')
  if (betpawaMap) {
    for (const [key, market] of betpawaMap) {
      const bookmakerMarkets = new Map<string, MarketOddsDetail | null>()
      for (const slug of BOOKMAKER_ORDER) {
        const bMap = bookmakerMaps.get(slug)
        bookmakerMarkets.set(slug, bMap?.get(key) ?? null)
      }

      unifiedMarkets.push({
        id: market.betpawa_market_id,
        name: market.betpawa_market_name,
        line: market.line,
        marketGroups: market.market_groups ?? ['other'],
        bookmakerMarkets,
      })
      allMarketKeys.delete(key)
    }
  }

  // Add remaining markets from other bookmakers that Betpawa doesn't have
  for (const key of allMarketKeys) {
    // Find first bookmaker that has this market
    let referenceMarket: MarketOddsDetail | undefined
    for (const slug of BOOKMAKER_ORDER) {
      const bMap = bookmakerMaps.get(slug)
      referenceMarket = bMap?.get(key)
      if (referenceMarket) break
    }

    if (referenceMarket) {
      const bookmakerMarkets = new Map<string, MarketOddsDetail | null>()
      for (const slug of BOOKMAKER_ORDER) {
        const bMap = bookmakerMaps.get(slug)
        bookmakerMarkets.set(slug, bMap?.get(key) ?? null)
      }

      unifiedMarkets.push({
        id: referenceMarket.betpawa_market_id,
        name: referenceMarket.betpawa_market_name,
        line: referenceMarket.line,
        marketGroups: referenceMarket.market_groups ?? ['other'],
        bookmakerMarkets,
      })
    }
  }

  return unifiedMarkets
}

/**
 * Get unique market groups from unified markets and return them in display order.
 * Groups with no markets are excluded. Unknown groups appear before 'other'.
 */
function getAvailableGroups(markets: UnifiedMarket[]): string[] {
  const presentGroups = new Set<string>()
  markets.forEach((m) => m.marketGroups.forEach((g) => presentGroups.add(g)))

  // Include known tabs in order
  const knownTabs = TAB_ORDER.filter(
    (tab) => tab === 'all' || presentGroups.has(tab)
  )

  // Add any unknown groups alphabetically before 'other'
  const unknownTabs = [...presentGroups]
    .filter((g) => !TAB_ORDER.includes(g))
    .sort()

  const otherIndex = knownTabs.indexOf('other')
  if (otherIndex >= 0) {
    knownTabs.splice(otherIndex, 0, ...unknownTabs)
  } else {
    knownTabs.push(...unknownTabs)
  }

  return knownTabs
}

/**
 * Get bookmaker order based on selected competitor.
 * When a competitor is selected, places them second after Betpawa.
 */
function getBookmakerOrder(selectedCompetitor: string | null): string[] {
  if (!selectedCompetitor) {
    return BOOKMAKER_ORDER
  }

  // Betpawa always first, selected competitor second, rest follow
  const others = BOOKMAKER_ORDER.filter(
    (slug) => slug !== 'betpawa' && slug !== selectedCompetitor
  )
  return ['betpawa', selectedCompetitor, ...others]
}

/**
 * Fuzzy match function using subsequence matching.
 * Checks if all characters in query appear in target in order.
 * Example: "o25" matches "Over 2.5 Goals" because o-2-5 appear in order.
 */
function fuzzyMatch(query: string, target: string): boolean {
  if (!query) return true

  // Normalize both strings: lowercase and remove spaces
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

interface MarketTabsProps {
  availableGroups: string[]
  activeTab: string
  onTabChange: (tab: string) => void
  marketCounts: Map<string, number>
}

function MarketTabs({
  availableGroups,
  activeTab,
  onTabChange,
  marketCounts,
}: MarketTabsProps) {
  return (
    <div className="flex flex-wrap gap-1 mb-4 border-b pb-2">
      {availableGroups.map((group) => {
        const count = group === 'all'
          ? Array.from(marketCounts.values()).reduce((a, b) => a + b, 0)
          : marketCounts.get(group) ?? 0
        const isActive = activeTab === group

        return (
          <button
            key={group}
            onClick={() => onTabChange(group)}
            className={cn(
              'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
              isActive
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted hover:bg-muted/80 text-muted-foreground hover:text-foreground'
            )}
          >
            {TAB_NAMES[group] ?? group}
            <span className={cn(
              'ml-1.5 text-xs',
              isActive ? 'text-primary-foreground/70' : 'text-muted-foreground'
            )}>
              ({count})
            </span>
          </button>
        )
      })}
    </div>
  )
}

export function MarketGrid({ marketsByBookmaker, eventId }: MarketGridProps) {
  const [activeTab, setActiveTab] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCompetitor, setSelectedCompetitor] = useState<string | null>(null)
  const [showScrollTop, setShowScrollTop] = useState(false)
  const [isHeaderStuck, setIsHeaderStuck] = useState(false)
  const [historyDialog, setHistoryDialog] = useState<HistoryDialogState | null>(null)
  const headerRef = useRef<HTMLDivElement>(null)
  const placeholderRef = useRef<HTMLDivElement>(null)

  // Track scroll position for sticky header and scroll-to-top button
  // Note: The app layout uses overflow-auto on <main>, so we listen to that element
  // Use data-scroll-container attribute to target the correct (inner) main element
  useEffect(() => {
    const scrollContainer = document.querySelector('[data-scroll-container]')
    if (!scrollContainer || !headerRef.current) return

    const handleScroll = () => {
      setShowScrollTop(scrollContainer.scrollTop > 400)

      // Check if header should be stuck (fixed at top of scroll container)
      if (headerRef.current && placeholderRef.current) {
        const placeholderRect = placeholderRef.current.getBoundingClientRect()
        const scrollContainerRect = scrollContainer.getBoundingClientRect()
        // Header should stick when placeholder scrolls above scroll container top
        const shouldStick = placeholderRect.top < scrollContainerRect.top
        setIsHeaderStuck(shouldStick)
      }
    }
    scrollContainer.addEventListener('scroll', handleScroll, { passive: true })
    return () => scrollContainer.removeEventListener('scroll', handleScroll)
  }, [])

  const scrollToTop = () => {
    const scrollContainer = document.querySelector('[data-scroll-container]')
    scrollContainer?.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const unifiedMarkets = useMemo(
    () => buildUnifiedMarkets(marketsByBookmaker),
    [marketsByBookmaker]
  )

  const availableGroups = useMemo(
    () => getAvailableGroups(unifiedMarkets),
    [unifiedMarkets]
  )

  const marketCounts = useMemo(() => {
    const counts = new Map<string, number>()
    for (const market of unifiedMarkets) {
      // Count market in each of its groups
      for (const group of market.marketGroups) {
        counts.set(group, (counts.get(group) ?? 0) + 1)
      }
    }
    return counts
  }, [unifiedMarkets])

  const filteredMarkets = useMemo(() => {
    let markets = unifiedMarkets

    // Apply tab filter
    if (activeTab !== 'all') {
      markets = markets.filter((m) => m.marketGroups.includes(activeTab))
    }

    // Apply fuzzy search filter
    if (searchQuery) {
      markets = markets.filter((m) => {
        // Build searchable text from name and line
        const searchTarget = m.line !== null
          ? `${m.name} ${m.line}`
          : m.name
        return fuzzyMatch(searchQuery, searchTarget)
      })
    }

    return markets
  }, [unifiedMarkets, activeTab, searchQuery])

  const bookmakerOrder = useMemo(
    () => getBookmakerOrder(selectedCompetitor),
    [selectedCompetitor]
  )

  // Build all bookmakers list for comparison mode
  const allBookmakers = useMemo(() => {
    return marketsByBookmaker
      .filter((bm) => bm.markets.length > 0)
      .map((bm) => ({
        slug: bm.bookmaker_slug,
        name: BOOKMAKER_NAMES[bm.bookmaker_slug] ?? bm.bookmaker_slug,
      }))
  }, [marketsByBookmaker])

  // Handler for odds/margin clicks to open history dialog
  const handleHistoryClick = (bookmakerSlug: string, marketId: string, marketName: string) => {
    setHistoryDialog({
      eventId,
      marketId,
      bookmakerSlug,
      marketName,
      bookmakerName: BOOKMAKER_NAMES[bookmakerSlug] ?? bookmakerSlug,
      allBookmakers,
    })
  }

  if (unifiedMarkets.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        No market data available for this match.
      </div>
    )
  }

  // Get scroll container rect for fixed positioning
  const getScrollContainerRect = () => {
    const scrollContainer = document.querySelector('[data-scroll-container]')
    return scrollContainer?.getBoundingClientRect()
  }

  return (
    <div>
      {/* Placeholder to reserve space when header is fixed */}
      <div ref={placeholderRef}>
        {isHeaderStuck && headerRef.current && (
          <div style={{ height: headerRef.current.offsetHeight }} />
        )}
      </div>

      {/* Navigation header - becomes fixed when scrolled past */}
      <div
        ref={headerRef}
        className={cn(
          'bg-background pt-2 pb-3 border-b border-border z-20',
          isHeaderStuck ? 'fixed shadow-md' : ''
        )}
        style={isHeaderStuck ? {
          top: getScrollContainerRect()?.top ?? 0,
          left: getScrollContainerRect()?.left ?? 0,
          right: `calc(100% - ${(getScrollContainerRect()?.right ?? 0)}px)`,
          width: getScrollContainerRect()?.width ?? 'auto',
        } : undefined}
      >
        <h2 className="text-2xl font-semibold tracking-tight mb-3">All Markets</h2>
        <MarketTabs
          availableGroups={availableGroups}
          activeTab={activeTab}
          onTabChange={setActiveTab}
          marketCounts={marketCounts}
        />

        <MarketFilterBar
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          selectedCompetitor={selectedCompetitor}
          onCompetitorChange={setSelectedCompetitor}
        />
      </div>

      {/* Table inside Card for visual consistency */}
      <Card className={isHeaderStuck ? 'mt-4' : 'mt-4'}>
        <CardContent className="pt-6">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="border-b bg-muted/50">
                  <th className="py-3 px-4 text-left font-semibold">Market</th>
                  <th className="py-3 px-2 text-center font-semibold">Selection</th>
                  {bookmakerOrder.map((slug) => (
                    <th key={slug} className="py-3 px-2 text-center font-semibold">
                      {BOOKMAKER_NAMES[slug]}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredMarkets.map((market, index) => (
                  <MarketRow
                    key={`${market.id}_${market.line ?? 'null'}_${index}`}
                    marketName={market.name}
                    line={market.line}
                    bookmakerMarkets={market.bookmakerMarkets}
                    bookmakerOrder={bookmakerOrder}
                    eventId={eventId}
                    onOddsClick={handleHistoryClick}
                    onMarginClick={handleHistoryClick}
                  />
                ))}
              </tbody>
            </table>
          </div>

          {filteredMarkets.length === 0 && (
            <div className="text-center py-4 text-muted-foreground text-sm">
              {searchQuery && activeTab !== 'all'
                ? `No markets matching "${searchQuery}" in ${TAB_NAMES[activeTab] ?? activeTab}`
                : searchQuery
                  ? `No markets matching "${searchQuery}"`
                  : activeTab !== 'all'
                    ? `No markets in ${TAB_NAMES[activeTab] ?? activeTab}`
                    : 'No markets available'}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Scroll-to-top button - appears when scrolled down */}
      {showScrollTop && (
        <Button
          variant="outline"
          size="icon"
          className="fixed bottom-20 right-6 shadow-lg transition-opacity duration-200"
          onClick={scrollToTop}
          aria-label="Scroll to top"
        >
          <ArrowUp className="h-4 w-4" />
        </Button>
      )}

      {/* History Dialog */}
      {historyDialog && (
        <HistoryDialog
          open={true}
          onOpenChange={(open) => !open && setHistoryDialog(null)}
          eventId={historyDialog.eventId}
          marketId={historyDialog.marketId}
          bookmakerSlug={historyDialog.bookmakerSlug}
          marketName={historyDialog.marketName}
          bookmakerName={historyDialog.bookmakerName}
          allBookmakers={historyDialog.allBookmakers}
        />
      )}
    </div>
  )
}
