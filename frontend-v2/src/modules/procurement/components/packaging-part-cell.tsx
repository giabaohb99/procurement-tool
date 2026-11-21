/**
 * duoc-CR-784 — ô THÀNH PHẦN của bảng sản phẩm (bám `partCell` của bản mẫu): mã trên, giá dưới — giá đổi
 * thì "cũ → mới" với số mới tô theo chiều tăng / giảm; chưa có giá thì nói thẳng "chưa có giá". Mã đang
 * được chọn tô nền nổi để mắt dò ra ngay dòng nào bị mã đó kéo giá.
 */
import { cn } from '@/shared/utils/cn'

import type { PackagingPart } from '../types/packaging-cost-types'
import { formatPackagingPrice, packagingDiffTone } from '../utils/packaging-price-format'
import { PackagingCodeLink } from './packaging-code-link'

export function PackagingPartCell({
  part,
  linkCode = false,
}: {
  part: PackagingPart | undefined
  /** Mã bấm được → Lịch sử mua hàng của mã đó (bảng Tổng hợp theo sản phẩm). */
  linkCode?: boolean
}) {
  if (!part?.code) return <span className="text-muted-foreground">—</span>

  const current = part.applied ?? part.new
  const changed = part.old != null && current != null && Math.abs(current - part.old) > 1e-9

  return (
    <div
      className={cn(
        'leading-tight',
        part.selected && '-mx-1 rounded bg-amber-100 px-1 py-0.5 dark:bg-amber-900',
      )}
    >
      {linkCode ? (
        <PackagingCodeLink code={part.code} className="text-xs font-medium" />
      ) : (
        <div className="text-xs font-medium tabular-nums">{part.code}</div>
      )}
      <div className="text-xs tabular-nums">
        {current == null ? (
          <span className="text-muted-foreground">chưa có giá</span>
        ) : changed ? (
          <>
            <span className="text-muted-foreground">{formatPackagingPrice(part.old)} →</span>{' '}
            <span className={cn('font-semibold', packagingDiffTone(current - (part.old ?? 0)))}>
              {formatPackagingPrice(current)}
            </span>
          </>
        ) : (
          formatPackagingPrice(current)
        )}
      </div>
    </div>
  )
}
