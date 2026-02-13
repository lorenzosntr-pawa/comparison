import { useState, useCallback } from 'react'
import { useParams, Link } from 'react-router'
import { ArrowLeft, Loader2, AlertCircle } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useUnmappedDetail } from './hooks/use-unmapped-detail'
import { SourceMarketPanel } from './components/source-market-panel'
import { TargetMarketPanel } from './components/target-market-panel'
import type { MappingFormState } from './components/target-market-form'
import type { MappingPickerMode } from './components/mapping-picker'

/**
 * Mapping Editor page.
 *
 * Two-column layout (40% / 60%):
 * - Left panel: Source market details (platform, name, external ID, occurrences, sample outcomes)
 * - Right panel: Target market configuration (picker to select existing or create new, form fields)
 */
export function MappingEditor() {
  const { unmappedId } = useParams<{ unmappedId: string }>()
  const id = unmappedId ? parseInt(unmappedId, 10) : undefined
  const { data, isLoading, error } = useUnmappedDetail(id)

  // Target market panel state
  const [pickerMode, setPickerMode] = useState<MappingPickerMode>('create')
  const [selectedMappingId, setSelectedMappingId] = useState<string | undefined>()
  const [formState, setFormState] = useState<MappingFormState>({
    canonicalId: '',
    name: '',
    betpawaId: null,
    sportybetId: null,
    bet9jaKey: null,
    priority: 10,
  })

  // Stable callback for form changes to avoid unnecessary re-renders
  const handleFormChange = useCallback((state: MappingFormState) => {
    setFormState(state)
  }, [])

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

      {/* Two-column layout: 40% source, 60% target */}
      <div className="grid gap-6 lg:grid-cols-[2fr_3fr]">
        {/* Left Panel: Source Market Details */}
        <SourceMarketPanel data={data} />

        {/* Right Panel: Target Market Configuration */}
        <TargetMarketPanel
          sourceMarket={data}
          formState={formState}
          onFormChange={handleFormChange}
          selectedMappingId={selectedMappingId}
          onMappingSelect={setSelectedMappingId}
          mode={pickerMode}
          onModeChange={setPickerMode}
        />
      </div>
    </div>
  )
}
