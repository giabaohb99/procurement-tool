import type { ReactNode } from 'react'

import { FormSection, useFormSectionContext } from '@/shared/ui/form-section'
import { cn } from '@/shared/utils/cn'

interface EmployeeDetailBlockProps {
  /** Tiêu đề nhóm — thay cho tiêu đề cũ của khối bên trong (bị ẩn đi). */
  title: string
  /** Mặc định mở. Khối phụ / dài (phiên đăng nhập, lịch sử thao tác) có thể gập sẵn. */
  defaultOpen?: boolean
  /** Tóm tắt hiện cạnh tiêu đề khi đang gập. */
  summary?: ReactNode
  children: ReactNode
}

/**
 * Bọc một KHỐI không phải `FormSection` (bảng quá trình công tác, thẻ tài khoản, chữ ký,
 * danh sách người báo tin, lịch sử thao tác…) thành một nhóm phẳng gập / mở được như
 * accordion của ERPNext (duoc-CR-708, màn chi tiết nhân sự).
 *
 * Tiêu đề cũ của khối bên trong (`SectionHeading` hoặc `CardTitle`) bị ẩn bằng lớp phạm vi
 * để không ra hai tiêu đề chồng nhau; phần còn lại của hàng tiêu đề cũ (nút «Lưu danh sách»,
 * «Bắt đăng nhập lại»…) vẫn giữ nguyên.
 *
 * Ngoài màn dùng kiểu `flat` (vd Trang cá nhân dùng lại cùng component con) thì KHÔNG bọc
 * gì cả — khối hiện y như cũ.
 */
export function EmployeeDetailBlock({
  title,
  defaultOpen,
  summary,
  children,
}: EmployeeDetailBlockProps) {
  const { variant } = useFormSectionContext()
  if (variant !== 'flat') return <>{children}</>

  return (
    <FormSection title={title} defaultOpen={defaultOpen} summary={summary}>
      <div
        className={cn(
          'col-span-full min-w-0',
          '[&_[data-slot=card-title]]:hidden [&_[data-slot=section-heading]]:hidden',
          //  Đầu thẻ CHỈ chứa tiêu đề thì ẩn cả đầu thẻ — không thì còn một khoảng trống
          //  (đệm + gap của thẻ) ngay dưới tiêu đề nhóm. Đầu thẻ có thêm nút thì giữ.
          '[&_[data-slot=card-header]:has(>[data-slot=section-heading]:only-child)]:hidden',
          '[&_[data-slot=card-header]:has(>[data-slot=card-title]:only-child)]:hidden',
        )}
      >
        {children}
      </div>
    </FormSection>
  )
}
