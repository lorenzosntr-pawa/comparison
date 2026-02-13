import { Plus, Trash2, ChevronUp, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  createEmptyOutcomeItem,
  type OutcomeFormItem,
} from '../utils/outcome-suggest'

type SourcePlatform = 'sportybet' | 'bet9ja'

interface OutcomeMappingTableProps {
  /** Current outcome mappings */
  outcomes: OutcomeFormItem[]
  /** Callback when outcomes change */
  onChange: (outcomes: OutcomeFormItem[]) => void
  /** Source platform to highlight the relevant column */
  sourcePlatform: SourcePlatform
}

/**
 * OutcomeMappingTable component for editing outcome mappings.
 *
 * Features:
 * - Editable cells for all outcome fields
 * - Add/remove outcome rows
 * - Reorder via up/down buttons
 * - Highlights source platform column
 */
export function OutcomeMappingTable({
  outcomes,
  onChange,
  sourcePlatform,
}: OutcomeMappingTableProps) {
  /**
   * Update a single field in an outcome row.
   */
  const handleFieldChange = (
    index: number,
    field: keyof OutcomeFormItem,
    value: string | number | null
  ) => {
    const updated = [...outcomes]
    updated[index] = { ...updated[index], [field]: value }
    onChange(updated)
  }

  /**
   * Add a new empty row at the end.
   */
  const handleAddRow = () => {
    const newPosition = outcomes.length
    onChange([...outcomes, createEmptyOutcomeItem(newPosition)])
  }

  /**
   * Remove a row by index.
   */
  const handleRemoveRow = (index: number) => {
    if (outcomes.length <= 1) {
      // Don't remove last row - at least one outcome required
      return
    }
    const updated = outcomes
      .filter((_, i) => i !== index)
      .map((item, i) => ({ ...item, position: i })) // Renumber positions
    onChange(updated)
  }

  /**
   * Move a row up (decrease position).
   */
  const handleMoveUp = (index: number) => {
    if (index === 0) return
    const updated = [...outcomes]
    // Swap with previous
    const temp = updated[index]
    updated[index] = { ...updated[index - 1], position: index }
    updated[index - 1] = { ...temp, position: index - 1 }
    onChange(updated)
  }

  /**
   * Move a row down (increase position).
   */
  const handleMoveDown = (index: number) => {
    if (index === outcomes.length - 1) return
    const updated = [...outcomes]
    // Swap with next
    const temp = updated[index]
    updated[index] = { ...updated[index + 1], position: index }
    updated[index + 1] = { ...temp, position: index + 1 }
    onChange(updated)
  }

  /**
   * Get highlight class for source platform columns.
   */
  const getColumnHighlight = (platform: 'sportybet' | 'bet9ja') => {
    return sourcePlatform === platform ? 'bg-accent/50' : ''
  }

  return (
    <div className="space-y-3">
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[60px]">Pos</TableHead>
              <TableHead className="min-w-[120px]">Canonical ID</TableHead>
              <TableHead className="min-w-[100px]">Betpawa Name</TableHead>
              <TableHead
                className={`min-w-[120px] ${getColumnHighlight('sportybet')}`}
              >
                SportyBet Desc
              </TableHead>
              <TableHead
                className={`min-w-[100px] ${getColumnHighlight('bet9ja')}`}
              >
                Bet9ja Suffix
              </TableHead>
              <TableHead className="w-[100px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {outcomes.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="h-24 text-center">
                  <span className="text-muted-foreground">
                    No outcomes defined. Click "Add Outcome" to add one.
                  </span>
                </TableCell>
              </TableRow>
            ) : (
              outcomes.map((outcome, index) => (
                <TableRow key={index}>
                  {/* Position with reorder buttons */}
                  <TableCell className="p-2">
                    <div className="flex flex-col items-center gap-0.5">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-5 w-5"
                        onClick={() => handleMoveUp(index)}
                        disabled={index === 0}
                      >
                        <ChevronUp className="h-3 w-3" />
                      </Button>
                      <span className="text-xs text-muted-foreground">
                        {index}
                      </span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="h-5 w-5"
                        onClick={() => handleMoveDown(index)}
                        disabled={index === outcomes.length - 1}
                      >
                        <ChevronDown className="h-3 w-3" />
                      </Button>
                    </div>
                  </TableCell>

                  {/* Canonical ID */}
                  <TableCell className="p-2">
                    <Input
                      value={outcome.canonicalId}
                      onChange={(e) =>
                        handleFieldChange(index, 'canonicalId', e.target.value)
                      }
                      placeholder="e.g., home"
                      className="h-8 text-sm"
                    />
                  </TableCell>

                  {/* Betpawa Name */}
                  <TableCell className="p-2">
                    <Input
                      value={outcome.betpawaName || ''}
                      onChange={(e) =>
                        handleFieldChange(
                          index,
                          'betpawaName',
                          e.target.value || null
                        )
                      }
                      placeholder="e.g., 1"
                      className="h-8 text-sm"
                    />
                  </TableCell>

                  {/* SportyBet Desc */}
                  <TableCell
                    className={`p-2 ${getColumnHighlight('sportybet')}`}
                  >
                    <Input
                      value={outcome.sportybetDesc || ''}
                      onChange={(e) =>
                        handleFieldChange(
                          index,
                          'sportybetDesc',
                          e.target.value || null
                        )
                      }
                      placeholder="e.g., Home"
                      className="h-8 text-sm"
                    />
                  </TableCell>

                  {/* Bet9ja Suffix */}
                  <TableCell className={`p-2 ${getColumnHighlight('bet9ja')}`}>
                    <Input
                      value={outcome.bet9jaSuffix || ''}
                      onChange={(e) =>
                        handleFieldChange(
                          index,
                          'bet9jaSuffix',
                          e.target.value || null
                        )
                      }
                      placeholder="e.g., 1"
                      className="h-8 text-sm"
                    />
                  </TableCell>

                  {/* Actions */}
                  <TableCell className="p-2">
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      onClick={() => handleRemoveRow(index)}
                      disabled={outcomes.length <= 1}
                      title={
                        outcomes.length <= 1
                          ? 'At least one outcome required'
                          : 'Remove outcome'
                      }
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>

      {/* Add row button */}
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="w-full"
        onClick={handleAddRow}
      >
        <Plus className="mr-2 h-4 w-4" />
        Add Outcome
      </Button>
    </div>
  )
}
