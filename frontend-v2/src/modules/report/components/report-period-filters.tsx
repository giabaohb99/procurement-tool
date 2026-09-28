import type { ReactNode } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

import { ALL_COMPANY, type ReportPeriod } from '../hooks/use-report-period'

interface ReportPeriodFiltersProps {
  period: ReportPeriod
  /** Ô lọc riêng của trang, đứng TRƯỚC hai ô kỳ. */
  children?: ReactNode
  /** Nguồn dữ liệu không lọc theo công ty (vd Báo cáo khảo sát) — ẩn ô đó đi cho khỏi nói dối. */
  hideCompany?: boolean
}

/** Bộ lọc kỳ một hàng ở đầu trang báo cáo: [ô riêng của trang] · Công ty · Năm. */
export function ReportPeriodFilters({ period, children, hideCompany = false }: ReportPeriodFiltersProps) {
  const { can } = usePermission()
  //  Ô công ty mượn danh mục của Nhân sự — thiếu quyền thì tắt hẳn, kẻo mở
  //  trang là ăn toast 403.
  const canReadCompany = !hideCompany && can('company', 'read')
  const { data: companies } = useCompanies(
    { page_size: 500, is_active: true },
    { enabled: canReadCompany },
  )

  return (
    <div className="flex flex-wrap gap-2 max-md:w-full">
      {children}
      {canReadCompany && (
        <Select value={period.companyId} onValueChange={period.setCompanyId}>
          <SelectTrigger className="w-52 max-md:min-w-0 max-md:flex-1" aria-label="Công ty">
            <SelectValue placeholder="Công ty" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ALL_COMPANY}>Tất cả công ty</SelectItem>
            {companies?.items.map((item) => (
              <SelectItem key={item.id} value={String(item.id)}>
                {item.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
      <Select value={String(period.year)} onValueChange={period.setYear}>
        <SelectTrigger className="w-32" aria-label="Năm">
          <SelectValue placeholder="Năm" />
        </SelectTrigger>
        <SelectContent>
          {period.years.map((y) => (
            <SelectItem key={y} value={String(y)}>
              Năm {y}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
