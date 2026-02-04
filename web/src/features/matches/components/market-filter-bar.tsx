import { Search } from 'lucide-react'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'

interface MarketFilterBarProps {
  searchQuery: string
  onSearchChange: (query: string) => void
  selectedCompetitor: string | null
  onCompetitorChange: (competitor: string | null) => void
}

export function MarketFilterBar({
  searchQuery,
  onSearchChange,
  selectedCompetitor,
  onCompetitorChange,
}: MarketFilterBarProps) {
  return (
    <div className="flex flex-row gap-3 items-center mb-4">
      <div className="relative flex-1 max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search markets..."
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          className="pl-9"
        />
      </div>

      <Select
        value={selectedCompetitor ?? 'none'}
        onValueChange={(value) =>
          onCompetitorChange(value === 'none' ? null : value)
        }
      >
        <SelectTrigger className="w-[160px]">
          <SelectValue placeholder="Compare with..." />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="none">None</SelectItem>
          <SelectItem value="sportybet">vs SportyBet</SelectItem>
          <SelectItem value="bet9ja">vs Bet9ja</SelectItem>
        </SelectContent>
      </Select>
    </div>
  )
}
