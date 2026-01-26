import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'
import { useSettings, useUpdateSettings } from '../hooks'

const PLATFORMS = [
  { slug: 'sportybet', name: 'SportyBet' },
  { slug: 'betpawa', name: 'BetPawa' },
  { slug: 'bet9ja', name: 'Bet9ja' },
]

interface PlatformTogglesProps {
  horizontal?: boolean
}

export function PlatformToggles({ horizontal = false }: PlatformTogglesProps) {
  const { data: settings } = useSettings()
  const { mutate: updateSettings, isPending } = useUpdateSettings()

  const enabledPlatforms = settings?.enabledPlatforms ?? []

  const handleToggle = (slug: string, checked: boolean) => {
    let newPlatforms: string[]

    if (checked) {
      newPlatforms = [...enabledPlatforms, slug]
    } else {
      // Prevent disabling all platforms
      if (enabledPlatforms.length <= 1) {
        return
      }
      newPlatforms = enabledPlatforms.filter((p) => p !== slug)
    }

    updateSettings({ enabledPlatforms: newPlatforms })
  }

  return (
    <div
      className={cn(
        horizontal
          ? 'flex flex-wrap gap-x-6 gap-y-3'
          : 'space-y-4'
      )}
    >
      {PLATFORMS.map((platform) => {
        const isEnabled = enabledPlatforms.includes(platform.slug)
        const isOnlyEnabled = isEnabled && enabledPlatforms.length === 1

        return (
          <div
            key={platform.slug}
            className={cn(
              'flex items-center gap-3',
              horizontal ? '' : 'justify-between'
            )}
          >
            <Switch
              checked={isEnabled}
              onCheckedChange={(checked) => handleToggle(platform.slug, checked)}
              disabled={isPending || isOnlyEnabled}
            />
            <div className="space-y-0.5">
              <div className="text-sm font-medium">{platform.name}</div>
              {isOnlyEnabled && !horizontal && (
                <div className="text-xs text-muted-foreground">
                  At least one platform must remain enabled
                </div>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
