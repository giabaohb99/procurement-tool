/**
 * duoc-CR-784 — ba THẺ NỔI đầu màn Tác động giá: "Mã đã chọn", "Sản phẩm bị ảnh hưởng" và "Tăng nhiều nhất /thùng"
 * (người chủ chốt 23/11/2026: dòng chữ tóm tắt khó đọc, đổi sang thẻ như trang Lịch sử mua hàng — viền trái màu nhấn,
 * ô biểu tượng nền nhạt, số to đậm; chỉ ba thẻ này, không đưa lại "Sản phẩm tăng chi phí" / "giảm"). Số lấy từ `kpis`
 * nên luôn tính trên TOÀN BỘ tập bị ảnh hưởng, không đổi theo trang / từ khóa. Thẻ thứ ba bấm được: xếp bảng sản phẩm
 * theo chênh /thùng giảm dần và cuộn tới bảng, để bộ phận bán hàng tra ngay sản phẩm đó.
 */
import { ArrowDownWideNarrow, Package, TrendingUp, type LucideIcon } from 'lucide-react'

import { cn } from '@/shared/utils/cn'

import type { PackagingImpactKpis } from '../types/packaging-cost-types'
import {
  buildImpactSummaryCards,
  type ImpactSummaryCard,
  type ImpactSummaryCardKey,
} from '../utils/packaging-impact-print'
import { packagingDiffTone } from '../utils/packaging-price-format'

/** Biểu tượng + biến màu nhấn của từng thẻ. Thẻ "Tăng nhiều nhất" xanh lá: chi phí TĂNG = xanh (luật màu của hệ). */
const LOOK: Record<ImpactSummaryCardKey, { icon: LucideIcon; color: string }> = {
  selected: { icon: Package, color: 'var(--chart-1)' },
  affected: { icon: Package, color: 'var(--chart-4)' },
  'top-increase': { icon: TrendingUp, color: 'var(--color-emerald-600)' },
}

interface PackagingImpactSummaryProps {
  kpis: PackagingImpactKpis | undefined
  /** Số sản phẩm sau từ khóa / lọc nâng cao — CHỈ truyền khi đang lọc; thẻ "Sản phẩm bị ảnh hưởng" ghi "Đang lọc: x / M". */
  filteredTotal?: number
  /** Bấm thẻ "Tăng nhiều nhất" (chỉ có khi có sản phẩm tăng): màn xếp bảng sản phẩm + cuộn tới bảng. */
  onShowTopIncrease: () => void
}

function CardBody({ card }: { card: ImpactSummaryCard }) {
  const look = LOOK[card.key]
  const Icon = look.icon
  //  Câu dài ("Không có sản phẩm tăng") hạ cỡ chữ như thẻ lịch sử, số thì to đậm.
  const longValue = card.value.length > 12
  return (
    <>
      <div className="flex items-center gap-2">
        <span
          className="flex size-8 shrink-0 items-center justify-center rounded-lg"
          style={{ backgroundColor: `color-mix(in oklab, ${look.color} 16%, transparent)`, color: look.color }}
        >
          <Icon className="size-4" />
        </span>
        <span className="truncate text-[13px] font-medium text-muted-foreground">{card.label}</span>
        {card.product && (
          <span className="ml-auto flex shrink-0 items-center gap-1 text-xs font-medium text-muted-foreground group-hover:text-foreground">
            <ArrowDownWideNarrow className="size-3.5" />
            Xem
          </span>
        )}
      </div>
      <div className="flex items-baseline gap-1.5">
        <span
          className={cn(
            'font-bold tracking-tight tabular-nums',
            longValue ? 'text-base leading-snug text-muted-foreground' : 'text-2xl leading-none text-foreground',
            card.tone && packagingDiffTone(1),
          )}
          title={card.value}
        >
          {card.value}
        </span>
        {card.unit && <span className="text-xs text-muted-foreground">{card.unit}</span>}
      </div>
      {(card.sub || card.detail) && (
        <div className="flex min-w-0 flex-col gap-0.5 text-xs text-muted-foreground">
          {card.sub && <span className={cn(card.tone && packagingDiffTone(1))}>{card.sub}</span>}
          {card.detail && (
            <span className="truncate" title={card.detail}>
              {card.detail}
            </span>
          )}
        </div>
      )}
    </>
  )
}

export function PackagingImpactSummary({ kpis, filteredTotal, onShowTopIncrease }: PackagingImpactSummaryProps) {
  if (!kpis) return null
  const cards = buildImpactSummaryCards(kpis, filteredTotal)

  return (
    <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
      {cards.map((card) => {
        const color = LOOK[card.key].color
        const className = cn(
          'group flex min-w-0 flex-col gap-2 rounded-xl border border-l-4 bg-card p-3.5 text-left shadow-sm',
          card.product && 'cursor-pointer transition-shadow hover:shadow-md focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
        )
        const style = {
          borderLeftColor: color,
          backgroundImage: `linear-gradient(135deg, color-mix(in oklab, ${color} 7%, transparent), transparent 60%)`,
        }
        //  Có sản phẩm tăng → cả thẻ là một nút; không có thì chỉ là chữ (không giả vờ bấm được).
        return card.product ? (
          <button
            key={card.key}
            type="button"
            className={className}
            style={style}
            title="Xếp bảng sản phẩm theo chênh lệch /thùng giảm dần và cuộn tới bảng"
            onClick={onShowTopIncrease}
          >
            <CardBody card={card} />
          </button>
        ) : (
          <div key={card.key} className={className} style={style}>
            <CardBody card={card} />
          </div>
        )
      })}
    </div>
  )
}
