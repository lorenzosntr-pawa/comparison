import { Home, BarChart3, Settings, Activity, History, GitCompare, TrendingUp } from 'lucide-react'
import { NavLink, useLocation } from 'react-router'
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
import { Badge } from '@/components/ui/badge'
import { useCoverage } from '@/features/coverage/hooks'
import { useHealth, useSchedulerStatus } from '@/features/dashboard/hooks'
import { cn } from '@/lib/utils'

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
  const { data: coverage } = useCoverage()
  const { data: health } = useHealth()
  const { data: scheduler } = useSchedulerStatus()

  const dbHealthy = health?.status === 'healthy'
  const schedulerRunning = scheduler?.running ?? false
  const schedulerPaused = scheduler?.paused ?? false
  const schedulerHealthy = schedulerRunning && !schedulerPaused

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
            <div className="px-2 space-y-2 text-xs text-muted-foreground">
              <div className="flex items-center justify-between">
                <span>Events</span>
                <Badge variant="secondary" className="text-xs h-5 px-1.5">
                  {coverage?.total_events ?? '-'}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span>System</span>
                <div className="flex gap-1.5">
                  <span
                    className={cn(
                      'h-2 w-2 rounded-full',
                      dbHealthy ? 'bg-green-500' : 'bg-red-500'
                    )}
                    title="Database"
                  />
                  <span
                    className={cn(
                      'h-2 w-2 rounded-full',
                      schedulerHealthy
                        ? 'bg-green-500'
                        : schedulerPaused
                          ? 'bg-yellow-500'
                          : 'bg-gray-500'
                    )}
                    title="Scheduler"
                  />
                </div>
              </div>
            </div>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  )
}
