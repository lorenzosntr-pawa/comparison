import { AlertCircle, Check, Plus, RefreshCw } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { MappingFormState, MappingDetailResponse } from './target-market-form'
import type { OutcomeFormItem } from '../utils/outcome-suggest'
import type { UnmappedMarketDetail } from '../hooks/use-unmapped-detail'

export interface MappingPreviewProps {
  mode: 'create' | 'extend'
  formState: MappingFormState
  outcomes: OutcomeFormItem[]
  sourceMarket: UnmappedMarketDetail
  existingMapping?: MappingDetailResponse | null
}

interface ValidationWarning {
  type: 'error' | 'warning'
  message: string
}

/**
 * Validate the mapping form state and outcomes.
 */
function validateMapping(
  formState: MappingFormState,
  outcomes: OutcomeFormItem[],
  mode: 'create' | 'extend'
): ValidationWarning[] {
  const warnings: ValidationWarning[] = []

  // Check canonical ID
  if (!formState.canonicalId) {
    warnings.push({ type: 'error', message: 'Canonical ID is required' })
  } else if (!/^[a-z0-9_]+$/.test(formState.canonicalId)) {
    warnings.push({
      type: 'error',
      message: 'Canonical ID must be lowercase letters, numbers, and underscores only',
    })
  }

  // Check name
  if (!formState.name) {
    warnings.push({ type: 'error', message: 'Name is required' })
  }

  // Check at least one platform ID
  if (!formState.betpawaId && !formState.sportybetId && !formState.bet9jaKey) {
    warnings.push({
      type: 'error',
      message: 'At least one platform ID is required',
    })
  }

  // Check outcomes
  if (outcomes.length === 0) {
    warnings.push({ type: 'error', message: 'At least one outcome is required' })
  } else {
    // Check all outcomes have canonical IDs
    const missingCanonicalIds = outcomes.filter((o) => !o.canonicalId)
    if (missingCanonicalIds.length > 0) {
      warnings.push({
        type: 'error',
        message: `${missingCanonicalIds.length} outcome(s) missing canonical ID`,
      })
    }
  }

  return warnings
}

/**
 * Get platform coverage indicators.
 */
function getPlatformCoverage(formState: MappingFormState): {
  betpawa: boolean
  sportybet: boolean
  bet9ja: boolean
} {
  return {
    betpawa: !!formState.betpawaId,
    sportybet: !!formState.sportybetId,
    bet9ja: !!formState.bet9jaKey,
  }
}

/**
 * MappingPreview displays a summary of the mapping that will be created/updated.
 *
 * Shows:
 * - Mode indicator (create/extend)
 * - Summary of canonical ID, name, platform coverage
 * - Impact description
 * - Compact outcome preview table
 * - Validation warnings
 */
export function MappingPreview({
  mode,
  formState,
  outcomes,
  sourceMarket,
  existingMapping,
}: MappingPreviewProps) {
  const warnings = validateMapping(formState, outcomes, mode)
  const hasErrors = warnings.some((w) => w.type === 'error')
  const coverage = getPlatformCoverage(formState)

  return (
    <div className="space-y-4">
      {/* Mode Badge */}
      <div className="flex items-center gap-2">
        {mode === 'create' ? (
          <Badge className="gap-1">
            <Plus className="h-3 w-3" />
            Creating New Mapping
          </Badge>
        ) : (
          <Badge variant="secondary" className="gap-1">
            <RefreshCw className="h-3 w-3" />
            Extending Existing Mapping
          </Badge>
        )}
      </div>

      {/* Summary Card */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">Mapping Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {/* Canonical ID and Name */}
          <div className="grid gap-2 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Canonical ID</span>
              <code className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">
                {formState.canonicalId || '(not set)'}
              </code>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Name</span>
              <span className="font-medium">
                {formState.name || '(not set)'}
              </span>
            </div>
          </div>

          {/* Platform Coverage */}
          <div className="flex items-center gap-2 pt-2 border-t">
            <span className="text-sm text-muted-foreground">Platforms:</span>
            <div className="flex gap-1.5">
              <Badge
                variant={coverage.betpawa ? 'default' : 'outline'}
                className="text-[10px]"
              >
                {coverage.betpawa ? <Check className="h-2.5 w-2.5 mr-0.5" /> : null}
                Betpawa
              </Badge>
              <Badge
                variant={coverage.sportybet ? 'default' : 'outline'}
                className="text-[10px]"
              >
                {coverage.sportybet ? <Check className="h-2.5 w-2.5 mr-0.5" /> : null}
                SportyBet
              </Badge>
              <Badge
                variant={coverage.bet9ja ? 'default' : 'outline'}
                className="text-[10px]"
              >
                {coverage.bet9ja ? <Check className="h-2.5 w-2.5 mr-0.5" /> : null}
                Bet9ja
              </Badge>
            </div>
          </div>

          {/* Outcome Count */}
          <div className="flex justify-between text-sm pt-2 border-t">
            <span className="text-muted-foreground">Outcomes</span>
            <span className="font-medium">{outcomes.length}</span>
          </div>
        </CardContent>
      </Card>

      {/* Impact Section */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium">This mapping will:</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm">
            {mode === 'create' ? (
              <li className="flex items-start gap-2">
                <Check className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                <span>
                  Create new mapping with canonical_id:{' '}
                  <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
                    {formState.canonicalId || '?'}
                  </code>
                </span>
              </li>
            ) : (
              <li className="flex items-start gap-2">
                <Check className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
                <span>
                  Add <strong>{sourceMarket.source}</strong> support to existing mapping
                </span>
              </li>
            )}
            <li className="flex items-start gap-2">
              <Check className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
              <span>
                Mark {sourceMarket.source} market{' '}
                <code className="rounded bg-muted px-1 py-0.5 font-mono text-xs">
                  {sourceMarket.marketName || sourceMarket.externalMarketId}
                </code>{' '}
                as <Badge variant="secondary" className="text-[10px]">MAPPED</Badge>
              </span>
            </li>
          </ul>
        </CardContent>
      </Card>

      {/* Outcome Preview Table */}
      {outcomes.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">
              Outcome Mappings ({outcomes.length})
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="max-h-40 overflow-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="h-8 text-xs">Pos</TableHead>
                    <TableHead className="h-8 text-xs">Canonical ID</TableHead>
                    <TableHead className="h-8 text-xs">Betpawa</TableHead>
                    <TableHead className="h-8 text-xs">SportyBet</TableHead>
                    <TableHead className="h-8 text-xs">Bet9ja</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {outcomes.map((outcome, idx) => (
                    <TableRow key={idx}>
                      <TableCell className="py-1.5 text-xs">
                        {outcome.position}
                      </TableCell>
                      <TableCell className="py-1.5">
                        <code className="text-xs font-mono">
                          {outcome.canonicalId || '-'}
                        </code>
                      </TableCell>
                      <TableCell className="py-1.5 text-xs">
                        {outcome.betpawaName || '-'}
                      </TableCell>
                      <TableCell className="py-1.5 text-xs">
                        {outcome.sportybetDesc || '-'}
                      </TableCell>
                      <TableCell className="py-1.5 text-xs">
                        {outcome.bet9jaSuffix || '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Warnings Section */}
      {warnings.length > 0 && (
        <Alert variant={hasErrors ? 'destructive' : 'default'}>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>
            {hasErrors ? 'Validation Errors' : 'Warnings'}
          </AlertTitle>
          <AlertDescription>
            <ul className="list-disc list-inside space-y-1 mt-2">
              {warnings.map((warning, idx) => (
                <li key={idx} className="text-sm">
                  {warning.message}
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}
    </div>
  )
}

/**
 * Check if the mapping form state is valid for submission.
 */
export function isValidForSubmission(
  formState: MappingFormState,
  outcomes: OutcomeFormItem[]
): boolean {
  const warnings = validateMapping(formState, outcomes, 'create')
  return !warnings.some((w) => w.type === 'error')
}
