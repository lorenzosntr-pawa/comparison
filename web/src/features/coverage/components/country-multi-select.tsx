import * as React from 'react'
import { Check, ChevronsUpDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover'

interface CountryMultiSelectProps {
  countries: string[]
  selected: string[]
  onSelectedChange: (selected: string[]) => void
}

export function CountryMultiSelect({
  countries,
  selected,
  onSelectedChange,
}: CountryMultiSelectProps) {
  const [open, setOpen] = React.useState(false)

  const handleSelectAll = () => {
    onSelectedChange([...countries])
  }

  const handleClearAll = () => {
    onSelectedChange([])
  }

  const handleToggleCountry = (country: string) => {
    if (selected.includes(country)) {
      onSelectedChange(selected.filter((c) => c !== country))
    } else {
      onSelectedChange([...selected, country])
    }
  }

  const triggerText =
    selected.length === 0
      ? 'All Countries'
      : selected.length === 1
        ? selected[0]
        : `${selected.length} countries`

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          role="combobox"
          aria-expanded={open}
          className="w-48 justify-between"
        >
          <span className="truncate">{triggerText}</span>
          <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-48 p-0" align="start">
        <Command>
          <CommandInput placeholder="Search countries..." />
          <CommandList>
            <CommandEmpty>No country found.</CommandEmpty>
            <CommandGroup>
              <div className="flex gap-1 p-1">
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 flex-1 text-xs"
                  onClick={handleSelectAll}
                >
                  Select All
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 flex-1 text-xs"
                  onClick={handleClearAll}
                >
                  Clear All
                </Button>
              </div>
            </CommandGroup>
            <CommandSeparator />
            <CommandGroup>
              {countries.map((country) => {
                const isSelected = selected.includes(country)
                return (
                  <CommandItem
                    key={country}
                    value={country}
                    onSelect={() => handleToggleCountry(country)}
                  >
                    <Checkbox
                      checked={isSelected}
                      className="mr-2"
                      // Prevent checkbox from capturing click - let CommandItem handle it
                      onClick={(e) => e.preventDefault()}
                    />
                    <span className="flex-1 truncate">{country}</span>
                    {isSelected && (
                      <Check className="ml-auto h-4 w-4 text-primary" />
                    )}
                  </CommandItem>
                )
              })}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}
