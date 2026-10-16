import { ChevronRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { LABOR_CONTRACT_TYPE, labelOf } from '@/shared/constants/statuses'
import { ChartCard } from '@/shared/ui/chart'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { useExpiringLaborContracts } from '../hooks/use-expiring-labor-contracts'
import type { ExpiringLaborContract } from '../types/labor-contract'
import { countByLevel, describeDaysLeft } from '../utils/labor-contract-expiry'

interface ExpiringLaborContractsCardProps {
  /** Ô span trên lưới của trang Tổng quan. */
  className?: string
}

/**
 * HĐLĐ sắp hết / đã hết hạn trong phạm vi người xem (duoc-CR-620).
 *
 * Nơi gọi chỉ dựng thẻ khi có `labor_contract.read` — hợp đồng mang lương nên
 * người không có quyền thì không thấy cả cái khung, khác thẻ «Hồ sơ cần bổ sung»
 * vẫn hiện câu «không có quyền».
 *
 * Hết hạn sớm nhất lên đầu, kể cả HĐ đã quá hạn: người đó vẫn đi làm mà không có
 * hợp đồng, phải nằm trên cùng cho tới khi Nhân sự lập HĐ mới hoặc chấm dứt. Luật
 * ai bị báo (đã có HĐ nối tiếp, đã nghỉ việc thì thôi) ở backend `expiry_service`.
 */
export function ExpiringLaborContractsCard({ className }: ExpiringLaborContractsCardProps) {
  const query = useExpiringLaborContracts(true)
  const items = query.data?.items ?? []
  const warnDays = query.data?.warn_days ?? 30
  const dangerDays = query.data?.danger_days ?? 15
  const counts = countByLevel(items)

  const description = counts.total
    ? [
        `${counts.total} hợp đồng hết hạn trong ${warnDays} ngày tới hoặc đã quá hạn`,
        counts.overdue ? `${counts.overdue} đã quá hạn` : '',
        `đỏ: còn ≤ ${dangerDays} ngày, tới hạn phải báo trước cho người lao động`,
      ]
        .filter(Boolean)
        .join(' · ')
    : `Không có hợp đồng nào hết hạn trong ${warnDays} ngày tới.`

  //  Thẻ CẢNH BÁO mà tải hỏng thì không được nói «không có gì» — đó là trấn an giả,
  //  đúng lúc có thể đang có hợp đồng quá hạn. `ChartCard` không có trạng thái lỗi riêng.
  if (query.isError) {
    return (
      <ChartCard
        className={className}
        title="Hợp đồng lao động sắp hết hạn"
        isEmpty
        emptyLabel="Không tải được danh sách hợp đồng sắp hết hạn. Tải lại trang để thử lại."
      >
        <div />
      </ChartCard>
    )
  }

  return (
    <ChartCard
      className={className}
      title="Hợp đồng lao động sắp hết hạn"
      description={description}
      loading={query.isLoading}
      isEmpty={!query.isLoading && counts.total === 0}
      emptyLabel="Chưa có hợp đồng nào cần gia hạn."
    >
      {/* Danh sách tự cuộn: trang Tổng quan là chỗ liếc, không phải chỗ đọc 50 dòng. */}
      <ul className="max-h-80 divide-y overflow-y-auto">
        {items.map((item) => (
          <ExpiringRow key={item.id} item={item} />
        ))}
      </ul>
    </ChartCard>
  )
}

function ExpiringRow({ item }: { item: ExpiringLaborContract }) {
  const typeLabel = labelOf(LABOR_CONTRACT_TYPE, String(item.contract_type)) || '—'
  return (
    <li>
      <Link
        to={`${appRoutes.hr.employeeDetail(item.employee_id)}?tab=labor-contracts`}
        className="-mx-2 flex items-center justify-between gap-3 rounded-md px-2 py-2.5 transition-colors hover:bg-accent"
      >
        <div className="min-w-0">
          <p className="truncate text-sm font-medium">
            {item.employee_name}
            {item.employee_code && (
              <span className="font-normal text-muted-foreground"> · {item.employee_code}</span>
            )}
          </p>
          <p className="truncate text-xs text-muted-foreground">
            {item.contract_no || item.code} · {typeLabel} · hết {formatDate(item.end_date)}
          </p>
        </div>
        <span className="flex shrink-0 items-center gap-1">
          <span
            className={cn(
              'rounded-full px-2.5 py-0.5 text-xs font-semibold whitespace-nowrap',
              item.level === 'danger'
                ? 'bg-destructive/10 text-destructive'
                : 'bg-warning/15 text-warning',
            )}
          >
            {describeDaysLeft(item.days_left)}
          </span>
          <ChevronRight className="size-4 text-muted-foreground" aria-hidden />
        </span>
      </Link>
    </li>
  )
}
