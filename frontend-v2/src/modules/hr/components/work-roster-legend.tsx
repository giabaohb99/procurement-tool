import { cn } from '@/shared/utils/cn'

/** Chú giải — mẫu màu phải TRÙNG với ô trong lưới (`WorkRosterCellView`). */
const ITEMS: { label: string; swatch: string }[] = [
  { label: 'Đi làm', swatch: 'bg-card border-border' },
  { label: 'Nghỉ theo lịch', swatch: 'bg-muted border-border' },
  { label: 'Ngày lễ', swatch: 'bg-destructive/10 border-destructive/30' },
  { label: 'Phép đã duyệt', swatch: 'bg-leave-approved border-leave-approved' },
  { label: 'Chờ duyệt', swatch: 'bg-info/10 border-dashed border-info' },
]

export function WorkRosterLegend({ className }: { className?: string }) {
  return (
    <ul
      aria-label="Chú giải màu"
      className={cn('flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground', className)}
    >
      {ITEMS.map((item) => (
        <li key={item.label} className="flex items-center gap-1.5">
          <span aria-hidden className={cn('size-3.5 rounded-sm border', item.swatch)} />
          {item.label}
        </li>
      ))}
      <li className="flex items-center gap-1.5">
        <span aria-hidden className="relative size-3.5 overflow-hidden rounded-sm border border-border bg-card">
          <span className="absolute inset-y-0 left-0 w-1/2 bg-leave-approved" />
        </span>
        Nghỉ nửa buổi
      </li>
    </ul>
  )
}
