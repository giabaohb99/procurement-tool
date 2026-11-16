import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

interface ProfileFieldGroupProps {
  title: string
  icon: LucideIcon
  /** Nút bên phải tiêu đề nhóm (vd "Sửa" của nhóm Liên hệ). */
  actions?: ReactNode
  children: ReactNode
  className?: string
}

/**
 * Một NHÓM trường trong thẻ Hồ sơ nhân sự ở Trang cá nhân — tiêu đề nhỏ + các dòng, KHÔNG viền thẻ.
 *
 * Trước duoc-CR-766 mỗi nhóm là một thẻ riêng xếp lưới hai cột: thẻ cao thấp khác nhau nên lưới chừa
 * khoảng trống lớn, và trang là một chồng mười thẻ. Nay các nhóm nằm chung một thẻ, chảy theo cột
 * (`columns-2`); `break-inside-avoid` giữ một nhóm không bị cắt đôi sang cột bên kia.
 */
export function ProfileFieldGroup({ title, icon: Icon, actions, children, className }: ProfileFieldGroupProps) {
  return (
    <section aria-label={title} className={cn('break-inside-avoid', className)}>
      <div className="mb-1 flex min-h-8 items-center justify-between gap-2 border-b pb-1.5">
        <h3 className="flex items-center gap-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
          <Icon className="size-4 shrink-0" />
          {title}
        </h3>
        {actions}
      </div>
      {children}
    </section>
  )
}
