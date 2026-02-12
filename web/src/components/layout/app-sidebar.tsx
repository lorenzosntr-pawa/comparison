import { useState, useEffect } from 'react'
import { Home, BarChart3, Settings, Activity, History, GitCompare, TrendingUp, Check, X, Clock, Wifi, WifiOff, Loader2, Play, Timer } from 'lucide-react'
import { NavLink, useLocation } from 'react-router'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from '@/components/ui/sidebar'
import { Button } from '@/components/ui/button'
import { useCoverage } from '@/features/coverage/hooks'
import { useHealth, useSchedulerStatus, useActiveScrapesObserver } from '@/features/dashboard/hooks'
import { useScrapeRuns } from '@/features/scrape-runs/hooks'
import { api } from '@/lib/api'
import { cn } from '@/lib/utils'
import { formatDistanceToNow, differenceInSeconds } from 'date-fns'

const navItems = [
  { title: 'Odds Comparison', url: '/', icon: BarChart3 },
  { title: 'Coverage', url: '/coverage', icon: GitCompare },
  { title: 'Historical Analysis', url: '/historical-analysis', icon: TrendingUp },
  { title: 'Dashboard', url: '/dashboard', icon: Home },
  { title: 'Scrape Runs', url: '/scrape-runs', icon: History },
  { title: 'Settings', url: '/settings', icon: Settings },
]

export function AppSidebar() {
  const location = useLocation()
  const queryClient = useQueryClient()
  const { data: coverage } = useCoverage()
  const { data: health } = useHealth()
  const { data: scheduler } = useSchedulerStatus()
  const { data: recentRuns } = useScrapeRuns(1, 0)
  const { activeScrapeId, overallPhase, connectionState } = useActiveScrapesObserver()

  const triggerScrape = useMutation({
    mutationFn: () => api.triggerScrape(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scrapeRuns'] })
    },
  })

  const dbHealthy = health?.database === 'connected'
  const schedulerRunning = scheduler?.running ?? false
  const schedulerPaused = scheduler?.paused ?? false

  const lastRun = recentRuns?.[0]
  const lastRunTime = lastRun?.started_at
    ? formatDistanceToNow(new Date(lastRun.started_at), { addSuffix: true })
    : null

  // Countdown to next scrape
  const nextRun = scheduler?.jobs?.[0]?.next_run
  const [countdown, setCountdown] = useState<string | null>(null)

  useEffect(() => {
    if (!nextRun || schedulerPaused || !schedulerRunning) {
      setCountdown(null)
      return
    }

    const updateCountdown = () => {
      const seconds = differenceInSeconds(new Date(nextRun), new Date())
      if (seconds <= 0) {
        setCountdown('Now')
        return
      }
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      if (mins >= 60) {
        const hours = Math.floor(mins / 60)
        const remainingMins = mins % 60
        setCountdown(`${hours}h ${remainingMins}m`)
      } else if (mins > 0) {
        setCountdown(`${mins}m ${secs}s`)
      } else {
        setCountdown(`${secs}s`)
      }
    }

    updateCountdown()
    const interval = setInterval(updateCountdown, 1000)
    return () => clearInterval(interval)
  }, [nextRun, schedulerPaused, schedulerRunning])

  return (
    <Sidebar collapsible="offcanvas">
      <SidebarHeader className="border-b border-sidebar-border">
        <div className="flex items-center gap-2 px-2 py-2">
          <Activity className="h-6 w-6 text-primary" />
          <span className="font-bold text-lg group-data-[collapsible=icon]:hidden">
            pawaRisk
          </span>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {navItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton
                    asChild
                    isActive={location.pathname === item.url}
                    tooltip={item.title}
                  >
                    <NavLink to={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
        <SidebarGroup className="group-data-[collapsible=icon]:hidden">
          <SidebarGroupLabel>Status</SidebarGroupLabel>
          <SidebarGroupContent>
            <div className="px-2 space-y-3 text-xs">
              {/* Events - total and matched */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-muted-foreground">
                  <span>Events</span>
                  <span className="font-medium text-foreground">
                    {coverage?.total_events ?? '-'} total
                  </span>
                </div>
                <div className="flex items-center justify-between text-muted-foreground">
                  <span className="pl-2">Matched</span>
                  <span className="font-medium text-foreground">
                    {coverage?.matched_count ?? '-'}
                  </span>
                </div>
              </div>

              {/* System health */}
              <div className="space-y-1">
                <div className="flex items-center justify-between text-muted-foreground">
                  <span>Database</span>
                  <span className={cn(
                    'flex items-center gap-1 font-medium',
                    dbHealthy ? 'text-green-600' : 'text-red-600'
                  )}>
                    {dbHealthy ? (
                      <>
                        <Check className="h-3 w-3" />
                        OK
                      </>
                    ) : (
                      <>
                        <X className="h-3 w-3" />
                        Error
                      </>
                    )}
                  </span>
                </div>
                <div className="flex items-center justify-between text-muted-foreground">
                  <span>Scheduler</span>
                  <span className={cn(
                    'font-medium',
                    schedulerRunning && !schedulerPaused
                      ? 'text-green-600'
                      : schedulerPaused
                        ? 'text-yellow-600'
                        : 'text-muted-foreground'
                  )}>
                    {schedulerRunning && !schedulerPaused
                      ? 'Running'
                      : schedulerPaused
                        ? 'Paused'
                        : 'Stopped'}
                  </span>
                </div>
                <div className="flex items-center justify-between text-muted-foreground">
                  <span>WebSocket</span>
                  <span className={cn(
                    'flex items-center gap-1 font-medium',
                    connectionState === 'connected'
                      ? 'text-green-600'
                      : connectionState === 'connecting'
                        ? 'text-yellow-600'
                        : 'text-red-600'
                  )}>
                    {connectionState === 'connected' ? (
                      <>
                        <Wifi className="h-3 w-3" />
                        OK
                      </>
                    ) : connectionState === 'connecting' ? (
                      <>
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Connecting
                      </>
                    ) : (
                      <>
                        <WifiOff className="h-3 w-3" />
                        Disconnected
                      </>
                    )}
                  </span>
                </div>
                <div className="flex items-center justify-between text-muted-foreground">
                  <span>Next Scrape</span>
                  <span className="font-medium text-foreground flex items-center gap-1">
                    <Timer className="h-3 w-3" />
                    {schedulerPaused
                      ? 'Paused'
                      : !schedulerRunning
                        ? '-'
                        : countdown ?? '-'}
                  </span>
                </div>
              </div>

              {/* Active scrape (when running) */}
              {activeScrapeId !== null && (
                <div className="space-y-1 pt-1 border-t border-sidebar-border">
                  <div className="flex items-center justify-between text-muted-foreground">
                    <span>Active Scrape</span>
                    <span className="font-medium text-blue-600 flex items-center gap-1">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      In Progress
                    </span>
                  </div>
                  {overallPhase && (
                    <div className="flex items-center justify-between text-muted-foreground">
                      <span className="pl-2">Phase</span>
                      <span className="font-medium text-foreground">
                        {overallPhase}
                      </span>
                    </div>
                  )}
                </div>
              )}

              {/* Last scrape run */}
              {lastRun && (
                <div className="space-y-1 pt-1 border-t border-sidebar-border">
                  <div className="flex items-center justify-between text-muted-foreground">
                    <span>Last Scrape</span>
                    <span className="font-medium text-foreground flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {lastRunTime}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-muted-foreground">
                    <span className="pl-2">Status</span>
                    <span className={cn(
                      'font-medium',
                      lastRun.status === 'completed'
                        ? 'text-green-600'
                        : lastRun.status === 'failed'
                          ? 'text-red-600'
                          : lastRun.status === 'running'
                            ? 'text-blue-600'
                            : 'text-yellow-600'
                    )}>
                      {lastRun.status === 'completed' ? 'OK' :
                       lastRun.status === 'running' ? 'In Progress' :
                       lastRun.status.charAt(0).toUpperCase() + lastRun.status.slice(1)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-muted-foreground">
                    <span className="pl-2">Events</span>
                    <span className="font-medium text-foreground">
                      {lastRun.events_scraped}
                    </span>
                  </div>
                </div>
              )}

              {/* Manual scrape button */}
              <div className="pt-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="w-full"
                  disabled={activeScrapeId !== null || triggerScrape.isPending}
                  onClick={() => triggerScrape.mutate()}
                >
                  {triggerScrape.isPending ? (
                    <Loader2 className="h-3 w-3 animate-spin mr-1" />
                  ) : (
                    <Play className="h-3 w-3 mr-1" />
                  )}
                  Run Scrape
                </Button>
              </div>
            </div>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  )
}
