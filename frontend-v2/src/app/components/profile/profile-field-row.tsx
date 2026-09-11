import type { LucideIcon } from 'lucide-react'

import { cn } from '@/shared/utils/cn'

interface ProfileFieldRowProps {
  icon: LucideIcon
  label: string
  /** Giá trị đã dựng thành chữ. Rỗng thì hiện «Chưa cập nhật» nghiêng, mờ. */
  value?: string
}

/**
 * MỘT DÒNG hồ sơ ở Trang cá nhân — nhãn bên trái, giá trị bên phải.
 *
 * Tách khỏi `profile-info-card` để khối *Hồ sơ nhân sự* mở rộng dùng chung đúng
 * một kiểu dòng: hai khối nằm sát nhau trên cùng một tab, lệch một chút là đọc
 * ra như hai trang khác nhau bị dán vào nhau.
 *
 * ⚠️ Khổ hẹp XẾP CHỒNG nhãn trên / giá trị dưới. Một hàng ngang thì riêng nhãn
 * `w-40` đã chiếm 160px trong 358px dùng được, phần còn lại không đủ cho một tên
 * pháp nhân — «CÔNG TY TNHH DEGO HOLDING» bị cắt cụt đúng chỗ phân biệt được các
 * pháp nhân với nhau. Từ `sm` trở lên về lại một hàng.
 *
 * ⚠️ Khổ hẹp cho XUỐNG DÒNG thay vì cắt (`break-words`, không `truncate`): đọc
 * được cả một địa chỉ thường trú dài quan trọng hơn giữ mỗi dòng đúng một hàng.
 */
export function ProfileFieldRow({ icon: Icon, label, value }: ProfileFieldRowProps) {
  const text = value?.trim()

  return (
    <div className="flex flex-col gap-0.5 border-b border-dashed py-2 last:border-b-0 sm:flex-row sm:items-center sm:gap-3">
      <div className="flex items-center gap-3 sm:shrink-0">
        <Icon className="size-4 shrink-0 text-muted-foreground" />
        <span className="text-[13px] text-muted-foreground sm:w-40">{label}</span>
      </div>
      {/*  `pl-7` = bề ngang biểu tượng (16) + khe (12): giá trị thẳng cột với
           nhãn ở trên. */}
      <span
        className={cn(
          'min-w-0 flex-1 pl-7 text-sm break-words sm:pl-0',
          text ? 'font-medium text-navy dark:text-foreground' : 'text-muted-foreground italic',
        )}
      >
        {text || 'Chưa cập nhật'}
      </span>
    </div>
  )
}
