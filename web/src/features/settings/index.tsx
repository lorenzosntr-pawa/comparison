import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useSettings } from './hooks'
import { IntervalSelector, PlatformToggles, SchedulerControl } from './components'

export function Settings() {
  const { isLoading, error } = useSettings()

  if (error) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Settings</h1>
        <Card>
          <CardContent className="pt-6">
            <p className="text-destructive">
              Failed to load settings. Please try again later.
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Settings</h1>
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-32" />
                <Skeleton className="h-4 w-48" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-10 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Settings</h1>

      <div className="grid gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Scheduler Control</CardTitle>
            <CardDescription>
              Pause or resume the automatic odds scraping
            </CardDescription>
          </CardHeader>
          <CardContent>
            <SchedulerControl />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Scraping Interval</CardTitle>
            <CardDescription>
              Configure how frequently odds are fetched
            </CardDescription>
          </CardHeader>
          <CardContent>
            <IntervalSelector />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Platform Selection</CardTitle>
            <CardDescription>
              Enable or disable scraping for specific bookmakers
            </CardDescription>
          </CardHeader>
          <CardContent>
            <PlatformToggles />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
