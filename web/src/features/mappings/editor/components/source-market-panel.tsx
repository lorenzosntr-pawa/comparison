import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { UnmappedMarketDetail } from '../hooks/use-unmapped-detail'

/**
 * Get source badge styling based on platform.
 */
function getSourceBadge(source: string): { label: string; className: string } {
  switch (source) {
    case 'sportybet':
      return {
        label: 'SportyBet',
        className: 'bg-blue-100 text-blue-800 hover:bg-blue-200',
      }
    case 'bet9ja':
      return {
        label: 'Bet9ja',
        className: 'bg-green-100 text-green-800 hover:bg-green-200',
      }
    default:
      return {
        label: source,
        className: 'bg-gray-100 text-gray-800 hover:bg-gray-200',
      }
  }
}

interface SourceMarketPanelProps {
  /** Unmapped market detail data */
  data: UnmappedMarketDetail
}

/**
 * Source Market Panel component.
 *
 * Displays source market details including:
 * - Platform badge (SportyBet/Bet9ja)
 * - Market name
 * - External market ID
 * - Occurrence count
 * - Sample outcomes (JSON display)
 */
export function SourceMarketPanel({ data }: SourceMarketPanelProps) {
  const source = getSourceBadge(data.source)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base flex items-center gap-2">
          Source Market
          <Badge className={source.className} variant="secondary">
            {source.label}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Market Name */}
        <div>
          <p className="text-sm font-medium text-muted-foreground">Market Name</p>
          <p className="text-sm">{data.marketName || '(No name available)'}</p>
        </div>

        {/* External ID */}
        <div>
          <p className="text-sm font-medium text-muted-foreground">External Market ID</p>
          <p className="text-sm font-mono">{data.externalMarketId}</p>
        </div>

        {/* Occurrence Count */}
        <div>
          <p className="text-sm font-medium text-muted-foreground">Occurrences</p>
          <p className="text-sm">{data.occurrenceCount} times</p>
        </div>

        {/* Sample Outcomes */}
        {data.sampleOutcomes && data.sampleOutcomes.length > 0 && (
          <div>
            <p className="text-sm font-medium text-muted-foreground mb-2">Sample Outcomes</p>
            <pre className="text-xs bg-muted p-3 rounded-md overflow-auto max-h-48">
              {JSON.stringify(data.sampleOutcomes, null, 2)}
            </pre>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
