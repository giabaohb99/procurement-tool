import { TriangleAlert } from 'lucide-react'

import { formatQuantity } from '@/shared/utils/format-money'

import type { ReportMeta } from '../types/report-analytics'

/** `meta` của `/api/payroll-fund/summary` — thêm số người đang làm chưa có HĐLĐ hiệu lực. */
type PayrollFundMeta = ReportMeta & { people_without_contract?: number | null }

/**
 * Dòng nhắc dưới thẻ KPI của Quỹ lương (duoc-CR-692): quỹ lương chỉ cộng lương trên HĐLĐ đang
 * hiệu lực, nên người đang làm mà chưa có hợp đồng KHÔNG nằm trong số — không nói ra thì người
 * xem tưởng quỹ lương đã đủ. Backend chỉ trả `people_without_contract` khi người xem có
 * `employee.read`; vắng khóa hoặc bằng 0 thì không hiện gì.
 */
export function PayrollFundMissingContractNotice({ meta }: { meta: ReportMeta }) {
  const count = (meta as PayrollFundMeta).people_without_contract
  if (!count || count <= 0) return null
  return (
    <p className="flex items-start gap-1.5 text-xs text-muted-foreground">
      <TriangleAlert className="mt-px size-3.5 shrink-0 text-amber-600" aria-hidden />
      <span>
        {formatQuantity(count)} người đang làm chưa có hợp đồng lao động hiệu lực — quỹ lương chưa
        gồm họ.
      </span>
    </p>
  )
}
