/**
 * Hook for fetching a list of countries for filter dropdowns.
 *
 * @module use-countries
 * @description Provides the data source for country filter dropdowns.
 * Supports availability scoping so competitor mode shows only countries
 * with competitor-only events.
 *
 * @example
 * ```typescript
 * import { useCountries } from '@/features/matches/hooks/use-countries'
 *
 * function CountryFilter({ availability }) {
 *   const { data: countries, isPending } = useCountries({ availability })
 *
 *   if (isPending) return <Spinner />
 *
 *   return (
 *     <Select>
 *       {countries?.map(country => (
 *         <SelectItem key={country} value={country}>{country}</SelectItem>
 *       ))}
 *     </Select>
 *   )
 * }
 * ```
 */

import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

/**
 * Parameters for filtering the countries list.
 */
export interface UseCountriesParams {
  /** Filter by platform availability: 'betpawa' or 'competitor' */
  availability?: 'betpawa' | 'competitor'
}

/**
 * Fetches a list of countries for filter dropdowns.
 *
 * @description Returns countries that have events in the specified availability mode.
 * When availability='competitor', returns only countries with competitor-only events.
 *
 * @param params - Filter options
 * @returns TanStack Query result with array of country names
 */
export function useCountries(params: UseCountriesParams = {}) {
  const { availability } = params

  return useQuery({
    queryKey: ['countries', { availability }],
    queryFn: () => api.getCountries({ availability }),
    staleTime: 60000, // 1 minute
    gcTime: 300000, // 5 minutes
  })
}
