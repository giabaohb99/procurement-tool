/**
 * duoc-CR-784 — dòng KPI gọn của Lịch sử mua hàng (một dòng chữ, KHÔNG thẻ lớn — người chủ chốt 20/11/2026 chê thẻ to).
 * Số tính trên TOÀN BỘ tập đã lọc, không phải trang đang xem; xem `buildHistorySummary` để biết số nào chỉ có khi một mã.
 */
import { Loader2 } from 'lucide-react'

import type { PackagingHistoryStats } from '../types/packaging-cost-types'
import { buildHistorySummary } from '../utils/packaging-history'

interface PackagingHistorySummaryProps {
  stats: PackagingHistoryStats | undefined
  /** Đúng một mã được chọn (có biểu đồ) — bật nhóm số giá. */
  singleCode: boolean
  fetching?: boolean
}

export function PackagingHistorySummary({
  stats,
  singleCode,
  fetching,
}: PackagingHistorySummaryProps) {
  if (!stats) return null
  const items = buildHistorySummary(stats, singleCode)
  return (
    //  `basis-0` + `min-w-80`: dòng KPI co lại / xuống dòng trong khung để nút của bảng (Tải lại, Cột) vẫn nằm cùng hàng bên phải.
    <p className="flex min-w-80 flex-1 basis-0 flex-wrap items-center text-sm text-muted-foreground">
      {items.map((item, index) => (
        <span key={item.label}>
          {index > 0 && <span className="mx-1.5">·</span>}
          {item.label} <b className="text-foreground tabular-nums">{item.value}</b>
        </span>
      ))}
      {!singleCode && stats.purchase_count > 0 && (
        <span className="ml-2 text-xs">
          (chọn đúng một mã để xem giá bình quân, thấp nhất, cao nhất)
        </span>
      )}
      {fetching && <Loader2 className="ml-2 size-3.5 animate-spin" />}
    </p>
  )
}
