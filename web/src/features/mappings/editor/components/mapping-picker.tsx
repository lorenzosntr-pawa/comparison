import * as React from 'react'
import { Check, ChevronsUpDown, Plus, X, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useMappingsSearch, type MappingListItem } from '../hooks/use-mappings-search'

export type MappingPickerMode = 'select' | 'create'

interface MappingPickerProps {
  onSelect: (mapping: MappingListItem | null) => void
  selectedId?: string
  mode: MappingPickerMode
  onModeChange: (mode: MappingPickerMode) => void
}

/**
 * MappingPicker component with searchable dropdown for existing mappings.
 *
 * Two modes:
 * - "select": Choose an existing mapping to extend
 * - "create": Create a new mapping from scratch
 */
export function MappingPicker({
  onSelect,
  selectedId,
  mode,
  onModeChange,
}: MappingPickerProps) {
  const [open, setOpen] = React.useState(false)
  const [search, setSearch] = React.useState('')
  const { data, isLoading } = useMappingsSearch(search)

  const mappings = data?.items ?? []
  const selectedMapping = mappings.find((m) => m.canonicalId === selectedId)

  const handleSelect = (mapping: MappingListItem) => {
    onSelect(mapping)
    setOpen(false)
    setSearch('')
  }

  const handleClear = () => {
    onSelect(null)
    setSearch('')
  }

  const handleModeChange = (value: string) => {
    const newMode = value as MappingPickerMode
    onModeChange(newMode)
    if (newMode === 'create') {
      onSelect(null)
    }
  }

  return (
    <div className="space-y-3">
      {/* Mode toggle */}
      <Tabs value={mode} onValueChange={handleModeChange}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="select">Extend Existing</TabsTrigger>
          <TabsTrigger value="create">Create New</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Select existing mode */}
      {mode === 'select' && (
        <div className="space-y-2">
          <Popover open={open} onOpenChange={setOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                role="combobox"
                aria-expanded={open}
                className="w-full justify-between"
              >
                {selectedMapping ? (
                  <span className="truncate">{selectedMapping.name}</span>
                ) : (
                  <span className="text-muted-foreground">Search existing mappings...</span>
                )}
                <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-[400px] p-0" align="start">
              <Command shouldFilter={false}>
                <CommandInput
                  placeholder="Search by name or canonical ID..."
                  value={search}
                  onValueChange={setSearch}
                />
                <CommandList>
                  {isLoading ? (
                    <div className="flex items-center justify-center py-6">
                      <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                    </div>
                  ) : mappings.length === 0 ? (
                    <CommandEmpty>No mappings found.</CommandEmpty>
                  ) : (
                    <CommandGroup>
                      {mappings.map((mapping) => (
                        <CommandItem
                          key={mapping.canonicalId}
                          value={mapping.canonicalId}
                          onSelect={() => handleSelect(mapping)}
                        >
                          <div className="flex flex-1 flex-col gap-1">
                            <div className="flex items-center gap-2">
                              <span className="font-medium">{mapping.name}</span>
                              {mapping.canonicalId === selectedId && (
                                <Check className="h-4 w-4 text-primary" />
                              )}
                            </div>
                            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                              <code className="bg-muted px-1 py-0.5 rounded">
                                {mapping.canonicalId}
                              </code>
                              <PlatformBadges mapping={mapping} />
                            </div>
                          </div>
                        </CommandItem>
                      ))}
                    </CommandGroup>
                  )}
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>

          {/* Selected mapping summary */}
          {selectedMapping && (
            <SelectedMappingSummary
              mapping={selectedMapping}
              onClear={handleClear}
            />
          )}
        </div>
      )}

      {/* Create new mode */}
      {mode === 'create' && (
        <div className="flex items-center gap-2 rounded-md border border-dashed p-4 text-sm text-muted-foreground">
          <Plus className="h-4 w-4" />
          <span>New mapping will be created with the form below</span>
        </div>
      )}
    </div>
  )
}

/**
 * Platform availability badges for a mapping.
 */
function PlatformBadges({ mapping }: { mapping: MappingListItem }) {
  return (
    <div className="flex gap-1">
      {mapping.betpawaId && (
        <Badge variant="secondary" className="text-[10px] px-1 py-0">
          BP
        </Badge>
      )}
      {mapping.sportybetId && (
        <Badge variant="secondary" className="text-[10px] px-1 py-0">
          SB
        </Badge>
      )}
      {mapping.bet9jaKey && (
        <Badge variant="secondary" className="text-[10px] px-1 py-0">
          B9
        </Badge>
      )}
      <Badge
        variant={mapping.source === 'code' ? 'outline' : 'default'}
        className="text-[10px] px-1 py-0"
      >
        {mapping.source}
      </Badge>
    </div>
  )
}

/**
 * Summary display of the selected mapping with clear button.
 */
function SelectedMappingSummary({
  mapping,
  onClear,
}: {
  mapping: MappingListItem
  onClear: () => void
}) {
  return (
    <div className="flex items-start justify-between rounded-md border bg-muted/50 p-3">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{mapping.name}</span>
          <PlatformBadges mapping={mapping} />
        </div>
        <div className="text-xs text-muted-foreground">
          <code className="bg-muted px-1 py-0.5 rounded">
            {mapping.canonicalId}
          </code>
          <span className="ml-2">{mapping.outcomeCount} outcomes</span>
        </div>
      </div>
      <Button
        variant="ghost"
        size="sm"
        className="h-6 w-6 p-0"
        onClick={onClear}
      >
        <X className="h-3 w-3" />
        <span className="sr-only">Clear selection</span>
      </Button>
    </div>
  )
}
