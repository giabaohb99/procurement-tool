import { cn } from '@/shared/utils/cn'

import { getDataModule } from '../config/data-modules'

/** Thẻ Phân hệ có icon + tên, tô màu đúng thẻ phân hệ ở Trang chủ. */
export function ModuleBadge({ moduleId }: { moduleId?: string }) {
  const m = moduleId ? getDataModule(moduleId) : undefined
  if (!m) return <span className="text-muted-foreground">—</span>
  const Icon = m.icon
  return (
    <span
      className={cn(
        'inline-flex w-fit items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium',
        m.accent,
      )}
    >
      <Icon className="size-3.5" />
      {m.label}
    </span>
  )
}
