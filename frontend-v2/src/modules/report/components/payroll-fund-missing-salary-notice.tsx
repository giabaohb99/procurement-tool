import { TriangleAlert } from 'lucide-react'

import { formatQuantity } from '@/shared/utils/format-money'

import type { ReportMeta } from '../types/report-analytics'

/** `meta` của `/api/payroll-fund/summary` — thêm số người đang làm chưa nhập lương ở hồ sơ. */
type PayrollFundMeta = ReportMeta & { people_without_salary?: number | null }

/**
 * Dòng nhắc dưới thẻ KPI của Quỹ lương (duoc-CR-693): quỹ lương cộng ô lương + phụ cấp nhập ở
 * hồ sơ từng người, nên người đang làm mà chưa ai nhập lương KHÔNG nằm trong số — không nói ra
 * thì người xem tưởng quỹ lương đã đủ. Vắng khóa (máy chủ không trả) hoặc bằng 0 thì không hiện gì.
 */
export function PayrollFundMissingSalaryNotice({ meta }: { meta: ReportMeta }) {
  const count = (meta as PayrollFundMeta).people_without_salary
  if (!count || count <= 0) return null
  return (
    <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
      <TriangleAlert className="mt-px size-3.5 shrink-0 text-amber-600" aria-hidden />
      <span>{formatQuantity(count)} người đang làm chưa nhập lương — quỹ lương chưa gồm họ.</span>
    </p>
  )
}
