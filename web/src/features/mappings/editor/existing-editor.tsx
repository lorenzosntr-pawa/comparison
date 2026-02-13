import { useState, useCallback, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router'
import { ArrowLeft, Loader2, AlertCircle, Send, Edit2, Copy, CheckCircle2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useMappingDetail } from './hooks/use-mapping-detail'
import { useCreateMapping, useUpdateMapping } from './hooks/use-create-mapping'
import { isValidForSubmission } from './components/mapping-preview'
import { OutcomeMappingTable } from './components/outcome-mapping-table'
import type { MappingFormState, MappingDetailResponse } from './components/target-market-form'
import type { OutcomeFormItem } from './utils/outcome-suggest'

interface ExistingEditorProps {
  mode: 'edit' | 'override'
}

/**
 * Convert MappingDetailResponse outcomes to OutcomeFormItem array.
 */
function mapOutcomesToFormItems(mapping: MappingDetailResponse): OutcomeFormItem[] {
  return mapping.outcomeMapping.map((o, index) => ({
    id: `outcome-${index}`,
    canonicalId: o.canonicalId,
    betpawaName: o.betpawaName ?? '',
    sportybetDesc: o.sportybetDesc ?? '',
    bet9jaSuffix: o.bet9jaSuffix ?? '',
    position: o.position,
    source: 'existing' as const,
  }))
}

/**
 * Simple form for editing mapping configuration.
 */
function MappingForm({
  value,
  onChange,
  mode,
}: {
  value: MappingFormState
  onChange: (value: MappingFormState) => void
  mode: 'edit' | 'override'
}) {
  const handleFieldChange = (
    field: keyof MappingFormState,
    newValue: string | number | null
  ) => {
    onChange({ ...value, [field]: newValue })
  }

  return (
    <div className="space-y-4">
      {/* Canonical ID - always readonly for existing mappings */}
      <div className="space-y-2">
        <Label htmlFor="canonicalId">
          Canonical ID
          <Badge variant="outline" className="ml-2 text-[10px]">
            Read-only
          </Badge>
        </Label>
        <Input
          id="canonicalId"
          value={value.canonicalId}
          disabled
          className="bg-muted"
        />
      </div>

      {/* Name */}
      <div className="space-y-2">
        <Label htmlFor="name">Name</Label>
        <Input
          id="name"
          value={value.name}
          onChange={(e) => handleFieldChange('name', e.target.value)}
          placeholder="e.g., Match Result (1X2)"
        />
      </div>

      {/* Platform IDs Section */}
      <div className="space-y-3">
        <Label className="text-sm font-medium">Platform IDs</Label>

        <div className="grid gap-3 md:grid-cols-3">
          {/* Betpawa ID */}
          <div className="space-y-1">
            <Label htmlFor="betpawaId" className="text-sm">
              Betpawa ID
            </Label>
            <Input
              id="betpawaId"
              value={value.betpawaId || ''}
              onChange={(e) =>
                handleFieldChange('betpawaId', e.target.value || null)
              }
              placeholder="e.g., 3743"
            />
          </div>

          {/* SportyBet ID */}
          <div className="space-y-1">
            <Label htmlFor="sportybetId" className="text-sm">
              SportyBet ID
            </Label>
            <Input
              id="sportybetId"
              value={value.sportybetId || ''}
              onChange={(e) =>
                handleFieldChange('sportybetId', e.target.value || null)
              }
              placeholder="e.g., 1"
            />
          </div>

          {/* Bet9ja Key */}
          <div className="space-y-1">
            <Label htmlFor="bet9jaKey" className="text-sm">
              Bet9ja Key
            </Label>
            <Input
              id="bet9jaKey"
              value={value.bet9jaKey || ''}
              onChange={(e) =>
                handleFieldChange('bet9jaKey', e.target.value || null)
              }
              placeholder="e.g., S_1X2"
            />
          </div>
        </div>
      </div>

      {/* Priority */}
      <div className="space-y-2">
        <Label htmlFor="priority">Priority (0-100)</Label>
        <Input
          id="priority"
          type="number"
          min={0}
          max={100}
          value={value.priority}
          onChange={(e) => {
            const num = parseInt(e.target.value, 10)
            handleFieldChange('priority', isNaN(num) ? 0 : Math.min(100, Math.max(0, num)))
          }}
          placeholder="10"
        />
        <p className="text-xs text-muted-foreground">
          Higher priority mappings override lower ones. {mode === 'override' && 'User mappings need priority > 0 to override code.'}
        </p>
      </div>
    </div>
  )
}

/**
 * Simple outcome table for edit mode (no source platform highlighting).
 */
function SimpleOutcomeTable({
  outcomes,
  onChange,
}: {
  outcomes: OutcomeFormItem[]
  onChange: (outcomes: OutcomeFormItem[]) => void
}) {
  // Wrap with a neutral source platform for the existing component
  return (
    <OutcomeMappingTable
      outcomes={outcomes}
      onChange={onChange}
      sourcePlatform="sportybet" // Neutral - no highlighting needed
    />
  )
}

type SubmitState = 'idle' | 'submitting' | 'success' | 'error'

/**
 * Editor for existing mappings.
 *
 * Supports two modes:
 * - edit: Edit an existing user mapping (source = 'db')
 * - override: Create a new user mapping that overrides a code mapping
 */
export function ExistingEditor({ mode }: ExistingEditorProps) {
  const navigate = useNavigate()
  const { canonicalId } = useParams<{ canonicalId: string }>()
  const decodedId = canonicalId ? decodeURIComponent(canonicalId) : undefined
  const { data: mapping, isLoading, error } = useMappingDetail(decodedId)

  // Form state
  const [formState, setFormState] = useState<MappingFormState>({
    canonicalId: '',
    name: '',
    betpawaId: null,
    sportybetId: null,
    bet9jaKey: null,
    priority: 10,
  })

  // Outcome mapping state
  const [outcomes, setOutcomes] = useState<OutcomeFormItem[]>([])

  // Submit dialog state
  const [isSubmitDialogOpen, setIsSubmitDialogOpen] = useState(false)
  const [reason, setReason] = useState('')
  const [submitState, setSubmitState] = useState<SubmitState>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // Mutations
  const createMutation = useCreateMapping()
  const updateMutation = useUpdateMapping()

  // Initialize form when mapping loads
  useEffect(() => {
    if (mapping) {
      setFormState({
        canonicalId: mapping.canonicalId,
        name: mapping.name,
        betpawaId: mapping.betpawaId,
        sportybetId: mapping.sportybetId,
        bet9jaKey: mapping.bet9jaKey,
        priority: mode === 'override' ? 10 : mapping.priority, // Higher priority for override
      })
      setOutcomes(mapOutcomesToFormItems(mapping))
    }
  }, [mapping, mode])

  // Reset dialog state when opened
  useEffect(() => {
    if (isSubmitDialogOpen) {
      setReason('')
      setSubmitState('idle')
      setErrorMessage(null)
    }
  }, [isSubmitDialogOpen])

  // Stable callback for form changes
  const handleFormChange = useCallback((state: MappingFormState) => {
    setFormState(state)
  }, [])

  // Stable callback for outcome changes
  const handleOutcomesChange = useCallback((newOutcomes: OutcomeFormItem[]) => {
    setOutcomes(newOutcomes)
  }, [])

  const isValid = isValidForSubmission(formState, outcomes)
  const canSubmit = isValid && reason.trim().length > 0 && submitState === 'idle'

  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return

    setSubmitState('submitting')
    setErrorMessage(null)

    try {
      if (mode === 'override') {
        // Create new user mapping that overrides code mapping
        await createMutation.mutateAsync({
          canonicalId: formState.canonicalId,
          name: formState.name,
          betpawaId: formState.betpawaId,
          sportybetId: formState.sportybetId,
          bet9jaKey: formState.bet9jaKey,
          outcomeMapping: outcomes,
          priority: formState.priority,
          reason: reason.trim(),
        })
      } else {
        // Update existing user mapping
        await updateMutation.mutateAsync({
          canonicalId: formState.canonicalId,
          name: formState.name,
          betpawaId: formState.betpawaId,
          sportybetId: formState.sportybetId,
          bet9jaKey: formState.bet9jaKey,
          outcomeMapping: outcomes,
          priority: formState.priority,
          reason: reason.trim(),
        })
      }

      setSubmitState('success')
      setTimeout(() => {
        navigate('/mappings')
      }, 1500)
    } catch (err) {
      setSubmitState('error')
      setErrorMessage(err instanceof Error ? err.message : 'An unexpected error occurred')
    }
  }, [canSubmit, mode, formState, outcomes, reason, createMutation, updateMutation, navigate])

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
              <span>Failed to load mapping: {error.message}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  // No data state
  if (!mapping) {
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
            <p className="text-muted-foreground">Mapping not found</p>
          </CardContent>
        </Card>
      </div>
    )
  }

  const isEditMode = mode === 'edit'
  const title = isEditMode ? 'Edit Mapping' : 'Override Mapping'
  const description = isEditMode
    ? 'Edit this user-created mapping'
    : 'Create a user mapping that overrides this code mapping'

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
        <div className="flex items-center gap-2">
          {isEditMode ? (
            <Badge variant="secondary" className="gap-1 bg-blue-100 text-blue-800">
              <Edit2 className="h-3 w-3" />
              Edit Mode
            </Badge>
          ) : (
            <Badge variant="secondary" className="gap-1 bg-orange-100 text-orange-800">
              <Copy className="h-3 w-3" />
              Override Mode
            </Badge>
          )}
        </div>
      </div>

      {/* Title Card */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle>{title}</CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <span className="text-sm text-muted-foreground">Canonical ID</span>
              <p className="font-mono text-sm">{mapping.canonicalId}</p>
            </div>
            <div>
              <span className="text-sm text-muted-foreground">Original Source</span>
              <p className="text-sm">
                {mapping.source === 'code' ? 'Code-defined' : 'User-created'}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Form Section */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Mapping Configuration</CardTitle>
        </CardHeader>
        <CardContent>
          <MappingForm
            value={formState}
            onChange={handleFormChange}
            mode={mode}
          />
        </CardContent>
      </Card>

      {/* Outcome Mapping Section */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Outcome Mappings</CardTitle>
        </CardHeader>
        <CardContent>
          <SimpleOutcomeTable
            outcomes={outcomes}
            onChange={handleOutcomesChange}
          />
        </CardContent>
      </Card>

      {/* Submit Button */}
      <div className="flex justify-end pt-4 border-t">
        <Button
          size="lg"
          onClick={() => setIsSubmitDialogOpen(true)}
          disabled={!isValid}
          className="gap-2"
        >
          <Send className="h-4 w-4" />
          Preview & Submit
        </Button>
      </div>

      {/* Submit Dialog */}
      <Dialog open={isSubmitDialogOpen} onOpenChange={setIsSubmitDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>
              {submitState === 'success'
                ? 'Mapping Saved'
                : isEditMode ? 'Update Mapping' : 'Create Override Mapping'}
            </DialogTitle>
            <DialogDescription>
              {submitState === 'success'
                ? 'Your changes have been saved successfully.'
                : isEditMode
                  ? 'Confirm your changes to this user mapping.'
                  : 'This will create a user mapping that overrides the code mapping.'}
            </DialogDescription>
          </DialogHeader>

          {submitState === 'success' ? (
            <div className="flex flex-col items-center justify-center py-8 gap-4">
              <CheckCircle2 className="h-16 w-16 text-green-500" />
              <p className="text-lg font-medium">Mapping saved!</p>
              <p className="text-sm text-muted-foreground">
                Redirecting to dashboard...
              </p>
            </div>
          ) : (
            <>
              {/* Summary */}
              <div className="py-4 space-y-2 border-y">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Canonical ID</span>
                  <span className="font-mono">{formState.canonicalId}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Name</span>
                  <span>{formState.name}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Outcomes</span>
                  <span>{outcomes.length}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Priority</span>
                  <span>{formState.priority}</span>
                </div>
              </div>

              {/* Reason Input */}
              <div className="space-y-2">
                <Label htmlFor="reason">
                  Reason for change <span className="text-destructive">*</span>
                </Label>
                <Input
                  id="reason"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g., Updating outcome mappings for Bet9ja"
                  disabled={submitState === 'submitting'}
                />
                <p className="text-xs text-muted-foreground">
                  This will be recorded in the audit log.
                </p>
              </div>

              {/* Error Display */}
              {submitState === 'error' && errorMessage && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{errorMessage}</AlertDescription>
                </Alert>
              )}

              <DialogFooter className="gap-2 sm:gap-0">
                <Button
                  variant="outline"
                  onClick={() => setIsSubmitDialogOpen(false)}
                  disabled={submitState === 'submitting'}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSubmit}
                  disabled={!canSubmit}
                >
                  {submitState === 'submitting' ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    isEditMode ? 'Update Mapping' : 'Create Override'
                  )}
                </Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

/**
 * Edit existing user mapping.
 */
export function EditMappingEditor() {
  return <ExistingEditor mode="edit" />
}

/**
 * Override code mapping with user mapping.
 */
export function OverrideMappingEditor() {
  return <ExistingEditor mode="override" />
}
