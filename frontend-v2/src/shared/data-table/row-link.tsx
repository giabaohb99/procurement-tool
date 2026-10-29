import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { cn } from '@/shared/utils/cn'

interface RowLinkProps {
  to: string
  children: ReactNode
  className?: string
}

/**
 * Mã chứng từ trong ô bảng là LINK THẬT (`<a href>`): chuột phải "Mở trong tab
 * mới" chạy được, Ctrl / chuột giữa để trình duyệt tự mở tab mới, bấm thường
 * chuyển trang trong SPA. Chặn lan lên dòng để một cú bấm không mở hai lần.
 */
export function RowLink({ to, children, className }: RowLinkProps) {
  return (
    <Link
      to={to}
      className={cn('truncate font-medium text-primary hover:underline', className)}
      onClick={(event) => event.stopPropagation()}
      onAuxClick={(event) => event.stopPropagation()}
    >
      {children}
    </Link>
  )
}
