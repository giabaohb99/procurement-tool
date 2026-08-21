import { Filter, X } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/shared/ui/sheet'

export interface QuickFilterSheetProps {
  activeCount?: number
  onClearAll?: () => void
  children: ReactNode
}

export function QuickFilterSheet({ activeCount = 0, onClearAll, children }: QuickFilterSheetProps) {
  const [open, setOpen] = useState(false)

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="outline" size="sm" className="h-9 px-3 text-xs md:hidden flex items-center gap-1.5">
          <Filter className="h-3.5 w-3.5" />
          <span>Bộ lọc</span>
          {activeCount > 0 && (
            <Badge variant="default" className="h-4 px-1.5 text-[10px] rounded-full">
              {activeCount}
            </Badge>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent side="bottom" className="max-h-[85vh] rounded-t-xl p-4 overflow-y-auto">
        <SheetHeader className="pb-3 border-b flex flex-row items-center justify-between">
          <SheetTitle className="text-base font-semibold flex items-center gap-2">
            <Filter className="h-4 w-4" /> Bộ lọc nhanh
            {activeCount > 0 && (
              <Badge variant="secondary" className="text-xs">
                {activeCount} đang lọc
              </Badge>
            )}
          </SheetTitle>
          {onClearAll && activeCount > 0 && (
            <Button variant="ghost" size="sm" className="h-8 text-xs text-muted-foreground" onClick={onClearAll}>
              <X className="h-3.5 w-3.5 mr-1" /> Xóa lọc
            </Button>
          )}
        </SheetHeader>

        <div className="py-4 space-y-4">
          {children}
        </div>

        <div className="pt-3 border-t">
          <Button className="w-full h-10" onClick={() => setOpen(false)}>
            Áp dụng
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  )
}
