/**
 * duoc-CR-784 — thẻ số liệu của Lịch sử mua hàng, trình bày y bản mẫu HTML (người chủ chốt 23/11/2026): thẻ nền trắng, viền
 * trên xanh lá thương hiệu, nhãn nhỏ, số to màu navy, một dòng phụ xám. Bộ thẻ đổi theo cách xem (một mã / nhiều mã /
 * theo sản phẩm), xem `buildHistorySummary`. Số tính trên TOÀN BỘ tập đã lọc, không phải trang đang xem.
 */
import { cn } from '@/shared/utils/cn'

import type { PackagingHistoryMode, PackagingHistoryStats } from '../types/packaging-cost-types'
import { buildHistorySummary } from '../utils/packaging-history-summary-items'
import { packagingDiffTone } from '../utils/packaging-price-format'

/** Từ chừng này ký tự trở lên thì dùng cỡ chữ nhỏ hơn để lọt thẻ hẹp (6 thẻ / hàng). */
const LONG_VALUE_LENGTH = 10

interface PackagingHistorySummaryProps {
  stats: PackagingHistoryStats | undefined
  /** Đúng một mã được chọn (có biểu đồ) — bật bộ thẻ giá. */
  singleCode: boolean
  mode: PackagingHistoryMode
  /** Số mã (hoặc mã sản phẩm) đã chọn; 0 = tất cả. */
  selectedCount: number
}

export function PackagingHistorySummary({
  stats,
  singleCode,
  mode,
  selectedCount,
}: PackagingHistorySummaryProps) {
  if (!stats) return null
  const items = buildHistorySummary(stats, { singleCode, mode, selectedCount })
  return (
    <div
      className={cn(
        'grid grid-cols-2 gap-3 md:grid-cols-3',
        items.length > 4 ? 'xl:grid-cols-6' : 'xl:grid-cols-4',
      )}
    >
      {items.map((item) => (
        <div
          key={item.label}
          className="flex min-w-0 flex-col rounded-lg border border-t-[3px] border-t-brand-green bg-card px-3.5 py-3 shadow-xs"
        >
          <span className="truncate text-xs font-semibold text-muted-foreground">{item.label}</span>
          <span
            className={cn(
              //  Giá trị dài ("1.900 – 2.800") thu cỡ chữ và được xuống dòng thay vì bị cắt "…".
              'mt-1 leading-tight font-bold tabular-nums break-words',
              item.value.length > LONG_VALUE_LENGTH ? 'text-lg' : 'text-[22px]',
              item.tone ? packagingDiffTone(item.tone === 'up' ? 1 : -1) : 'text-navy',
            )}
            title={item.value}
          >
            {item.value}
          </span>
          <span className="mt-0.5 text-xs break-words text-muted-foreground" title={item.sub}>
            {item.sub || '\u00a0'}
          </span>
        </div>
      ))}
    </div>
  )
}
