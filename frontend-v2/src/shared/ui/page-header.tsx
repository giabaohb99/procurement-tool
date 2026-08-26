import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

interface PageHeaderProps {
  /** Tiêu đề — nhận cả JSX để chèn huy hiệu/trạng thái NGAY CẠNH tiêu đề. */
  title: ReactNode
  /** Dòng phụ dưới tiêu đề — nhận cả JSX để chèn trạng thái, huy hiệu… */
  description?: ReactNode
  /**
   * Chèn TRƯỚC tiêu đề — chỗ cho nút quay lại của trang chi tiết. Để cạnh tiêu
   * đề chứ không nhét chung với nhóm nút bên phải: "quay lại" là điều hướng,
   * không phải hành động trên bản ghi.
   */
  leading?: ReactNode
  /** Nút hành động bên phải (Thêm mới, Xuất Excel…). */
  actions?: ReactNode
  /**
   * Dính lên đầu khung khi cuộn.
   *
   * Cho trang dài mà nhóm nút nằm TRÊN ĐẦU (Lưu, Bãi bỏ, chuyển tab): cuộn
   * xuống giữa form rồi muốn lưu mà phải cuộn ngược lên đầu thì thao tác nào
   * cũng mất hai lần cuộn.
   *
   * Lề âm để dải này chạy hết bề ngang khung, không thụt vào theo phần đệm của
   * `PageContainer` — dính mà vẫn còn hai mép hở thì nhìn ra ngay là vá víu.
   */
  sticky?: boolean
}

/** Tiêu đề chuẩn cho mọi trang — giữ khoảng cách và cỡ chữ đồng nhất. */
export function PageHeader({
  title,
  description,
  leading,
  actions,
  sticky = false,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        'mb-5 flex flex-wrap items-start justify-between gap-3',
        sticky &&
          'sticky top-0 z-20 -mx-4 -mt-4 border-b bg-secondary px-4 py-3 lg:-mx-6 lg:-mt-6 lg:px-6',
      )}
    >
      <div className="flex items-start gap-3">
        {leading}
        <div>
          <h1 className="text-xl font-semibold tracking-tight text-navy">{title}</h1>
          {description && (
            <div className="mt-1 flex flex-wrap items-center gap-x-2 text-sm text-muted-foreground">
              {description}
            </div>
          )}
        </div>
      </div>
      {/* `flex-wrap` bắt buộc: trang chi tiết có màn tới 8 nút, không cho xuống
          dòng thì cụm nút đẩy rộng cả trang và sinh THANH CUỘN NGANG cho toàn
          trang — đã gặp ở màn chi tiết văn bản. `justify-end` để khi xuống dòng
          các nút vẫn bám mép phải, không trôi vào giữa. */}
      {actions && (
        <div className="flex min-w-0 flex-wrap items-center justify-end gap-2">{actions}</div>
      )}
    </div>
  )
}
