import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

interface ErrorStateProps {
  /** Mã hiện to phía trên (vd `404`). Bỏ trống khi lỗi không có mã. */
  code?: string
  title: string
  description: string
  /** Chi tiết kỹ thuật để người dùng copy gửi khi báo lỗi. */
  detail?: string
  /** Các nút hành động — trang gọi tự quyết định. */
  children?: ReactNode
  /** `true` khi dùng ngoài khung app (chưa có header/menu) để chiếm hết màn hình. */
  fullScreen?: boolean
}

/**
 * Khung hiển thị chung cho mọi màn lỗi (404, lỗi route, lỗi render). Gom về một
 * chỗ để ba màn này không trôi khác nhau về bố cục và cỡ chữ.
 */
export function ErrorState({
  code,
  title,
  description,
  detail,
  children,
  fullScreen = false,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center px-6 text-center',
        fullScreen ? 'min-h-screen bg-secondary' : 'min-h-[60vh]',
      )}
    >
      {code && <p className="text-5xl font-semibold text-primary">{code}</p>}

      <h1 className={cn('text-lg font-medium text-navy', code && 'mt-3')}>{title}</h1>
      <p className="mt-1 max-w-md text-sm text-muted-foreground">{description}</p>

      {children && <div className="mt-6 flex flex-wrap justify-center gap-3">{children}</div>}

      {detail && (
        <p className="mt-6 max-w-lg font-mono text-xs break-all text-muted-foreground/70">
          {detail}
        </p>
      )}
    </div>
  )
}
