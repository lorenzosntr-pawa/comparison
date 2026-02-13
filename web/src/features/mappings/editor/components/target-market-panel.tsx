import * as React from 'react'
import { Loader2, Wand2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { MappingPicker, type MappingPickerMode } from './mapping-picker'
import {
  TargetMarketForm,
  createInitialFormState,
  createExtendFormState,
  type MappingFormState,
} from './target-market-form'
import { OutcomeMappingTable } from './outcome-mapping-table'
import {
  suggestOutcomes,
  suggestionsToFormItems,
  type OutcomeFormItem,
  type SourcePlatform,
} from '../utils/outcome-suggest'
import { useMappingDetail } from '../hooks/use-mapping-detail'
import type { MappingListItem } from '../hooks/use-mappings-search'
import type { UnmappedMarketDetail } from '../hooks/use-unmapped-detail'

interface TargetMarketPanelProps {
  sourceMarket: UnmappedMarketDetail
  formState: MappingFormState
  onFormChange: (state: MappingFormState) => void
  outcomes: OutcomeFormItem[]
  onOutcomesChange: (outcomes: OutcomeFormItem[]) => void
  selectedMappingId: string | undefined
  onMappingSelect: (id: string | undefined) => void
  mode: MappingPickerMode
  onModeChange: (mode: MappingPickerMode) => void
}

/**
 * Converts existing mapping outcome data to form items.
 */
function existingOutcomesToFormItems(
  outcomeMapping: Array<{
    canonicalId: string
    betpawaName: string | null
    sportybetDesc: string | null
    bet9jaSuffix: string | null
    position: number
  }>
): OutcomeFormItem[] {
  return outcomeMapping.map((om) => ({
    canonicalId: om.canonicalId,
    betpawaName: om.betpawaName,
    sportybetDesc: om.sportybetDesc,
    bet9jaSuffix: om.bet9jaSuffix,
    position: om.position,
  }))
}

/**
 * TargetMarketPanel composes the mapping picker, form, and outcome mapping table.
 *
 * Manages the flow:
 * - User can choose "Extend Existing" and search for a mapping
 * - When selected, fetches full details and pre-fills form + outcomes
 * - User can choose "Create New" for a blank form with auto-suggested outcomes
 */
export function TargetMarketPanel({
  sourceMarket,
  formState,
  onFormChange,
  outcomes,
  onOutcomesChange,
  selectedMappingId,
  onMappingSelect,
  mode,
  onModeChange,
}: TargetMarketPanelProps) {
  // Track whether outcomes were auto-suggested
  const [isAutoSuggested, setIsAutoSuggested] = React.useState(false)

  // Fetch full mapping details when one is selected
  const { data: mappingDetail, isLoading: isLoadingDetail } = useMappingDetail(
    mode === 'select' ? selectedMappingId : undefined
  )

  // Determine source platform (only sportybet and bet9ja are mapped)
  const sourcePlatform = sourceMarket.source as SourcePlatform

  /**
   * Generate outcome suggestions from source market sample outcomes.
   */
  const handleAutoSuggest = React.useCallback(() => {
    if (sourcePlatform !== 'sportybet' && sourcePlatform !== 'bet9ja') {
      return
    }
    const suggestions = suggestOutcomes(
      sourceMarket.sampleOutcomes,
      sourcePlatform
    )
    onOutcomesChange(suggestionsToFormItems(suggestions))
    setIsAutoSuggested(true)
  }, [sourceMarket.sampleOutcomes, sourcePlatform, onOutcomesChange])

  // Update form and outcomes when mapping detail loads or mode changes
  React.useEffect(() => {
    if (mode === 'create') {
      onFormChange(createInitialFormState(sourceMarket))
      // Auto-suggest outcomes on create mode
      handleAutoSuggest()
    } else if (mode === 'select' && mappingDetail) {
      onFormChange(createExtendFormState(mappingDetail, sourceMarket))
      // Load existing outcomes
      onOutcomesChange(existingOutcomesToFormItems(mappingDetail.outcomeMapping))
      setIsAutoSuggested(false)
    }
  }, [mode, mappingDetail, sourceMarket, onFormChange, onOutcomesChange, handleAutoSuggest])

  const handleMappingSelect = (mapping: MappingListItem | null) => {
    onMappingSelect(mapping?.canonicalId)
  }

  const handleModeChange = (newMode: MappingPickerMode) => {
    onModeChange(newMode)
    if (newMode === 'create') {
      onMappingSelect(undefined)
    }
  }

  const handleOutcomesChange = (newOutcomes: OutcomeFormItem[]) => {
    onOutcomesChange(newOutcomes)
    // Clear auto-suggest indicator when user makes manual changes
    setIsAutoSuggested(false)
  }

  // Determine form mode based on picker mode and selection
  const formMode = mode === 'create' ? 'create' : 'extend'

  // Check if we can auto-suggest (supported platform with sample outcomes)
  const canAutoSuggest =
    (sourcePlatform === 'sportybet' || sourcePlatform === 'bet9ja') &&
    sourceMarket.sampleOutcomes &&
    sourceMarket.sampleOutcomes.length > 0

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
          <>
            <TargetMarketForm
              mode={formMode}
              existingMapping={mappingDetail}
              sourceMarket={sourceMarket}
              value={formState}
              onChange={onFormChange}
            />

            {/* Outcome Mapping Section */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Label className="text-sm font-medium">Outcome Mappings</Label>
                  {isAutoSuggested && (
                    <Badge variant="secondary" className="text-[10px]">
                      Auto-suggested
                    </Badge>
                  )}
                  {mode === 'select' && mappingDetail && (
                    <Badge variant="outline" className="text-[10px]">
                      From existing
                    </Badge>
                  )}
                </div>
                {canAutoSuggest && (
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={handleAutoSuggest}
                    className="gap-1.5"
                  >
                    <Wand2 className="h-3.5 w-3.5" />
                    Auto-Suggest
                  </Button>
                )}
              </div>

              <OutcomeMappingTable
                outcomes={outcomes}
                onChange={handleOutcomesChange}
                sourcePlatform={
                  sourcePlatform === 'sportybet' || sourcePlatform === 'bet9ja'
                    ? sourcePlatform
                    : 'sportybet'
                }
              />
            </div>
          </>
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
