# Phase 6: React Foundation - Research

**Researched:** 2026-01-20
**Domain:** React 19 + Vite + TanStack Query + Tailwind v4 + shadcn/ui
**Confidence:** HIGH

<research_summary>
## Summary

Researched the modern React ecosystem for building a data-dense dashboard application with collapsible sidebar, dark/light themes, and API integration. The standard 2026 stack is React 19 + Vite + TypeScript + TanStack Query v5 + Tailwind v4 + shadcn/ui.

Key finding: shadcn/ui provides a complete sidebar component with built-in icon-collapse mode (`collapsible="icon"`), eliminating custom implementation. The ThemeProvider pattern handles dark/light mode with localStorage persistence. TanStack Query v5 renamed `cacheTime` to `gcTime` and `isLoading` to `isPending`.

**Primary recommendation:** Use Vite's react-ts template, upgrade to React 19, initialize shadcn/ui with Tailwind v4, and leverage shadcn's built-in sidebar component for navigation. Feature-based folder structure (src/features/ + src/components/) for scalability.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react | 19.x | UI framework | Latest with compiler optimizations |
| react-dom | 19.x | DOM rendering | Required for web |
| vite | 7.x | Build tool | Fast dev, optimized builds, modern defaults |
| typescript | 5.x | Type safety | Industry standard |

### Data & Routing
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| @tanstack/react-query | 5.90.x | Server state management | Caching, background updates, stale-while-revalidate |
| react-router | 7.x | Client-side routing | Standard React router, v7 is stable |

### UI & Styling
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tailwindcss | 4.x | Utility CSS | CSS variables, dark mode built-in |
| @tailwindcss/vite | 4.x | Vite plugin | Required for Tailwind v4 |
| shadcn/ui | latest | Component library | Composable, accessible, includes sidebar |
| lucide-react | latest | Icons | Default shadcn icons, comprehensive set |

### Dev Tools
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @tanstack/react-query-devtools | 5.x | Query debugging | Development only |
| eslint | 9.x | Linting | Code quality |
| @typescript-eslint/* | latest | TS linting | TypeScript rules |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| shadcn/ui | Radix primitives only | More control but more work |
| TanStack Query | SWR | TQ has better devtools, more features |
| React Router | TanStack Router | TanStack Router newer, React Router more mature |
| Vite | Next.js | Next.js if SSR needed, Vite simpler for SPA |

**Installation:**
```bash
# Create project
pnpm create vite@latest web --template react-ts
cd web

# Upgrade to React 19
pnpm install react@19 react-dom@19
pnpm install -D @types/react@19 @types/react-dom@19

# Install Tailwind v4
pnpm install -D tailwindcss@latest @tailwindcss/vite@latest

# Install data/routing
pnpm install @tanstack/react-query react-router

# Dev tools
pnpm install -D @tanstack/react-query-devtools @types/node

# Initialize shadcn (after Tailwind setup)
npx shadcn@latest init
```
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### Recommended Project Structure
```
web/
├── src/
│   ├── components/           # Shared/reusable components
│   │   ├── ui/              # shadcn components (auto-generated)
│   │   ├── layout/          # Layout components (Sidebar, Header)
│   │   └── shared/          # App-wide shared components
│   ├── features/            # Feature-based modules
│   │   ├── dashboard/       # Dashboard feature
│   │   ├── matches/         # Match list/detail feature
│   │   └── settings/        # Settings feature
│   ├── hooks/               # Custom hooks
│   ├── lib/                 # Utilities, API client
│   ├── types/               # TypeScript types
│   ├── App.tsx              # Root component with providers
│   ├── main.tsx             # Entry point
│   └── index.css            # Global styles + Tailwind
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tsconfig.app.json
└── components.json          # shadcn config
```

### Pattern 1: Provider Stack
**What:** Wrap app with required providers in correct order
**When to use:** Always - at app root
**Example:**
```typescript
// src/App.tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { BrowserRouter } from 'react-router'
import { ThemeProvider } from '@/components/theme-provider'
import { SidebarProvider } from '@/components/ui/sidebar'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,  // 5 minutes
      gcTime: 1000 * 60 * 10,    // 10 minutes (was cacheTime in v4)
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ThemeProvider defaultTheme="system" storageKey="betpawa-theme">
          <SidebarProvider>
            <AppLayout />
          </SidebarProvider>
        </ThemeProvider>
      </BrowserRouter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  )
}
```

### Pattern 2: shadcn Sidebar with Icon Collapse
**What:** Use shadcn's built-in collapsible sidebar
**When to use:** Navigation with icon-collapse mode
**Example:**
```typescript
// src/components/layout/app-sidebar.tsx
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarFooter,
} from '@/components/ui/sidebar'
import { Home, List, Settings, Activity } from 'lucide-react'

const items = [
  { title: 'Dashboard', url: '/', icon: Home },
  { title: 'Matches', url: '/matches', icon: List },
  { title: 'Settings', url: '/settings', icon: Settings },
]

export function AppSidebar() {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader>
        <span className="font-bold">Betpawa Odds</span>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <a href={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  )
}
```

### Pattern 3: TanStack Query Hook Pattern
**What:** Custom hooks wrapping useQuery for API calls
**When to use:** All API data fetching
**Example:**
```typescript
// src/features/dashboard/hooks/use-scheduler-status.ts
import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

export function useSchedulerStatus() {
  return useQuery({
    queryKey: ['scheduler', 'status'],
    queryFn: () => api.get('/scheduler/status'),
    refetchInterval: 30000, // Poll every 30s
  })
}

// Usage in component
function SchedulerCard() {
  const { data, isPending, error } = useSchedulerStatus()

  if (isPending) return <Skeleton />
  if (error) return <ErrorCard error={error} />

  return <StatusDisplay status={data} />
}
```

### Pattern 4: Theme Provider (shadcn standard)
**What:** Context-based theme management with localStorage
**When to use:** Dark/light mode support
**Example:**
```typescript
// src/components/theme-provider.tsx
import { createContext, useContext, useEffect, useState } from 'react'

type Theme = 'dark' | 'light' | 'system'

const ThemeContext = createContext<{
  theme: Theme
  setTheme: (theme: Theme) => void
}>({ theme: 'system', setTheme: () => null })

export function ThemeProvider({
  children,
  defaultTheme = 'system',
  storageKey = 'ui-theme',
}: {
  children: React.ReactNode
  defaultTheme?: Theme
  storageKey?: string
}) {
  const [theme, setTheme] = useState<Theme>(
    () => (localStorage.getItem(storageKey) as Theme) || defaultTheme
  )

  useEffect(() => {
    const root = window.document.documentElement
    root.classList.remove('light', 'dark')

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
        ? 'dark'
        : 'light'
      root.classList.add(systemTheme)
    } else {
      root.classList.add(theme)
    }
  }, [theme])

  const value = {
    theme,
    setTheme: (theme: Theme) => {
      localStorage.setItem(storageKey, theme)
      setTheme(theme)
    },
  }

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export const useTheme = () => useContext(ThemeContext)
```

### Anti-Patterns to Avoid
- **Fetching in useEffect:** Use TanStack Query instead for caching/deduplication
- **Prop drilling theme:** Use ThemeProvider context
- **Custom sidebar collapse logic:** Use shadcn's built-in `collapsible="icon"`
- **Inline styles:** Use Tailwind utilities
- **Large components:** Split into smaller, focused components
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Collapsible sidebar | Custom collapse/expand logic | shadcn Sidebar with `collapsible="icon"` | Built-in, accessible, keyboard shortcuts |
| Data fetching | useEffect + useState | TanStack Query useQuery | Caching, deduplication, background refetch |
| Dark mode | Manual class toggling | shadcn ThemeProvider pattern | localStorage, system detection, transitions |
| Data tables | Custom table from scratch | shadcn Table + TanStack Table | Accessibility, sorting, pagination ready |
| Dropdown menus | Custom positioning | shadcn DropdownMenu (Radix) | Keyboard nav, portal, accessibility |
| Loading states | Custom spinners | shadcn Skeleton component | Consistent styling, easy to use |
| Status badges | Custom styled spans | shadcn Badge component | Variants, accessibility |
| Cards/panels | Custom divs | shadcn Card component | Consistent spacing, variants |

**Key insight:** shadcn/ui provides all the base components needed for this data-dense dashboard. The sidebar, table, card, and badge components are production-ready. Don't spend time building these from scratch.
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: TanStack Query v5 Naming Changes
**What goes wrong:** Using `isLoading` and `cacheTime` from v4 docs
**Why it happens:** Many tutorials/examples still use v4 syntax
**How to avoid:** Use `isPending` instead of `isLoading`, `gcTime` instead of `cacheTime`
**Warning signs:** TypeScript errors about unknown properties

### Pitfall 2: Tailwind v4 Config File
**What goes wrong:** Creating `tailwind.config.js` like v3
**Why it happens:** Old tutorials, muscle memory
**How to avoid:** Tailwind v4 uses CSS-based config, no JS config file. Use `@theme` in CSS.
**Warning signs:** Config file has no effect, dark mode doesn't work

### Pitfall 3: shadcn Component Import Paths
**What goes wrong:** Components not found after adding
**Why it happens:** Path alias not configured correctly in tsconfig
**How to avoid:** Add `@/*` alias to both `tsconfig.json` AND `tsconfig.app.json`
**Warning signs:** "Cannot find module '@/components/ui/button'"

### Pitfall 4: React Router v7 Import Changes
**What goes wrong:** Importing from 'react-router-dom'
**Why it happens:** v6 used 'react-router-dom', v7 merged into 'react-router'
**How to avoid:** Import everything from 'react-router', not 'react-router-dom'
**Warning signs:** Deprecation warnings, package not found

### Pitfall 5: Sidebar State Not Persisting
**What goes wrong:** Sidebar collapses on navigation
**Why it happens:** SidebarProvider not at correct level in component tree
**How to avoid:** SidebarProvider must wrap the entire layout, not just sidebar
**Warning signs:** Sidebar resets on route change

### Pitfall 6: Theme Flash on Load
**What goes wrong:** Light theme flashes before dark mode applies
**Why it happens:** Theme script runs after page paint
**How to avoid:** Add inline script in index.html to set class before render
**Warning signs:** Brief white flash when loading dark mode
</common_pitfalls>

<code_examples>
## Code Examples

### Vite Config with Path Aliases
```typescript
// vite.config.ts
import path from "path"
import tailwindcss from "@tailwindcss/vite"
import react from "@vitejs/plugin-react"
import { defineConfig } from "vite"

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### TypeScript Config for Path Aliases
```json
// tsconfig.json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}

// tsconfig.app.json - ALSO needs paths
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### API Client Setup
```typescript
// src/lib/api.ts
const API_BASE = '/api'

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status}`)
  }

  return response.json()
}

export const api = {
  get: <T>(url: string) => fetchJson<T>(url),
  post: <T>(url: string, data: unknown) =>
    fetchJson<T>(url, { method: 'POST', body: JSON.stringify(data) }),
}
```

### Route Configuration
```typescript
// src/routes.tsx
import { Routes, Route } from 'react-router'
import { Dashboard } from '@/features/dashboard'
import { MatchList, MatchDetail } from '@/features/matches'
import { Settings } from '@/features/settings'

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/matches" element={<MatchList />} />
      <Route path="/matches/:id" element={<MatchDetail />} />
      <Route path="/settings" element={<Settings />} />
    </Routes>
  )
}
```

### Mode Toggle Component
```typescript
// src/components/mode-toggle.tsx
import { Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useTheme } from '@/components/theme-provider'

export function ModeToggle() {
  const { setTheme } = useTheme()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon">
          <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">Toggle theme</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem onClick={() => setTheme('light')}>Light</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('dark')}>Dark</DropdownMenuItem>
        <DropdownMenuItem onClick={() => setTheme('system')}>System</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
```
</code_examples>

<sota_updates>
## State of the Art (2025-2026)

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tailwind config.js | Tailwind v4 CSS config | 2025 | No JS config, CSS variables for theming |
| react-router-dom | react-router (single package) | 2024 (v7) | Simpler imports |
| cacheTime | gcTime | 2024 (TQ v5) | Rename only, same behavior |
| isLoading | isPending | 2024 (TQ v5) | More accurate naming |
| Custom sidebar | shadcn Sidebar component | 2024 | Built-in collapse, keyboard shortcuts |
| Webpack/CRA | Vite | 2022+ | 10x faster dev server |

**New tools/patterns to consider:**
- **React 19 Compiler:** Auto-optimization, may reduce need for useMemo/useCallback
- **shadcn Sidebar:** Full-featured, replaces need for custom implementations
- **Tailwind v4 @theme:** CSS-based theming, better dark mode support

**Deprecated/outdated:**
- **Create React App:** Use Vite instead
- **tailwind.config.js:** Tailwind v4 uses CSS config
- **react-router-dom package:** Merged into react-router in v7
</sota_updates>

<open_questions>
## Open Questions

1. **React 19 Compiler Integration**
   - What we know: Vite has a plugin for React Compiler
   - What's unclear: Whether it's production-ready for all use cases
   - Recommendation: Start without compiler, add later if needed

2. **shadcn Windows Compatibility**
   - What we know: CLI has known issues on Windows
   - What's unclear: Which specific operations fail
   - Recommendation: Use WSL if issues occur, or manually copy component files
</open_questions>

<sources>
## Sources

### Primary (HIGH confidence)
- [Vite Getting Started](https://vite.dev/guide/) - Installation, config
- [TanStack Query Installation](https://tanstack.com/query/v5/docs/framework/react/installation) - Setup
- [TanStack Query Important Defaults](https://tanstack.com/query/v5/docs/react/guides/important-defaults) - gcTime/staleTime
- [shadcn/ui Sidebar](https://ui.shadcn.com/docs/components/sidebar) - Collapsible sidebar
- [shadcn/ui Vite Dark Mode](https://ui.shadcn.com/docs/dark-mode/vite) - ThemeProvider
- [shadcn/ui Vite Installation](https://ui.shadcn.com/docs/installation/vite) - Setup steps
- [Tailwind CSS Dark Mode](https://tailwindcss.com/docs/dark-mode) - Dark mode config
- [React Router Installation](https://reactrouter.com/start/declarative/installation) - v7 setup

### Secondary (MEDIUM confidence)
- [React Router v7 Guide - LogRocket](https://blog.logrocket.com/react-router-v7-guide/) - Patterns verified against docs
- [React Folder Structure 2025 - Robin Wieruch](https://www.robinwieruch.de/react-folder-structure/) - Feature-based structure
- [TanStack Query Caching Strategies - DHIWise](https://www.dhiwise.com/post/optimizing-performance-with-react-query-v5-best-practices) - gcTime/staleTime practices

### Tertiary (LOW confidence - needs validation)
- None - all findings verified against official docs
</sources>

<metadata>
## Metadata

**Research scope:**
- Core technology: React 19 + Vite + TypeScript
- Ecosystem: TanStack Query v5, React Router v7, Tailwind v4, shadcn/ui
- Patterns: Provider stack, feature folders, API hooks, theme management
- Pitfalls: v5 naming changes, Tailwind v4 config, path aliases

**Confidence breakdown:**
- Standard stack: HIGH - verified with official docs, stable versions
- Architecture: HIGH - based on official shadcn patterns and React best practices
- Pitfalls: HIGH - documented in migration guides and issue trackers
- Code examples: HIGH - adapted from official documentation

**Research date:** 2026-01-20
**Valid until:** 2026-02-20 (30 days - React ecosystem stable)
</metadata>

---

*Phase: 06-react-foundation*
*Research completed: 2026-01-20*
*Ready for planning: yes*
