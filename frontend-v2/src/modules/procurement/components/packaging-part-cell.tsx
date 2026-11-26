/**
 * duoc-CR-784 — ô THÀNH PHẦN của bảng sản phẩm (bám `partCell` của bản mẫu): mã trên, giá dưới — giá đổi
 * thì "cũ → mới" với số mới tô theo chiều tăng / giảm; chưa có giá thì nói thẳng "chưa có giá". Mã đang
 * được chọn tô nền nổi để mắt dò ra ngay dòng nào bị mã đó kéo giá.
 */
import { cn } from '@/shared/utils/cn'

import type { PackagingPart } from '../types/packaging-cost-types'
import { PackagingCodeLink } from './packaging-code-link'
import { PriceChangeText } from './packaging-price-cells'

export function PackagingPartCell({
  part,
  linkCode = false,
}: {
  part: PackagingPart | undefined
  /** Mã bấm được → Lịch sử mua hàng của mã đó (bảng Tổng hợp theo sản phẩm). */
  linkCode?: boolean
}) {
  if (!part?.code) return <span className="text-muted-foreground">—</span>

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
      <div className="text-xs">
        <PriceChangeText from={part.old} to={part.applied ?? part.new} />
      </div>
    </div>
  )
}
