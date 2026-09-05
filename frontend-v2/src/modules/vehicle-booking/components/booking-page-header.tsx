import { ArrowLeft } from 'lucide-react'
import type { ReactNode } from 'react'

import { Button } from '@/shared/ui/button'

/**
 * Tiêu đề chuẩn cho các trang phân hệ Đặt xe: nút back (icon) bên trái · tiêu đề ·
 * badge (tùy chọn) · đệm giãn · cụm nút thao tác dồn phải. Giống bản Yêu cầu báo giá.
 */
export function BookingPageHeader({
  title,
  onBack,
  badge,
  actions,
}: {
  title: string
  onBack: () => void
  badge?: ReactNode
  actions?: ReactNode
}) {
  return (
    <div className="mb-3 flex flex-wrap items-center gap-3">
      <Button variant="outline" size="icon" aria-label="Quay lại" onClick={onBack}>
        <ArrowLeft className="size-4" />
      </Button>
      <h1 className="text-xl font-semibold tracking-tight text-navy dark:text-foreground">{title}</h1>
      {badge}
      <div className="min-w-4 flex-1" />
      {actions && <div className="flex flex-wrap items-center justify-end gap-2">{actions}</div>}
    </div>
  )
}
