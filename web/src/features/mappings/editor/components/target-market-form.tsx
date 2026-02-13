import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import type { UnmappedMarketDetail } from '../hooks/use-unmapped-detail'

/**
 * Mapping detail response for pre-filling in extend mode.
 */
export interface MappingDetailResponse {
  canonicalId: string
  name: string
  betpawaId: string | null
  sportybetId: string | null
  bet9jaKey: string | null
  outcomeMapping: Array<{
    canonicalId: string
    betpawaName: string | null
    sportybetDesc: string | null
    bet9jaSuffix: string | null
    position: number
  }>
  source: 'code' | 'db'
  isActive: boolean
  priority: number
  createdAt: string | null
  updatedAt: string | null
}

/**
 * Form state for mapping configuration.
 */
export interface MappingFormState {
  canonicalId: string
  name: string
  betpawaId: string | null
  sportybetId: string | null
  bet9jaKey: string | null
  priority: number
}

interface TargetMarketFormProps {
  mode: 'create' | 'extend'
  existingMapping?: MappingDetailResponse | null
  sourceMarket: UnmappedMarketDetail
  value: MappingFormState
  onChange: (value: MappingFormState) => void
}

/**
 * Generate canonical ID from name (lowercase, underscores for spaces).
 */
function generateCanonicalId(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '')
    .replace(/\s+/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '')
}

/**
 * TargetMarketForm component for mapping configuration.
 *
 * Displays form fields for:
 * - Canonical ID (editable in create mode, readonly in extend mode)
 * - Name (required)
 * - Platform IDs (Betpawa, SportyBet, Bet9ja)
 * - Priority (0-100)
 *
 * In extend mode, pre-fills from existingMapping.
 * In create mode, generates canonical_id suggestion from name.
 */
export function TargetMarketForm({
  mode,
  existingMapping,
  sourceMarket,
  value,
  onChange,
}: TargetMarketFormProps) {
  const handleFieldChange = (
    field: keyof MappingFormState,
    newValue: string | number | null
  ) => {
    const updated = { ...value, [field]: newValue }

    // In create mode, auto-generate canonical ID from name
    if (mode === 'create' && field === 'name' && typeof newValue === 'string') {
      updated.canonicalId = generateCanonicalId(newValue)
    }

    onChange(updated)
  }

  // Determine which platform IDs are already set (readonly in extend mode)
  const existingBetpawa = existingMapping?.betpawaId
  const existingSportybet = existingMapping?.sportybetId
  const existingBet9ja = existingMapping?.bet9jaKey

  return (
    <div className="space-y-4">
      {/* Canonical ID */}
      <div className="space-y-2">
        <Label htmlFor="canonicalId">
          Canonical ID
          {mode === 'extend' && (
            <Badge variant="outline" className="ml-2 text-[10px]">
              Read-only
            </Badge>
          )}
        </Label>
        <Input
          id="canonicalId"
          value={value.canonicalId}
          onChange={(e) => handleFieldChange('canonicalId', e.target.value)}
          placeholder="e.g., match_result_1x2"
          disabled={mode === 'extend'}
          className={mode === 'extend' ? 'bg-muted' : ''}
        />
        {mode === 'create' && (
          <p className="text-xs text-muted-foreground">
            Auto-generated from name. Use lowercase with underscores.
          </p>
        )}
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
        <div className="flex items-center gap-2">
          <Label className="text-sm font-medium">Platform IDs</Label>
          <span className="text-xs text-muted-foreground">
            (fill in for platforms you want to map)
          </span>
        </div>

        {/* Betpawa ID */}
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Label htmlFor="betpawaId" className="text-sm">
              Betpawa ID
            </Label>
            {existingBetpawa && mode === 'extend' && (
              <Badge variant="secondary" className="text-[10px]">
                From existing
              </Badge>
            )}
            {sourceMarket.source === 'betpawa' && (
              <Badge variant="outline" className="text-[10px]">
                Source platform
              </Badge>
            )}
          </div>
          <Input
            id="betpawaId"
            value={value.betpawaId || ''}
            onChange={(e) =>
              handleFieldChange('betpawaId', e.target.value || null)
            }
            placeholder="e.g., 1"
            disabled={mode === 'extend' && !!existingBetpawa}
            className={
              mode === 'extend' && !!existingBetpawa ? 'bg-muted' : ''
            }
          />
        </div>

        {/* SportyBet ID */}
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Label htmlFor="sportybetId" className="text-sm">
              SportyBet ID
            </Label>
            {existingSportybet && mode === 'extend' && (
              <Badge variant="secondary" className="text-[10px]">
                From existing
              </Badge>
            )}
            {sourceMarket.source === 'sportybet' && (
              <Badge variant="outline" className="text-[10px]">
                Source platform
              </Badge>
            )}
          </div>
          <Input
            id="sportybetId"
            value={value.sportybetId || ''}
            onChange={(e) =>
              handleFieldChange('sportybetId', e.target.value || null)
            }
            placeholder="e.g., 1"
            disabled={mode === 'extend' && !!existingSportybet}
            className={
              mode === 'extend' && !!existingSportybet ? 'bg-muted' : ''
            }
          />
        </div>

        {/* Bet9ja Key */}
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Label htmlFor="bet9jaKey" className="text-sm">
              Bet9ja Key
            </Label>
            {existingBet9ja && mode === 'extend' && (
              <Badge variant="secondary" className="text-[10px]">
                From existing
              </Badge>
            )}
            {sourceMarket.source === 'bet9ja' && (
              <Badge variant="outline" className="text-[10px]">
                Source platform
              </Badge>
            )}
          </div>
          <Input
            id="bet9jaKey"
            value={value.bet9jaKey || ''}
            onChange={(e) =>
              handleFieldChange('bet9jaKey', e.target.value || null)
            }
            placeholder="e.g., FT_1X2"
            disabled={mode === 'extend' && !!existingBet9ja}
            className={mode === 'extend' && !!existingBet9ja ? 'bg-muted' : ''}
          />
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
          Higher priority mappings override lower ones. User mappings default to
          10.
        </p>
      </div>
    </div>
  )
}

/**
 * Create initial form state for create mode.
 */
export function createInitialFormState(
  sourceMarket: UnmappedMarketDetail
): MappingFormState {
  const name = sourceMarket.marketName || ''
  const canonicalId = generateCanonicalId(name)

  // Auto-fill platform ID from source market
  let betpawaId: string | null = null
  let sportybetId: string | null = null
  let bet9jaKey: string | null = null

  if (sourceMarket.source === 'betpawa') {
    betpawaId = sourceMarket.externalMarketId
  } else if (sourceMarket.source === 'sportybet') {
    sportybetId = sourceMarket.externalMarketId
  } else if (sourceMarket.source === 'bet9ja') {
    bet9jaKey = sourceMarket.externalMarketId
  }

  return {
    canonicalId,
    name,
    betpawaId,
    sportybetId,
    bet9jaKey,
    priority: 10,
  }
}

/**
 * Create form state from existing mapping for extend mode.
 */
export function createExtendFormState(
  existingMapping: MappingDetailResponse,
  sourceMarket: UnmappedMarketDetail
): MappingFormState {
  // Start with existing mapping values
  let betpawaId = existingMapping.betpawaId
  let sportybetId = existingMapping.sportybetId
  let bet9jaKey = existingMapping.bet9jaKey

  // Add source market ID if not already set
  if (sourceMarket.source === 'betpawa' && !betpawaId) {
    betpawaId = sourceMarket.externalMarketId
  } else if (sourceMarket.source === 'sportybet' && !sportybetId) {
    sportybetId = sourceMarket.externalMarketId
  } else if (sourceMarket.source === 'bet9ja' && !bet9jaKey) {
    bet9jaKey = sourceMarket.externalMarketId
  }

  return {
    canonicalId: existingMapping.canonicalId,
    name: existingMapping.name,
    betpawaId,
    sportybetId,
    bet9jaKey,
    priority: existingMapping.priority,
  }
}
