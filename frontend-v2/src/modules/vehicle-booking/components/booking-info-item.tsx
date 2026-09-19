import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

/**
 * Một cặp NHÃN — GIÁ TRỊ ở màn XEM phiếu.
 *
 * ⚠️ Cố ý KHÔNG dùng `ReadOnlyValue` (ô có viền, nền mờ). Ô khóa đó sinh ra cho
 * BIỂU MẪU: nó nói "chỗ này lẽ ra gõ được nhưng đang khóa". Trang chi tiết thì
 * không có chỗ nào gõ được cả, nên hai chục cái khung xếp thành lưới đọc ra như
 * một biểu mẫu bị vô hiệu hóa — mà tệ nhất là ô RỖNG: khung trống chiếm đúng
 * bằng chỗ của dữ liệu thật nên mắt phải quét hết mới biết chỗ nào có chữ.
 * Chữ trần vẫn bôi đen / chép được (đó mới là lý do ra đời của `ReadOnlyValue`).
 *
 * Cùng khuôn với `InfoItem` của chi tiết Văn thư (`approval-seal`).
 */
export function BookingInfoItem({
  label,
  children,
  className,
}: {
  label: string
  children?: ReactNode
  className?: string
}) {
  const empty = children === null || children === undefined || children === '' || children === '—'
  return (
    //  `min-w-0`: ô lưới co được dưới bề ngang một từ dài (email/URL) để không đẩy tràn lưới.
    <div className={cn('flex min-w-0 flex-col gap-0.5', className)}>
      <span className="text-xs text-muted-foreground">{label}</span>
      <div
        className={cn(
          'break-words text-sm',
          empty ? 'text-muted-foreground/60' : 'font-medium text-foreground',
        )}
      >
        {empty ? '—' : children}
      </div>
    </div>
  )
}

/**
 * Tiêu đề một thẻ chi tiết: icon + nhãn, gạch dưới kéo hết bề ngang thẻ
 * (`-mx-5 px-5` bù `p-5` của Card). `extra` dồn phải cho badge/chip.
 */
export function BookingCardHeader({
  icon,
  children,
  extra,
  className,
}: {
  icon: ReactNode
  children: ReactNode
  extra?: ReactNode
  /** Thẻ ở CỘT PHỤ hẹp hơn (`p-4`) nên phải bù lề khác: truyền `-mx-4 px-4`. */
  className?: string
}) {
  return (
    <div
      className={cn(
        '-mx-5 -mt-1 flex flex-wrap items-center justify-between gap-2 border-b px-5 pb-3',
        className,
      )}
    >
      <span className="inline-flex items-center gap-2 font-medium text-navy dark:text-foreground">
        {icon}
        {children}
      </span>
      {extra && <div className="flex flex-wrap items-center gap-1.5">{extra}</div>}
    </div>
  )
}
