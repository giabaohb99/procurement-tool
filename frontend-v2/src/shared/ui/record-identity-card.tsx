import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'

export interface IdentityChip {
  icon?: LucideIcon
  text: string
  /** `code` = chữ mono cho mã; `ok`/`muted` cho trạng thái. */
  tone?: 'code' | 'ok' | 'muted'
}

interface RecordIdentityCardProps {
  /** Ảnh đại diện / logo. Bỏ trống với danh mục không có ảnh (phòng ban…). */
  media?: ReactNode
  title: string
  chips?: IdentityChip[]
  /** Nút hành động bên phải (Lưu, Xóa…). */
  actions?: ReactNode
}

/**
 * "Thẻ danh tính" ở đầu mọi trang chi tiết: ảnh + tên + vài chip mô tả nhanh
 * (mã, chức vụ, trạng thái) để nhìn một cái là biết đang mở bản ghi nào.
 */
export function RecordIdentityCard({
  media,
  title,
  chips = [],
  actions,
}: RecordIdentityCardProps) {
  return (
    <Card className="mb-5 flex-row flex-wrap items-center gap-4 p-5">
      {media}

      <div className="min-w-0 flex-1">
        <h1 className="truncate text-lg font-semibold text-navy">{title}</h1>

        {chips.length > 0 && (
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {chips.map((chip) => (
              <Badge
                key={chip.text}
                variant={chip.tone === 'ok' ? 'default' : 'outline'}
                className={chip.tone === 'code' ? 'font-mono' : undefined}
              >
                {chip.icon && <chip.icon />}
                {chip.text}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </Card>
  )
}
