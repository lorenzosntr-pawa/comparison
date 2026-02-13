import { useQuery } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

/**
 * Mapping list item matching backend MappingListItem schema.
 */
export interface MappingListItem {
  canonicalId: string
  name: string
  betpawaId: string | null
  sportybetId: string | null
  bet9jaKey: string | null
  outcomeCount: number
  source: 'code' | 'db'
  isActive: boolean
  priority: number
}

/**
 * Mapping list response matching backend MappingListResponse schema.
 */
export interface MappingListResponse {
  items: MappingListItem[]
  total: number
  page: number
  pageSize: number
}

/**
 * Fetch mappings with optional search filter.
 */
async function fetchMappings(search?: string): Promise<MappingListResponse> {
  const params = new URLSearchParams()
  if (search && search.trim()) {
    params.set('search', search.trim())
  }
  params.set('pageSize', '20')
  const query = params.toString()
  return api.get<MappingListResponse>(`/mappings${query ? `?${query}` : ''}`)
}

/**
 * Hook to search mappings with debounced input.
 *
 * @param searchTerm - The search string (debounced internally)
 * @param debounceMs - Debounce delay in milliseconds (default 300)
 * @returns Query result with matching mappings
 */
export function useMappingsSearch(searchTerm: string, debounceMs = 300) {
  const [debouncedSearch, setDebouncedSearch] = useState(searchTerm)

  // Debounce the search term
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm)
    }, debounceMs)

    return () => clearTimeout(timer)
  }, [searchTerm, debounceMs])

  return useQuery({
    queryKey: ['mappings-search', debouncedSearch],
    queryFn: () => fetchMappings(debouncedSearch),
    // Keep previous data while loading new search results
    placeholderData: (previousData) => previousData,
  })
}
