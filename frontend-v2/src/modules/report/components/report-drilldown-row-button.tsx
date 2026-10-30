import { List } from 'lucide-react'

import { Button } from '@/shared/ui/button'

/** Nút "Xem" của cột "Danh sách" trong bảng "Xem theo" — chặn nổi bọt để không dính sự kiện của dòng. */
export function ReportDrilldownRowButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      className="h-7 gap-1 px-2 text-xs"
      aria-label={`Xem danh sách ${label}`}
      onClick={(e) => {
        e.stopPropagation()
        onClick()
      }}
    >
      <List className="size-3.5" aria-hidden />
      Xem
    </Button>
  )
}
