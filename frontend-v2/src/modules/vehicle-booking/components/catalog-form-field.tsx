import type { ReactNode } from 'react'

import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { cn } from '@/shared/utils/cn'

interface CatalogFormFieldProps {
  label: string
  required?: boolean
  /** Chiếm trọn hàng trong lưới 2 cột (địa chỉ, ghi chú dài). */
  fullWidth?: boolean
  /**
   * Dòng chú thích mờ DƯỚI ô nhập — nói thứ nhãn không nói đủ: đơn vị đang
   * tính, luật nghiệp vụ, hệ quả của việc bỏ trống.
   */
  hint?: ReactNode
  children: ReactNode
}

/**
 * Một ô nhập của biểu mẫu danh mục Đặt xe (Xe · Tài xế): nhãn + dấu sao bắt
 * buộc + ô nhập + chú thích.
 *
 * Dùng chung cho cả hai biểu mẫu — trước đây mỗi tệp tự chép một bản `Field`
 * giống hệt nhau, nên sửa khoảng cách nhãn ở màn này thì màn kia trôi đi một
 * kiểu khác.
 */
export function CatalogFormField({
  label,
  required,
  fullWidth,
  hint,
  children,
}: CatalogFormFieldProps) {
  return (
    <div className={cn('flex flex-col gap-1.5', fullWidth && 'sm:col-span-2')}>
      <Label>
        {label}
        {required && <RequiredMark />}
      </Label>
      {children}
      {hint && <p className="text-xs text-muted-foreground">{hint}</p>}
    </div>
  )
}
