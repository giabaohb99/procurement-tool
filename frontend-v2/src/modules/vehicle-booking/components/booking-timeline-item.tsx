import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

/**
 * Một dòng trên trục dọc (lộ trình, tiến trình xử lý): ĐIỂM ĐÁNH DẤU bên trái,
 * nội dung bên phải, đường nối chạy từ điểm đánh dấu xuống dòng kế.
 *
 * Đường nối là một `<span>` GIÃN theo chiều cao dòng (`flex-1`) chứ không phải
 * viền trái có chiều cao cố định: nội dung mỗi chặng dài ngắn khác nhau (một
 * điểm dừng có thêm người liên hệ + ghi chú), viết số cứng thì chỗ đứt chỗ thừa.
 *
 * Đặt trong `<ol className="flex flex-col">`.
 */
export function TimelineItem({
  marker,
  last,
  children,
}: {
  marker: ReactNode
  /** Dòng cuối: không vẽ đường nối, không chừa khoảng dưới. */
  last?: boolean
  children: ReactNode
}) {
  return (
    <li className="flex gap-3">
      <div className="flex flex-col items-center">
        {marker}
        {!last && <span className="w-px flex-1 bg-border" />}
      </div>
      <div className={cn('min-w-0 flex-1', last ? 'pb-0' : 'pb-4')}>{children}</div>
    </li>
  )
}
