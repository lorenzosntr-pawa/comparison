import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router'
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { MappingPreview, isValidForSubmission } from './mapping-preview'
import { useCreateMapping, useUpdateMapping } from '../hooks/use-create-mapping'
import { useUpdateUnmappedStatus } from '../hooks/use-update-unmapped-status'
import type { MappingFormState, MappingDetailResponse } from './target-market-form'
import type { OutcomeFormItem } from '../utils/outcome-suggest'
import type { UnmappedMarketDetail } from '../hooks/use-unmapped-detail'

export interface SubmitDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  mode: 'create' | 'extend'
  formState: MappingFormState
  outcomes: OutcomeFormItem[]
  sourceMarket: UnmappedMarketDetail
  existingMapping?: MappingDetailResponse | null
}

type SubmitState = 'idle' | 'submitting' | 'success' | 'error'

/**
 * Parse API error response to get user-friendly message.
 */
function parseApiError(error: unknown): string {
  if (error instanceof Error) {
    try {
      // Try to parse JSON error from API
      const parsed = JSON.parse(error.message)
      if (parsed.detail) {
        return typeof parsed.detail === 'string'
          ? parsed.detail
          : JSON.stringify(parsed.detail)
      }
    } catch {
      // Not JSON, use message directly
      return error.message
    }
  }
  return 'An unexpected error occurred'
}

/**
 * SubmitDialog handles the preview and submit flow for mapping creation/extension.
 *
 * Features:
 * - Displays MappingPreview with summary of changes
 * - Requires a reason for audit log
 * - Handles create mode (POST new mapping) and extend mode (PATCH existing)
 * - Updates unmapped market status to MAPPED on success
 * - Shows loading, success, and error states
 * - Redirects to dashboard on success
 * - Supports Cmd/Ctrl+Enter keyboard shortcut
 */
export function SubmitDialog({
  open,
  onOpenChange,
  mode,
  formState,
  outcomes,
  sourceMarket,
  existingMapping,
}: SubmitDialogProps) {
  const navigate = useNavigate()
  const [reason, setReason] = useState('')
  const [submitState, setSubmitState] = useState<SubmitState>('idle')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const createMutation = useCreateMapping()
  const updateMutation = useUpdateMapping()
  const unmappedStatusMutation = useUpdateUnmappedStatus()

  const isValid = isValidForSubmission(formState, outcomes)
  const canSubmit = isValid && reason.trim().length > 0 && submitState === 'idle'

  // Reset state when dialog opens
  useEffect(() => {
    if (open) {
      setReason('')
      setSubmitState('idle')
      setErrorMessage(null)
    }
  }, [open])

  const handleSubmit = useCallback(async () => {
    if (!canSubmit) return

    setSubmitState('submitting')
    setErrorMessage(null)

    try {
      // Step 1: Create or update the mapping
      if (mode === 'create') {
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
        // Extend mode - update existing mapping with new platform ID
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

      // Step 2: Mark unmapped market as MAPPED
      await unmappedStatusMutation.mutateAsync({
        id: sourceMarket.id,
        status: 'MAPPED',
      })

      // Step 3: Show success and redirect
      setSubmitState('success')
      setTimeout(() => {
        navigate('/mappings')
      }, 1500)
    } catch (error) {
      setSubmitState('error')
      setErrorMessage(parseApiError(error))
    }
  }, [
    canSubmit,
    mode,
    formState,
    outcomes,
    reason,
    sourceMarket.id,
    createMutation,
    updateMutation,
    unmappedStatusMutation,
    navigate,
  ])

  // Keyboard shortcut: Cmd/Ctrl+Enter to submit
  useEffect(() => {
    if (!open) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && canSubmit) {
        e.preventDefault()
        handleSubmit()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [open, canSubmit, handleSubmit])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {submitState === 'success'
              ? 'Mapping Saved'
              : 'Preview & Submit Mapping'}
          </DialogTitle>
          <DialogDescription>
            {submitState === 'success'
              ? 'Your mapping has been saved successfully.'
              : 'Review the mapping details below before submitting.'}
          </DialogDescription>
        </DialogHeader>

        {submitState === 'success' ? (
          <div className="flex flex-col items-center justify-center py-8 gap-4">
            <CheckCircle2 className="h-16 w-16 text-green-500" />
            <p className="text-lg font-medium">Mapping saved successfully!</p>
            <p className="text-sm text-muted-foreground">
              Redirecting to dashboard...
            </p>
          </div>
        ) : (
          <>
            {/* Preview Content */}
            <div className="py-4">
              <MappingPreview
                mode={mode}
                formState={formState}
                outcomes={outcomes}
                sourceMarket={sourceMarket}
                existingMapping={existingMapping}
              />
            </div>

            {/* Reason Input */}
            <div className="space-y-2 border-t pt-4">
              <Label htmlFor="reason">
                Reason for change <span className="text-destructive">*</span>
              </Label>
              <Input
                id="reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g., Adding SportyBet support for 1X2 market"
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
                onClick={() => onOpenChange(false)}
                disabled={submitState === 'submitting'}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={!canSubmit || submitState === 'submitting'}
              >
                {submitState === 'submitting' ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  'Submit Mapping'
                )}
              </Button>
            </DialogFooter>

            {/* Keyboard shortcut hint */}
            <p className="text-xs text-center text-muted-foreground">
              Press{' '}
              <kbd className="rounded border bg-muted px-1 py-0.5 font-mono text-[10px]">
                Ctrl
              </kbd>
              +
              <kbd className="rounded border bg-muted px-1 py-0.5 font-mono text-[10px]">
                Enter
              </kbd>{' '}
              to submit
            </p>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
