import { ArrowLeft } from 'lucide-react'
import type { ReactNode } from 'react'

import { Button } from '@/shared/ui/button'

/**
 * Tiêu đề chuẩn cho các trang phân hệ Duyệt dấu: nút back (icon) bên trái · tiêu
 * đề · badge (tùy chọn) · đệm giãn · cụm nút thao tác dồn phải.
 */
export function SealPageHeader({
  title,
  subtitle,
  onBack,
  badge,
  actions,
}: {
  title: string
  subtitle?: string
  onBack: () => void
  badge?: ReactNode
  actions?: ReactNode
}) {
  return (
    <div className="mb-3 flex flex-wrap items-center gap-3">
      <Button variant="outline" size="icon" aria-label="Quay lại" onClick={onBack}>
        <ArrowLeft className="size-4" />
      </Button>
      <div className="min-w-0">
        <h1 className="truncate text-xl font-semibold tracking-tight text-navy dark:text-foreground">
          {title}
        </h1>
        {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
      </div>
      {badge}
      <div className="min-w-4 flex-1" />
      {actions && <div className="flex flex-wrap items-center justify-end gap-2">{actions}</div>}
    </div>
  )
}
