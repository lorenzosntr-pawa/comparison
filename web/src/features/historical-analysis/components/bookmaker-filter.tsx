import { cn } from '@/lib/utils'

/** Brand colors for bookmakers */
export const BOOKMAKER_COLORS = {
  betpawa: '#3b82f6',    // Blue
  sportybet: '#22c55e',  // Green
  bet9ja: '#f97316',     // Orange
} as const

/** Tailwind classes for brand colors (for bg/text/border) */
const BOOKMAKER_CLASSES = {
  betpawa: {
    selected: 'bg-blue-500 text-white border-blue-500',
    unselected: 'bg-transparent text-blue-500 border-blue-500 hover:bg-blue-500/10',
  },
  sportybet: {
    selected: 'bg-green-500 text-white border-green-500',
    unselected: 'bg-transparent text-green-500 border-green-500 hover:bg-green-500/10',
  },
  bet9ja: {
    selected: 'bg-orange-500 text-white border-orange-500',
    unselected: 'bg-transparent text-orange-500 border-orange-500 hover:bg-orange-500/10',
  },
} as const

/** Bookmaker configuration */
const BOOKMAKERS = [
  { slug: 'betpawa', label: 'Betpawa' },
  { slug: 'sportybet', label: 'SportyBet' },
  { slug: 'bet9ja', label: 'Bet9ja' },
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
 * Uses pill-style buttons with brand colors.
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
      <div className="flex items-center gap-2">
        {BOOKMAKERS.map((bookmaker) => {
          const isSelected = selected.includes(bookmaker.slug)
          const isBetpawa = bookmaker.slug === 'betpawa'
          const classes = BOOKMAKER_CLASSES[bookmaker.slug as keyof typeof BOOKMAKER_CLASSES]

          return (
            <button
              key={bookmaker.slug}
              type="button"
              onClick={() => handleToggle(bookmaker.slug)}
              className={cn(
                'rounded-full px-3 py-1.5 text-sm font-medium border transition-colors',
                isSelected ? classes.selected : classes.unselected,
                isBetpawa ? 'cursor-default' : 'cursor-pointer'
              )}
            >
              {bookmaker.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}
