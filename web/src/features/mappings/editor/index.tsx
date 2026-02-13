import { useParams, Link } from 'react-router'
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { useUnmappedDetail } from './hooks/use-unmapped-detail'

/**
 * Get source badge styling.
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

/**
 * Mapping Editor page.
 *
 * Two-column layout:
 * - Left panel: Source market details (platform, name, external ID, occurrences, sample outcomes)
 * - Right panel: Placeholder for target mapping selection (future)
 */
export function MappingEditor() {
  const { unmappedId } = useParams<{ unmappedId: string }>()
  const id = unmappedId ? parseInt(unmappedId, 10) : undefined
  const { data, isLoading, error } = useUnmappedDetail(id)

  // Loading state
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <div className="space-y-4">
        <Link to="/mappings">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Mappings
          </Button>
        </Link>
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <span>Failed to load unmapped market: {error.message}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // No data state (shouldn't happen if no error, but handle it)
  if (!data) {
    return (
      <div className="space-y-4">
        <Link to="/mappings">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Mappings
          </Button>
        </Link>
        <Card>
          <CardContent className="pt-6">
            <p className="text-muted-foreground">Unmapped market not found</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const source = getSourceBadge(data.source)

  return (
    <div className="space-y-4">
      {/* Header with back link */}
      <div className="flex items-center justify-between">
        <Link to="/mappings">
          <Button variant="ghost" size="sm" className="gap-2">
            <ArrowLeft className="h-4 w-4" />
            Back to Mappings
          </Button>
        </Link>
        <h1 className="text-xl font-semibold">Mapping Editor</h1>
      </div>

      {/* Two-column layout */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Left Panel: Source Market Details */}
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

        {/* Right Panel: Target Mapping (Placeholder) */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Target Market</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-center h-48 text-muted-foreground">
              <p className="text-sm">Target market selection coming soon...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
