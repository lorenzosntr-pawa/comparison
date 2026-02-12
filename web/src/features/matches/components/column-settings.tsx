import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'
import { Separator } from '@/components/ui/separator'
import { Settings2 } from 'lucide-react'
import { AVAILABLE_COLUMNS } from '../hooks/use-column-settings'

interface ColumnSettingsProps {
  visibleColumns: string[]
  onToggleColumn: (columnId: string) => void
  onShowAll: () => void
  onHideAll: () => void
  onResetWidths?: () => void
}

export function ColumnSettings({
  visibleColumns,
  onToggleColumn,
  onShowAll,
  onHideAll,
  onResetWidths,
}: ColumnSettingsProps) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="h-9">
          <Settings2 className="w-4 h-4 mr-2" />
          Columns
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-56" align="end">
        <div className="space-y-4">
          <div className="font-medium text-sm">Visible Columns</div>

          <div className="space-y-2">
            {AVAILABLE_COLUMNS.map((column) => {
              const isVisible = visibleColumns.includes(column.id)
              const isLastOne = visibleColumns.length === 1 && isVisible

              return (
                <div key={column.id} className="flex items-center space-x-2">
                  <Checkbox
                    id={`column-${column.id}`}
                    checked={isVisible}
                    onCheckedChange={() => onToggleColumn(column.id)}
                    disabled={isLastOne}
                  />
                  <label
                    htmlFor={`column-${column.id}`}
                    className="text-sm cursor-pointer flex-1"
                  >
                    {column.label}
                  </label>
                </div>
              )
            })}
          </div>

          <Separator />

          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onShowAll}
              className="flex-1"
            >
              Show all
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={onHideAll}
              className="flex-1"
            >
              Hide all
            </Button>
          </div>

          {onResetWidths && (
            <>
              <Separator />
              <Button
                variant="ghost"
                size="sm"
                onClick={onResetWidths}
                className="w-full text-muted-foreground"
              >
                Reset column widths
              </Button>
            </>
          )}
        </div>
      </PopoverContent>
    </Popover>
  )
}
