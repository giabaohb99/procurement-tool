/**
 * duoc-CR-784 — số liệu tóm tắt của Lịch sử mua hàng dạng THẺ NỔI (người chủ chốt 21/11/2026: dòng chữ cũ khó đọc, đổi
 * sang thẻ, làm nổi bật — mỗi thẻ một màu nhấn: viền trái + ô biểu tượng nền nhạt, số to đậm). Màu lấy từ bảng màu biểu đồ
 * của theme (`--chart-*`, `--primary`) nên đổi đúng theo sáng / tối. Số tính trên TOÀN BỘ tập đã lọc, không phải trang
 * đang xem; xem `buildHistorySummary` để biết số nào chỉ có khi một mã.
 */
import {
  ArrowDownToLine,
  ArrowUpToLine,
  Boxes,
  Calculator,
  CalendarRange,
  ShoppingCart,
  Truck,
  type LucideIcon,
} from 'lucide-react'

import { cn } from '@/shared/utils/cn'

import type { PackagingHistoryStats } from '../types/packaging-cost-types'
import { buildHistorySummary } from '../utils/packaging-history'

/** Biểu tượng + biến màu nhấn theo nhãn số liệu (nhãn đến từ `buildHistorySummary`). */
const LOOK: Record<string, { icon: LucideIcon; color: string }> = {
  'Số lần mua': { icon: ShoppingCart, color: 'var(--chart-1)' },
  'Tổng SL': { icon: Boxes, color: 'var(--chart-4)' },
  'Giá BQ gia quyền': { icon: Calculator, color: 'var(--primary)' },
  'Thấp nhất': { icon: ArrowDownToLine, color: 'var(--chart-3)' },
  'Cao nhất': { icon: ArrowUpToLine, color: 'var(--chart-2)' },
  'Số NCC': { icon: Truck, color: 'var(--chart-1)' },
  'Khoảng ngày': { icon: CalendarRange, color: 'var(--muted-foreground)' },
}

interface PackagingHistorySummaryProps {
  stats: PackagingHistoryStats | undefined
  /** Đúng một mã được chọn (có biểu đồ) — bật nhóm số giá. */
  singleCode: boolean
}

export function PackagingHistorySummary({ stats, singleCode }: PackagingHistorySummaryProps) {
  if (!stats) return null
  const items = buildHistorySummary(stats, singleCode)
  const pickOneHint =
    !singleCode && stats.purchase_count > 0
      ? 'Chọn đúng một mã để xem giá bình quân, thấp nhất, cao nhất'
      : undefined
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4 xl:grid-cols-7">
      {items.map((item, index) => {
        const look = LOOK[item.label] ?? { icon: ShoppingCart, color: 'var(--primary)' }
        const Icon = look.icon
        const longValue = item.value.length > 12
        return (
          <div
            key={item.label}
            className={cn(
              'flex min-w-0 flex-col gap-2 rounded-xl border border-l-4 bg-card p-3.5 shadow-sm',
              item.label === 'Khoảng ngày' && 'max-xl:col-span-2',
            )}
            style={{
              borderLeftColor: look.color,
              backgroundImage: `linear-gradient(135deg, color-mix(in oklab, ${look.color} 7%, transparent), transparent 60%)`,
            }}
          >
            <div className="flex items-center gap-2">
              <span
                className="flex size-8 shrink-0 items-center justify-center rounded-lg"
                style={{
                  backgroundColor: `color-mix(in oklab, ${look.color} 16%, transparent)`,
                  color: look.color,
                }}
              >
                <Icon className="size-4" />
              </span>
              <span className="truncate text-[13px] font-medium text-muted-foreground">{item.label}</span>
            </div>
            <span
              className={cn(
                'font-bold tracking-tight text-foreground tabular-nums',
                longValue ? 'text-base leading-snug' : 'text-2xl leading-none',
              )}
              title={item.value}
            >
              {item.value}
            </span>
            {index === 0 && pickOneHint && (
              <span className="text-xs text-muted-foreground">{pickOneHint}</span>
            )}
          </div>
        )
      })}
    </div>
  )
}
