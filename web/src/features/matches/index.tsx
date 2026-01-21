import { useState } from 'react'
import { MatchTable } from './components'
import { useMatches } from './hooks'

export function MatchList() {
  const [page, setPage] = useState(1)
  const [pageSize] = useState(50)

  const { data, isPending, error } = useMatches({
    page,
    pageSize,
    minBookmakers: 2, // Only show matched events
  })

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Matches</h1>
        {data && (
          <span className="text-sm text-muted-foreground">
            {data.total} matches found
          </span>
        )}
      </div>

      {error && (
        <div className="p-4 text-red-500 bg-red-50 rounded-md">
          Failed to load matches: {error.message}
        </div>
      )}

      <MatchTable events={data?.events ?? []} isLoading={isPending} />

      {/* Pagination */}
      {data && data.total > pageSize && (
        <div className="flex items-center justify-between pt-4">
          <button
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-muted"
          >
            Previous
          </button>
          <span className="text-sm text-muted-foreground">
            Page {page} of {Math.ceil(data.total / pageSize)}
          </span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={page >= Math.ceil(data.total / pageSize)}
            className="px-4 py-2 text-sm border rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-muted"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}

export function MatchDetail() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Match Detail</h1>
      <p className="text-muted-foreground">
        Detailed market odds comparison will appear here.
      </p>
    </div>
  )
}
