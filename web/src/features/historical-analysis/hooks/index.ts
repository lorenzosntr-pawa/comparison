// Barrel export for historical-analysis hooks
export {
  useTournaments,
  TRACKED_MARKETS,
  type TournamentWithCount,
  type MarginMetrics,
} from './use-tournaments'

export {
  useTournamentMarkets,
  type TournamentMarket,
  type TournamentInfo,
  type MarginHistoryPoint as TournamentMarginHistoryPoint,
  type MarketMarginStats,
} from './use-tournament-markets'
