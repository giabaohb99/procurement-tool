import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

/**
 * Tiêu đề một KHỐI trong phiếu đóng dấu — kẻ ngang tràn mép thẻ `Card p-5`.
 *
 * Tách khỏi `seal-detail-body.tsx` (22/09/2026) vì thẻ Ghi chú dời sang cột phải
 * nhưng vẫn phải giống hệt các khối còn lại; chép lại khung thì hai nơi trôi khác
 * nhau ngay lần sửa đầu tiên.
 */
export function SealSectionHeader({
  icon: Icon,
  title,
  iconColor = 'text-primary',
  extra,
}: {
  icon: React.ElementType
  title: string
  iconColor?: string
  extra?: ReactNode
}) {
  return (
    <div className="-mx-5 -mt-1 flex items-center justify-between border-b border-border/50 px-5 pb-3">
      <div className="flex items-center gap-2 font-semibold text-sm text-navy dark:text-foreground">
        <Icon className={cn('size-4.5 shrink-0', iconColor)} />
        <span>{title}</span>
      </div>
      {extra && <div className="text-xs text-muted-foreground">{extra}</div>}
    </div>
  )
}
