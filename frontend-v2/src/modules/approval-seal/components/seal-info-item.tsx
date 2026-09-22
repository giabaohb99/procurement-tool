import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

/**
 * Một Ô NHÃN — GIÁ TRỊ trong phiếu đóng dấu (nhãn nhỏ mờ, giá trị đậm bên dưới).
 *
 * Tách khỏi `seal-detail-body.tsx` (22/09/2026) khi khối Người yêu cầu và khối
 * Phê duyệt dời sang cột phải: ba nơi cùng vẽ một kiểu ô, chép lại thì lệch.
 */
export function SealInfoItem({
  label,
  children,
  className,
}: {
  label: string
  children: ReactNode
  className?: string
}) {
  return (
    <div className={cn('flex min-w-0 flex-col gap-1', className)}>
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <div className="text-sm text-foreground font-medium">{children}</div>
    </div>
  )
}
