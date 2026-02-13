import { useNavigate } from 'react-router'
import { AlertTriangle, CheckCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useHighPriorityUnmapped } from '../hooks/use-high-priority-unmapped'
import type { HighPriorityItem } from '../hooks/use-high-priority-unmapped'

/**
 * Get priority badge styling based on score.
 * - 100+: red (Critical)
 * - 50-99: orange (High)
 * - <50: yellow (Medium)
 */
function getPriorityBadge(score: number): { label: string; className: string } {
  if (score >= 100) {
    return {
      label: 'Critical',
      className: 'bg-red-500 hover:bg-red-600 text-white',
    }
  }
  if (score >= 50) {
    return {
      label: 'High',
      className: 'bg-orange-500 hover:bg-orange-600 text-white',
    }
  }
  return {
    label: 'Medium',
    className: 'bg-yellow-500 hover:bg-yellow-600 text-white',
  }
}

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

interface HighPriorityRowProps {
  item: HighPriorityItem
  onNavigate: (id: number) => void
}

function HighPriorityRow({ item, onNavigate }: HighPriorityRowProps) {
  const priority = getPriorityBadge(item.priorityScore)
  const source = getSourceBadge(item.source)

  const handleClick = () => {
    onNavigate(item.id)
  }

  return (
    <div
      className="flex items-center justify-between py-2 px-2 -mx-2 rounded hover:bg-muted/50 cursor-pointer transition-colors"
      onClick={handleClick}
    >
      <div className="flex items-center gap-2 min-w-0 flex-1">
        <Badge className={source.className} variant="secondary">
          {source.label}
        </Badge>
        <span className="text-sm truncate" title={item.marketName || item.externalMarketId}>
          {item.marketName || item.externalMarketId}
        </span>
      </div>
      <Badge className={priority.className}>
        {priority.label}
      </Badge>
    </div>
  )
}

export function HighPriorityUnmapped() {
  const navigate = useNavigate()
  const { data, isLoading, error } = useHighPriorityUnmapped()

  const handleNavigateToEditor = (id: number) => {
    navigate(`/mappings/editor/${id}`)
  }

  if (error) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center gap-2 py-4">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          <CardTitle className="text-base">High Priority Unmapped</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-red-500">Failed to load high-priority items</p>
        </CardContent>
      </Card>
    )
  }

  if (isLoading) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center gap-2 py-4">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          <CardTitle className="text-base">High Priority Unmapped</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="flex items-center justify-between py-2">
              <div className="flex items-center gap-2">
                <Skeleton className="h-5 w-16" />
                <Skeleton className="h-4 w-40" />
              </div>
              <Skeleton className="h-5 w-16" />
            </div>
          ))}
        </CardContent>
      </Card>
    )
  }

  const items = data?.items ?? []

  // Empty state
  if (items.length === 0) {
    return (
      <Card>
        <CardHeader className="flex flex-row items-center gap-2 py-4">
          <CheckCircle className="h-5 w-5 text-green-500" />
          <CardTitle className="text-base">High Priority Unmapped</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-6 text-center">
            <CheckCircle className="h-10 w-10 text-green-500 mb-2" />
            <p className="text-sm font-medium text-green-700">All caught up!</p>
            <p className="text-xs text-muted-foreground mt-1">
              No high-priority unmapped markets
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center gap-2 py-4">
        <AlertTriangle className="h-5 w-5 text-orange-500" />
        <CardTitle className="text-base">High Priority Unmapped</CardTitle>
        <Badge variant="secondary" className="ml-auto">
          {items.length}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {items.map((item) => (
            <HighPriorityRow key={item.id} item={item} onNavigate={handleNavigateToEditor} />
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
