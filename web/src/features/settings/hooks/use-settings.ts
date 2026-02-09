/**
 * Hooks for reading and updating application settings.
 *
 * @module use-settings
 * @description Provides query and mutation hooks for managing application-wide
 * settings like scheduler interval, enabled platforms, and other configuration.
 *
 * @example
 * ```typescript
 * import { useSettings, useUpdateSettings } from '@/features/settings/hooks/use-settings'
 *
 * function SettingsForm() {
 *   const { data: settings, isPending } = useSettings()
 *   const { mutate: updateSettings, isPending: isSaving } = useUpdateSettings()
 *
 *   if (isPending) return <Spinner />
 *
 *   return (
 *     <form onSubmit={(e) => {
 *       e.preventDefault()
 *       const formData = new FormData(e.target)
 *       updateSettings({
 *         scrape_interval_minutes: parseInt(formData.get('interval')),
 *       })
 *     }}>
 *       <input name="interval" defaultValue={settings?.scrape_interval_minutes} />
 *       <button disabled={isSaving}>Save</button>
 *     </form>
 *   )
 * }
 * ```
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import type { SettingsUpdate } from '@/types/api'

/**
 * Fetches current application settings.
 *
 * @description Returns the current configuration including scheduler interval,
 * enabled platforms, and other settings. Uses a 30-second stale time since
 * settings rarely change.
 *
 * @returns TanStack Query result with SettingsResponse
 *
 * @example
 * ```typescript
 * const { data: settings, isPending, error } = useSettings()
 *
 * console.log(`Scrape interval: ${settings?.scrape_interval_minutes} minutes`)
 * ```
 */
export function useSettings() {
  return useQuery({
    queryKey: ['settings'],
    queryFn: () => api.getSettings(),
    staleTime: 30000, // Settings don't change often
  })
}

/**
 * Creates a mutation for updating application settings.
 *
 * @description Sends a PATCH request to update settings. On success:
 * 1. Invalidates the settings query to refresh the cached values
 * 2. Immediately refetches scheduler status (interval may have changed)
 *
 * @returns TanStack Mutation with mutate accepting SettingsUpdate payload
 *
 * @example
 * ```typescript
 * const { mutate: updateSettings, isPending, error } = useUpdateSettings()
 *
 * // Update scrape interval
 * updateSettings({ scrape_interval_minutes: 30 }, {
 *   onSuccess: () => toast.success('Settings saved'),
 *   onError: (err) => toast.error(err.message),
 * })
 *
 * // Enable/disable a platform
 * updateSettings({ enabled_platforms: ['betpawa', 'sportybet'] })
 * ```
 */
export function useUpdateSettings() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: SettingsUpdate) => api.updateSettings(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      // Use refetchQueries for immediate update of scheduler interval
      queryClient.refetchQueries({ queryKey: ['scheduler', 'status'] })
    },
  })
}
