/**
 * Chart component for visualizing margin patterns relative to kickoff time.
 *
 * @module time-to-kickoff-chart
 * @description Displays margin timeline with normalized X-axis showing hours
 * until kickoff. Includes visual time bucket zones (7d+, 3-7d, 24-72h, <24h).
 */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
  ReferenceLine,
  Legend,
} from 'recharts'
import type { TimeToKickoffPoint } from '../hooks/use-tournament-markets'
import { BOOKMAKER_COLORS } from './bookmaker-filter'

/**
 * Format hours-to-kickoff for display.
 * Returns strings like "-7d", "-3d 12h", "-6h", "KO"
 */
function formatHoursToKickoff(hours: number): string {
  if (hours >= 0) return 'KO'

  const absHours = Math.abs(hours)

  if (absHours >= 168) {
    // 7+ days
    const days = Math.floor(absHours / 24)
    return `-${days}d`
  } else if (absHours >= 24) {
    // 1-7 days
    const days = Math.floor(absHours / 24)
    const remainingHours = Math.round(absHours % 24)
    if (remainingHours > 0) {
      return `-${days}d ${remainingHours}h`
    }
    return `-${days}d`
  } else {
    // Less than 24 hours
    return `-${Math.round(absHours)}h`
  }
}

/**
 * Time bucket zone colors (light backgrounds for shading).
 */
const BUCKET_COLORS = {
  '7d+': '#f0f9ff', // Light blue
  '3-7d': '#fef3c7', // Light yellow
  '24-72h': '#fef9c3', // Lighter yellow
  '<24h': '#fee2e2', // Light red
}

interface TimeToKickoffChartProps {
  /** Margin data points with hoursToKickoff (Betpawa data) */
  data: TimeToKickoffPoint[]
  /** Competitor data keyed by bookmaker slug */
  competitorData?: Record<string, TimeToKickoffPoint[]>
  /** Which bookmakers to show (when in overlay mode) */
  selectedBookmakers?: string[]
  /** Chart height in pixels */
  height?: number
  /** Whether to show time bucket zones as shaded areas */
  showBucketZones?: boolean
}

/** Bookmaker display labels */
const BOOKMAKER_LABELS: Record<string, string> = {
  betpawa: 'Betpawa',
  sportybet: 'SportyBet',
  bet9ja: 'Bet9ja',
}

/** Merged data point for multi-bookmaker chart */
interface MergedDataPoint {
  hoursToKickoff: number
  betpawa?: number
  sportybet?: number
  bet9ja?: number
}

/**
 * Chart component for time-to-kickoff margin visualization.
 *
 * X-axis shows hours until kickoff (negative values, left = earliest).
 * Shaded zones indicate time buckets: 7d+, 3-7d, 24-72h, <24h.
 */
export function TimeToKickoffChart({
  data,
  competitorData,
  selectedBookmakers,
  height = 200,
  showBucketZones = true,
}: TimeToKickoffChartProps) {
  // Check if we're in multi-bookmaker mode
  const isMultiBookmakerMode = Boolean(competitorData && selectedBookmakers)

  if (!data.length) {
    return (
      <div
        className="flex items-center justify-center text-muted-foreground"
        style={{ height }}
      >
        No data available
      </div>
    )
  }

  // For multi-bookmaker mode, merge all data points
  let chartData: MergedDataPoint[]
  let minHours: number
  let maxHours: number

  if (isMultiBookmakerMode && competitorData && selectedBookmakers) {
    // Collect all unique hoursToKickoff values from all bookmakers
    const hoursSet = new Set<number>()
    const betpawaByHour = new Map<number, number>()
    const competitorsByHour: Record<string, Map<number, number>> = {}

    // Index Betpawa data by hours
    for (const point of data) {
      const h = Math.round(point.hoursToKickoff * 10) / 10 // Round to 1 decimal
      hoursSet.add(h)
      betpawaByHour.set(h, point.margin)
    }

    // Index competitor data by hours
    for (const [slug, points] of Object.entries(competitorData)) {
      competitorsByHour[slug] = new Map()
      for (const point of points) {
        const h = Math.round(point.hoursToKickoff * 10) / 10
        hoursSet.add(h)
        competitorsByHour[slug].set(h, point.margin)
      }
    }

    // Build merged data array
    const sortedHours = Array.from(hoursSet).sort((a, b) => a - b)
    chartData = sortedHours.map((h) => {
      const point: MergedDataPoint = { hoursToKickoff: h }
      if (selectedBookmakers.includes('betpawa')) {
        point.betpawa = betpawaByHour.get(h)
      }
      if (selectedBookmakers.includes('sportybet') && competitorsByHour.sportybet) {
        point.sportybet = competitorsByHour.sportybet.get(h)
      }
      if (selectedBookmakers.includes('bet9ja') && competitorsByHour.bet9ja) {
        point.bet9ja = competitorsByHour.bet9ja.get(h)
      }
      return point
    })

    minHours = Math.min(...sortedHours)
    maxHours = Math.max(...sortedHours, 0)
  } else {
    // Single bookmaker mode (original behavior)
    minHours = Math.min(...data.map((d) => d.hoursToKickoff))
    maxHours = Math.max(...data.map((d) => d.hoursToKickoff), 0)

    chartData = [...data]
      .sort((a, b) => a.hoursToKickoff - b.hoursToKickoff)
      .map((point) => ({
        hoursToKickoff: point.hoursToKickoff,
        betpawa: point.margin,
      }))
  }

  // Determine which bookmakers to render
  const bookmakersToShow = selectedBookmakers || ['betpawa']

  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart
        data={chartData}
        margin={{ top: 10, right: 20, left: 10, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />

        {/* Time bucket zones (rendered behind data) */}
        {showBucketZones && (
          <>
            {/* 7d+ zone: from min to -168 hours */}
            {minHours < -168 && (
              <ReferenceArea
                x1={minHours}
                x2={-168}
                fill={BUCKET_COLORS['7d+']}
                fillOpacity={0.4}
              />
            )}
            {/* 3-7d zone: -168 to -72 hours */}
            {minHours < -72 && (
              <ReferenceArea
                x1={Math.max(minHours, -168)}
                x2={-72}
                fill={BUCKET_COLORS['3-7d']}
                fillOpacity={0.4}
              />
            )}
            {/* 24-72h zone: -72 to -24 hours */}
            {minHours < -24 && (
              <ReferenceArea
                x1={Math.max(minHours, -72)}
                x2={-24}
                fill={BUCKET_COLORS['24-72h']}
                fillOpacity={0.4}
              />
            )}
            {/* <24h zone: -24 to max (or 0) */}
            <ReferenceArea
              x1={Math.max(minHours, -24)}
              x2={maxHours}
              fill={BUCKET_COLORS['<24h']}
              fillOpacity={0.4}
            />
          </>
        )}

        {/* Bucket boundary divider lines */}
        {showBucketZones && (
          <>
            {minHours < -168 && (
              <ReferenceLine
                x={-168}
                stroke="#94a3b8"
                strokeDasharray="4 4"
                strokeOpacity={0.6}
              />
            )}
            {minHours < -72 && (
              <ReferenceLine
                x={-72}
                stroke="#94a3b8"
                strokeDasharray="4 4"
                strokeOpacity={0.6}
              />
            )}
            {minHours < -24 && (
              <ReferenceLine
                x={-24}
                stroke="#94a3b8"
                strokeDasharray="4 4"
                strokeOpacity={0.6}
              />
            )}
          </>
        )}

        <XAxis
          dataKey="hoursToKickoff"
          type="number"
          domain={[minHours, maxHours]}
          tick={{ fontSize: 11 }}
          tickFormatter={formatHoursToKickoff}
          className="text-muted-foreground"
        />

        <YAxis
          domain={['auto', 'auto']}
          tick={{ fontSize: 11 }}
          tickFormatter={(value) =>
            typeof value === 'number' ? `${value.toFixed(1)}%` : ''
          }
          width={45}
          className="text-muted-foreground"
        />

        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--popover))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '6px',
            fontSize: '12px',
          }}
          labelFormatter={(value) => formatHoursToKickoff(value as number)}
          formatter={(value, name) => {
            if (typeof value !== 'number') return ['-', name]
            const label = BOOKMAKER_LABELS[name as string] || name
            return [`${value.toFixed(2)}%`, label]
          }}
          cursor={{ strokeDasharray: '3 3' }}
          isAnimationActive={false}
        />

        {/* Render a line for each selected bookmaker */}
        {bookmakersToShow.includes('betpawa') && (
          <Line
            type="monotone"
            dataKey="betpawa"
            name="betpawa"
            stroke={BOOKMAKER_COLORS.betpawa}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
            connectNulls
          />
        )}
        {bookmakersToShow.includes('sportybet') && isMultiBookmakerMode && (
          <Line
            type="monotone"
            dataKey="sportybet"
            name="sportybet"
            stroke={BOOKMAKER_COLORS.sportybet}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
            connectNulls
          />
        )}
        {bookmakersToShow.includes('bet9ja') && isMultiBookmakerMode && (
          <Line
            type="monotone"
            dataKey="bet9ja"
            name="bet9ja"
            stroke={BOOKMAKER_COLORS.bet9ja}
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
            connectNulls
          />
        )}

        {/* Legend when showing multiple bookmakers */}
        {isMultiBookmakerMode && bookmakersToShow.length > 1 && (
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value) => BOOKMAKER_LABELS[value] || value}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  )
}
