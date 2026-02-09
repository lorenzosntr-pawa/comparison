/**
 * Mobile viewport detection hook.
 *
 * @module use-mobile
 * @description Provides a reactive hook for detecting mobile viewport sizes.
 * Uses the CSS media query API for efficient, event-driven updates without
 * polling or resize event listeners.
 *
 * @example
 * ```typescript
 * import { useIsMobile } from '@/hooks/use-mobile'
 *
 * function ResponsiveLayout() {
 *   const isMobile = useIsMobile()
 *
 *   return isMobile ? <MobileNav /> : <DesktopNav />
 * }
 * ```
 */

import * as React from "react"

/** Breakpoint width in pixels below which viewport is considered mobile */
const MOBILE_BREAKPOINT = 768

/**
 * Hook for detecting if the current viewport is mobile-sized.
 *
 * @description Uses window.matchMedia for efficient media query evaluation.
 * Updates automatically when viewport crosses the breakpoint threshold.
 *
 * @returns True if viewport width is less than 768px, false otherwise.
 *          Returns false during initial SSR/hydration (before effect runs).
 *
 * @example
 * ```typescript
 * const isMobile = useIsMobile()
 * // Use for conditional rendering or styling
 * ```
 */
export function useIsMobile() {
  const [isMobile, setIsMobile] = React.useState<boolean | undefined>(undefined)

  React.useEffect(() => {
    const mql = window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT - 1}px)`)
    const onChange = () => {
      setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    }
    mql.addEventListener("change", onChange)
    setIsMobile(window.innerWidth < MOBILE_BREAKPOINT)
    return () => mql.removeEventListener("change", onChange)
  }, [])

  return !!isMobile
}
