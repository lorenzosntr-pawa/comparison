import * as React from 'react'
import { Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { MappingPicker, type MappingPickerMode } from './mapping-picker'
import {
  TargetMarketForm,
  createInitialFormState,
  createExtendFormState,
  type MappingFormState,
} from './target-market-form'
import { useMappingDetail } from '../hooks/use-mapping-detail'
import type { MappingListItem } from '../hooks/use-mappings-search'
import type { UnmappedMarketDetail } from '../hooks/use-unmapped-detail'

interface TargetMarketPanelProps {
  sourceMarket: UnmappedMarketDetail
  formState: MappingFormState
  onFormChange: (state: MappingFormState) => void
  selectedMappingId: string | undefined
  onMappingSelect: (id: string | undefined) => void
  mode: MappingPickerMode
  onModeChange: (mode: MappingPickerMode) => void
}

/**
 * TargetMarketPanel composes the mapping picker and form.
 *
 * Manages the flow:
 * - User can choose "Extend Existing" and search for a mapping
 * - When selected, fetches full details and pre-fills form
 * - User can choose "Create New" for a blank form
 */
export function TargetMarketPanel({
  sourceMarket,
  formState,
  onFormChange,
  selectedMappingId,
  onMappingSelect,
  mode,
  onModeChange,
}: TargetMarketPanelProps) {
  // Fetch full mapping details when one is selected
  const { data: mappingDetail, isLoading: isLoadingDetail } = useMappingDetail(
    mode === 'select' ? selectedMappingId : undefined
  )

  // Update form when mapping detail loads or mode changes
  React.useEffect(() => {
    if (mode === 'create') {
      onFormChange(createInitialFormState(sourceMarket))
    } else if (mode === 'select' && mappingDetail) {
      onFormChange(createExtendFormState(mappingDetail, sourceMarket))
    }
  }, [mode, mappingDetail, sourceMarket, onFormChange])

  const handleMappingSelect = (mapping: MappingListItem | null) => {
    onMappingSelect(mapping?.canonicalId)
  }

  const handleModeChange = (newMode: MappingPickerMode) => {
    onModeChange(newMode)
    if (newMode === 'create') {
      onMappingSelect(undefined)
    }
  }

  // Determine form mode based on picker mode and selection
  const formMode = mode === 'create' ? 'create' : 'extend'

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Target Market</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Mapping picker */}
        <MappingPicker
          onSelect={handleMappingSelect}
          selectedId={selectedMappingId}
          mode={mode}
          onModeChange={handleModeChange}
        />

        {/* Loading state when fetching mapping details */}
        {mode === 'select' && selectedMappingId && isLoadingDetail && (
          <div className="flex items-center justify-center py-6">
            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">
              Loading mapping details...
            </span>
          </div>
        )}

        {/* Form - show when we have data to display */}
        {(mode === 'create' ||
          (mode === 'select' && selectedMappingId && mappingDetail)) && (
          <TargetMarketForm
            mode={formMode}
            existingMapping={mappingDetail}
            sourceMarket={sourceMarket}
            value={formState}
            onChange={onFormChange}
          />
        )}

        {/* Prompt to select when in select mode without selection */}
        {mode === 'select' && !selectedMappingId && (
          <div className="py-8 text-center text-sm text-muted-foreground">
            Search and select an existing mapping above to extend it with the
            source market platform ID.
          </div>
        )}
      </CardContent>
    </Card>
  )
}
