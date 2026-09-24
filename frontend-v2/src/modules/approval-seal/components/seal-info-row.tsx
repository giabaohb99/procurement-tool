import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

/**
 * Một dòng **NHÃN TRÁI — GIÁ TRỊ PHẢI** của các thẻ ở CỘT PHẢI (đại ca chốt
 * 22/09/2026).
 *
 * Khác `SealInfoItem` (nhãn trên, giá trị dưới) dùng ở cột chính: trong cột hẹp
 * 380px, kiểu xếp chồng ngốn gấp đôi chiều cao mà bề ngang thì bỏ không — bốn ô
 * thành tám dòng. Nhãn ở đây phải NGẮN, vì nhãn dài đẩy giá trị xuống dòng và
 * mất sạch cái lợi vừa nói; ngữ cảnh đã nằm ở tiêu đề thẻ.
 *
 * `items-baseline` để chữ nhãn và chữ giá trị đứng cùng đường chân, không bị
 * lệch khi giá trị to hơn hoặc dài hai dòng.
 *
 * ⚠️ **KIỂU CHỮ CỦA GIÁ TRỊ KHAI Ở ĐÂY, không khai ở từng thẻ** (đại ca bắt lỗi
 * 22/09/2026). Bản dời từ thân phiếu sang mang theo thói cũ: tên thì sans đậm,
 * email/điện thoại thì `font-mono text-xs`, ngày thì `text-muted-foreground` —
 * ba kiểu chữ chen nhau trong một thẻ bốn dòng. Xếp chồng thì còn đỡ, chứ căn
 * phải thành một cột thì mắt đọc dọc và thấy ngay là vênh. Cần dạng chữ khác
 * (ví dụ `tabular-nums` cho ngày) thì bọc thêm bên trong, ĐỪNG đổi họ chữ.
 */
export function SealInfoRow({
  label,
  children,
  className,
}: {
  label: string
  children: ReactNode
  className?: string
}) {
  return (
    <div className={cn('flex min-w-0 items-baseline justify-between gap-3', className)}>
      {/*  `shrink-0`: nhãn là thứ neo, co nó lại thì "Chức danh" gãy thành hai
          dòng trong khi giá trị vẫn còn chỗ trống. */}
      <span className="shrink-0 text-xs font-medium text-muted-foreground">{label}</span>
      {/*  `break-words`: email / tên miền dài không có khoảng trắng nào để ngắt,
          để nguyên là tràn ra ngoài viền thẻ ở cột 380px. */}
      <div className="min-w-0 break-words text-right text-sm font-medium text-foreground">
        {children}
      </div>
    </div>
  )
}
