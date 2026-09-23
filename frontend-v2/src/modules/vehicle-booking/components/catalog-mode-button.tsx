import type { ReactNode } from 'react'

import { cn } from '@/shared/utils/cn'

/**
 * Nút CHỌN MỘT TRONG HAI của biểu mẫu danh mục Đặt xe (Nội bộ / Thuê ngoài,
 * Doanh nghiệp / Cá nhân).
 *
 * Dùng chung cho biểu mẫu Xe và Tài xế — trước đây mỗi tệp chép một bản giống
 * hệt nhau.
 *
 * ⚠️ `disabled` ở đây chỉ dành cho lúc ĐANG GỬI. Ô đã chốt sau khi tạo thì
 * đừng dựng nút mờ: nút mờ vẫn trông như bấm được và người dùng bấm hoài không
 * thấy gì xảy ra. Hiện giá trị đã chốt bằng chữ (`ReadOnlyValue`) kèm một câu
 * nói rõ vì sao — xem `vehicle-source-section.tsx`.
 */
export function CatalogModeButton({
  active,
  tone,
  disabled,
  onClick,
  children,
}: {
  active: boolean
  tone: 'blue' | 'amber'
  disabled?: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'flex h-10 items-center justify-center rounded-lg text-sm font-semibold transition-colors',
        'disabled:cursor-not-allowed disabled:opacity-60',
        !active && 'border border-input bg-background text-muted-foreground hover:bg-accent',
        active && tone === 'blue' && 'border-2 border-blue-500 bg-blue-50 text-blue-600 dark:bg-blue-950/40',
        active && tone === 'amber' && 'border-2 border-amber-500 bg-amber-50 text-amber-600 dark:bg-amber-950/40',
      )}
    >
      {children}
    </button>
  )
}
