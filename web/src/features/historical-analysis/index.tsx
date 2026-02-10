import { useState } from 'react'
import { subDays } from 'date-fns'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { FilterBar, type DateRange } from './components'

export function HistoricalAnalysisPage() {
  // Default to last 7 days
  const [dateRange, setDateRange] = useState<DateRange>(() => {
    const today = new Date()
    today.setHours(23, 59, 59, 999)
    const from = subDays(today, 7)
    from.setHours(0, 0, 0, 0)
    return { from, to: today }
  })

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Historical Analysis</h1>

      <FilterBar dateRange={dateRange} onDateRangeChange={setDateRange} />

      <Card>
        <CardHeader>
          <CardTitle>Tournament Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            Tournament analysis coming in Phase 84
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
