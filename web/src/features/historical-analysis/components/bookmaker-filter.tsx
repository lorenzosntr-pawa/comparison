import { Button } from '@/components/ui/button'

/** Brand colors for bookmakers */
export const BOOKMAKER_COLORS = {
  betpawa: '#3b82f6',    // Blue
  sportybet: '#22c55e',  // Green
  bet9ja: '#f97316',     // Orange
} as const

/** Bookmaker configuration */
const BOOKMAKERS = [
  { slug: 'betpawa', label: 'Betpawa', color: BOOKMAKER_COLORS.betpawa },
  { slug: 'sportybet', label: 'SportyBet', color: BOOKMAKER_COLORS.sportybet },
  { slug: 'bet9ja', label: 'Bet9ja', color: BOOKMAKER_COLORS.bet9ja },
] as const

interface BookmakerFilterProps {
  /** Currently selected bookmakers (always includes 'betpawa') */
  selected: string[]
  /** Callback when selection changes */
  onChange: (selected: string[]) => void
}

/**
 * Toggle buttons for selecting which bookmakers to display in comparisons.
 * Betpawa is always enabled as the reference bookmaker.
 */
export function BookmakerFilter({ selected, onChange }: BookmakerFilterProps) {
  const handleToggle = (slug: string) => {
    // Betpawa cannot be toggled off
    if (slug === 'betpawa') return

    if (selected.includes(slug)) {
      onChange(selected.filter((s) => s !== slug))
    } else {
      onChange([...selected, slug])
    }
  }

  return (
    <div className="flex flex-col gap-1.5">
      <label className="text-xs font-medium text-muted-foreground">
        Bookmakers
      </label>
      <div className="flex items-center gap-1">
        {BOOKMAKERS.map((bookmaker) => {
          const isSelected = selected.includes(bookmaker.slug)
          const isBetpawa = bookmaker.slug === 'betpawa'

          return (
            <Button
              key={bookmaker.slug}
              variant={isSelected ? 'default' : 'outline'}
              size="sm"
              onClick={() => handleToggle(bookmaker.slug)}
              className={`h-9 px-3 text-xs ${isBetpawa ? 'cursor-default' : ''}`}
              disabled={isBetpawa}
            >
              <span
                className="w-2 h-2 rounded-full mr-1.5"
                style={{ backgroundColor: bookmaker.color }}
              />
              {bookmaker.label}
            </Button>
          )
        })}
      </div>
    </div>
  )
}
