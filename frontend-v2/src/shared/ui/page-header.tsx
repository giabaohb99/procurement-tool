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
          'sticky top-0 z-20 -mx-4 -mt-4 border-b bg-canvas px-4 py-3 lg:-mx-6 lg:-mt-6 lg:px-6',
      )}
    >
      {/* `min-w-0`: khối tiêu đề phải CO ĐƯỢC, nếu không nó luôn đòi bề rộng của
          dòng mô tả dài nhất và đẩy cụm nút xuống một hàng riêng ngay từ ~820px
          — `flex-wrap` xuống dòng TRƯỚC khi co, nên không có vế này thì chữ
          không bao giờ tự ngắt. Có nó: mô tả ngắt làm hai dòng, cụm nút ở lại
          bên phải tiêu đề (báo 09/09/2026 ở màn Quỹ phép năm).

          `flex-[1_1_16rem]` chứ KHÔNG `flex-1`: `flex-1` đặt cỡ gốc bằng 0, tức
          khối tiêu đề không đòi lấy một pixel nào và cụm nút cứ thế lấn hết —
          màn chi tiết 4 nút ở 768px bóp tiêu đề còn ~60px, «Đơn nghỉ phép NP010»
          rơi xuống thành bốn dòng mỗi dòng một chữ, trong khi cụm nút vẫn nằm
          thong dong một hàng (báo 09/09/2026). 16rem là mức tiêu đề đòi giữ:
          còn đủ chỗ thì nút vẫn ở cùng hàng, không đủ thì cả cụm nút xuống hàng
          riêng — đúng thứ tự ưu tiên, vì tiêu đề nói ĐANG XEM CÁI GÌ. */}
      <div className="flex min-w-0 flex-[1_1_16rem] items-start gap-3">
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
          các nút vẫn bám mép phải, không trôi vào giữa.

          `max-md:w-full`: dưới 640px nhóm này luôn xuống hàng riêng, và một khối
          co theo nội dung ở đó khiến `w-full` của nút bên trong quy về đúng bề
          rộng cũ — tức không trang nào ép được nút trải hết hàng trên điện
          thoại, dù đó là cách bày hành động chính dễ bấm nhất. Chiếm trọn hàng
          không đổi gì với các trang khác: `justify-end` vẫn giữ nút bám mép
          phải, chỉ khác là mép phải của TRANG thay vì của cụm nút. */}
      {actions && (
        <div className="flex min-w-0 flex-wrap items-center justify-end gap-2 max-md:w-full">
          {actions}
        </div>
      )}
    </div>
  )
}
