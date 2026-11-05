import { ChevronDown, ChevronRight } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

interface ReportItemProgressCardProps {
  name: string
  docCount: number
  doneCount: number
  /** Thanh tiến độ của bảng gốc — truyền vào để thẻ và bảng không lệch màu / lệch cách đếm. */
  progress: ReactNode
  /** Ô "Hạn gần nhất" của bảng gốc. */
  expiry: ReactNode
  /** Đang sổ. Bỏ trống cùng `onToggle` = dòng TỔNG, không gập / sổ được. */
  open?: boolean
  onToggle?: () => void
  /** Nút sửa nút / xóa cụm — ANH EM của vùng bấm sổ, bám góc phải. */
  actions?: ReactNode
  /** Dải sổ (hồ sơ của dòng) — chỉ bày khi `open`. */
  children?: ReactNode
}

/**
 * Một DÒNG HÀNG của dạng xem *Theo dòng hàng* ở khổ điện thoại — thay cho bảng 6 cột
 * (mũi tên · tên · số hồ sơ · đã xong · tiến độ · hạn gần nhất). Dùng chung cho khối
 * *Báo cáo thực hiện* và khối *Hồ sơ cần có* vì hai bảng cùng một khuôn.
 *
 * ⚠️ **Vì sao bảng 6 cột vẫn phải đổi**: cột Tiến độ (thanh 160px) + Hạn (128px) đã
 * 288px, khung 322px còn lại 34px cho tên dòng hàng — tên "Kali nitrat KNO₃ 99%" bẻ
 * thành bốn dòng một chữ. Thẻ để tên một hàng riêng, thanh tiến độ trải cả bề ngang.
 *
 * ⚠️ **Vùng bấm sổ chỉ là hàng tiêu đề, không phải cả thẻ**: dải sổ bên dưới chứa
 * nút sửa / xóa / tick hồ sơ — bọc cả thẻ trong một `<button>` là lồng nút trong nút.
 * Ruột nút dựng bằng `<span>` vì `<button>` chỉ nhận nội dung chữ.
 */
export function ReportItemProgressCard({
  name,
  docCount,
  doneCount,
  progress,
  expiry,
  open = false,
  onToggle,
  actions,
  children,
}: ReportItemProgressCardProps) {
  const isTotal = !onToggle
  const heading = (
    <>
      {!isTotal && (
        <span className="mt-0.5 shrink-0 text-muted-foreground" aria-hidden="true">
          {open ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
        </span>
      )}
      <span className="min-w-0 flex-1">
        <span className={cn('block break-words', isTotal ? 'font-semibold' : 'font-medium')}>
          {name}
        </span>
        <span className="block text-xs tabular-nums text-muted-foreground">
          {docCount} hồ sơ · {doneCount} đã xong
        </span>
      </span>
    </>
  )

  return (
    <div className={cn('space-y-2 p-3', isTotal && 'bg-muted/50')}>
      <div className="flex items-start gap-2">
        {onToggle ? (
          <button
            type="button"
            aria-expanded={open}
            onClick={onToggle}
            className="flex min-w-0 flex-1 items-start gap-2 text-left"
          >
            {heading}
          </button>
        ) : (
          <div className="flex min-w-0 flex-1 items-start gap-2">{heading}</div>
        )}
        {actions && <div className="flex shrink-0 items-center gap-0.5">{actions}</div>}
      </div>

      <div className={cn('flex items-center gap-2', !isTotal && 'pl-6')}>
        <div className="min-w-0 flex-1">{progress}</div>
        <div className="shrink-0">{expiry}</div>
      </div>

      {open && children && <div className="rounded-md bg-muted/40 p-3">{children}</div>}
    </div>
  )
}
