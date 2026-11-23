/**
 * duoc-CR-784 — dòng tóm tắt "Mã đã chọn · Sản phẩm bị ảnh hưởng" nằm TRONG thanh công cụ của bảng mã đã chọn (người chủ
 * chốt 20/11/2026: bỏ bốn thẻ KPI của bản mẫu, hai số còn giữ thì đưa vào bảng, không để thành thẻ riêng).
 */
import type { PackagingImpactKpis } from '../types/packaging-cost-types'
import { describeImpactSummaryDetail } from '../utils/packaging-impact-print'

interface PackagingImpactSummaryProps {
  kpis: PackagingImpactKpis | undefined
}

export function PackagingImpactSummary({ kpis }: PackagingImpactSummaryProps) {
  if (!kpis) return null
  const detail = describeImpactSummaryDetail(kpis)

  return (
    <p className="text-sm text-muted-foreground">
      Mã đã chọn <b className="text-foreground tabular-nums">{kpis.selected_count}</b>
      {detail && ` (${detail})`}
      <span className="mx-2">·</span>
      Sản phẩm bị ảnh hưởng <b className="text-foreground tabular-nums">{kpis.affected_products}</b>
    </p>
  )
}
