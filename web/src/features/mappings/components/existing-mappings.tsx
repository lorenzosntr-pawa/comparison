import { useState } from 'react'
import { useNavigate } from 'react-router'
import { Search, Edit2, Copy, Code, Database } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useMappingsSearch, type MappingListItem } from '../editor/hooks/use-mappings-search'

type SourceFilter = 'all' | 'code' | 'db'

/**
 * Get platform badge styling.
 */
function PlatformBadge({ label, present }: { label: string; present: boolean }) {
  if (!present) {
    return (
      <Badge variant="outline" className="text-muted-foreground opacity-40">
        {label}
      </Badge>
    )
  }
  return (
    <Badge variant="secondary" className="bg-green-100 text-green-800">
      {label}
    </Badge>
  )
}

/**
 * Get source badge styling.
 */
function SourceBadge({ source }: { source: 'code' | 'db' }) {
  if (source === 'code') {
    return (
      <Badge variant="outline" className="gap-1">
        <Code className="h-3 w-3" />
        Code
      </Badge>
    )
  }
  return (
    <Badge variant="secondary" className="gap-1 bg-blue-100 text-blue-800">
      <Database className="h-3 w-3" />
      User
    </Badge>
  )
}

interface MappingRowProps {
  item: MappingListItem
  onEdit: (canonicalId: string, source: 'code' | 'db') => void
}

function MappingRow({ item, onEdit }: MappingRowProps) {
  const handleAction = () => {
    onEdit(item.canonicalId, item.source)
  }

  return (
    <TableRow className="cursor-pointer hover:bg-muted/50" onClick={handleAction}>
      <TableCell className="font-mono text-sm">{item.canonicalId}</TableCell>
      <TableCell>{item.name}</TableCell>
      <TableCell>
        <div className="flex gap-1">
          <PlatformBadge label="BP" present={!!item.betpawaId} />
          <PlatformBadge label="SB" present={!!item.sportybetId} />
          <PlatformBadge label="B9" present={!!item.bet9jaKey} />
        </div>
      </TableCell>
      <TableCell className="text-center">{item.outcomeCount}</TableCell>
      <TableCell>
        <SourceBadge source={item.source} />
      </TableCell>
      <TableCell>
        <Button
          variant="ghost"
          size="sm"
          className="gap-1"
          onClick={(e) => {
            e.stopPropagation()
            handleAction()
          }}
        >
          {item.source === 'db' ? (
            <>
              <Edit2 className="h-3 w-3" />
              Edit
            </>
          ) : (
            <>
              <Copy className="h-3 w-3" />
              Override
            </>
          )}
        </Button>
      </TableCell>
    </TableRow>
  )
}

function LoadingSkeleton() {
  return (
    <div className="space-y-2">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-center gap-4 py-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-40" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-8" />
          <Skeleton className="h-4 w-16" />
        </div>
      ))}
    </div>
  )
}

export function ExistingMappings() {
  const navigate = useNavigate()
  const [search, setSearch] = useState('')
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all')

  const { data, isLoading, error } = useMappingsSearch(search)

  const handleEdit = (canonicalId: string, source: 'code' | 'db') => {
    if (source === 'db') {
      // Edit existing user mapping
      navigate(`/mappings/editor/existing/${encodeURIComponent(canonicalId)}`)
    } else {
      // Override code mapping - create new user mapping with same canonical ID
      navigate(`/mappings/editor/override/${encodeURIComponent(canonicalId)}`)
    }
  }

  // Filter by source
  const filteredItems = (data?.items ?? []).filter((item) => {
    if (sourceFilter === 'all') return true
    return item.source === sourceFilter
  })

  // Calculate counts for tab badges
  const allCount = data?.items?.length ?? 0
  const codeCount = data?.items?.filter((i) => i.source === 'code').length ?? 0
  const dbCount = data?.items?.filter((i) => i.source === 'db').length ?? 0

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base">Existing Mappings</CardTitle>
          <Badge variant="secondary">{allCount} total</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search and Filter */}
        <div className="flex items-center gap-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search by name or ID..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-8"
            />
          </div>
          <Tabs
            value={sourceFilter}
            onValueChange={(v) => setSourceFilter(v as SourceFilter)}
          >
            <TabsList>
              <TabsTrigger value="all">All ({allCount})</TabsTrigger>
              <TabsTrigger value="code">Code ({codeCount})</TabsTrigger>
              <TabsTrigger value="db">User ({dbCount})</TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {/* Error state */}
        {error && (
          <p className="text-sm text-red-500">Failed to load mappings: {error.message}</p>
        )}

        {/* Loading state */}
        {isLoading && <LoadingSkeleton />}

        {/* Table */}
        {!isLoading && !error && (
          <div className="border rounded-md">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-32">Canonical ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead className="w-32">Platforms</TableHead>
                  <TableHead className="w-20 text-center">Outcomes</TableHead>
                  <TableHead className="w-20">Source</TableHead>
                  <TableHead className="w-24">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-muted-foreground py-8">
                      {search ? 'No mappings found matching your search' : 'No mappings found'}
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredItems.map((item) => (
                    <MappingRow key={item.canonicalId} item={item} onEdit={handleEdit} />
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
