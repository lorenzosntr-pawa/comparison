/**
 * Tournament detail page showing market statistics and margin timeline.
 *
 * @module tournament-detail
 */

import { useParams } from 'react-router'

/**
 * Tournament detail page - displays market cards with margin stats
 * and interactive timeline charts.
 */
export function TournamentDetailPage() {
  const { tournamentId } = useParams<{ tournamentId: string }>()

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Tournament Details</h1>
      <p>Tournament ID: {tournamentId}</p>
    </div>
  )
}
