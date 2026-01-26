import { useState } from 'react'
import { Database } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

export function ManageDataButton() {
  const [open, setOpen] = useState(false)

  return (
    <>
      <Button
        variant="outline"
        className="w-full"
        onClick={() => setOpen(true)}
      >
        <Database className="mr-2 h-4 w-4" />
        Manage Data
      </Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Manage Data</DialogTitle>
            <DialogDescription>
              View storage statistics and manually trigger data cleanup.
            </DialogDescription>
          </DialogHeader>
          <div className="py-6 text-center text-muted-foreground">
            Coming soon in Plan 22-05
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
