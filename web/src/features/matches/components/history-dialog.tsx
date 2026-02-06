import { useState } from 'react'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { OddsLineChart } from './odds-line-chart'
import { MarginLineChart } from './margin-line-chart'
import { useOddsHistory } from '../hooks/use-odds-history'
import { useMarginHistory } from '../hooks/use-margin-history'

export interface HistoryDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  eventId: number
  marketId: string
  bookmakerSlug: string
  marketName: string
  bookmakerName: string
}

export function HistoryDialog({
  open,
  onOpenChange,
  eventId,
  marketId,
  bookmakerSlug,
  marketName,
  bookmakerName,
}: HistoryDialogProps) {
  const [activeTab, setActiveTab] = useState<'odds' | 'margin'>('odds')

  const oddsHistory = useOddsHistory({
    eventId,
    marketId,
    bookmakerSlug,
    enabled: open && activeTab === 'odds',
  })

  const marginHistory = useMarginHistory({
    eventId,
    marketId,
    bookmakerSlug,
    enabled: open && activeTab === 'margin',
  })

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {marketName} - {bookmakerName}
          </DialogTitle>
        </DialogHeader>

        <Tabs
          value={activeTab}
          onValueChange={(value) => setActiveTab(value as 'odds' | 'margin')}
        >
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="odds">Odds</TabsTrigger>
            <TabsTrigger value="margin">Margin</TabsTrigger>
          </TabsList>

          <TabsContent value="odds" className="mt-4">
            {oddsHistory.isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-[300px] w-full" />
              </div>
            ) : oddsHistory.error ? (
              <div className="flex flex-col items-center justify-center h-[300px] gap-4">
                <p className="text-destructive">
                  Failed to load odds history
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => oddsHistory.refetch()}
                >
                  Retry
                </Button>
              </div>
            ) : (
              <OddsLineChart
                data={oddsHistory.data?.history ?? []}
                showMargin={true}
              />
            )}
          </TabsContent>

          <TabsContent value="margin" className="mt-4">
            {marginHistory.isLoading ? (
              <div className="space-y-2">
                <Skeleton className="h-[200px] w-full" />
              </div>
            ) : marginHistory.error ? (
              <div className="flex flex-col items-center justify-center h-[200px] gap-4">
                <p className="text-destructive">
                  Failed to load margin history
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => marginHistory.refetch()}
                >
                  Retry
                </Button>
              </div>
            ) : (
              <MarginLineChart data={marginHistory.data?.history ?? []} />
            )}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}
