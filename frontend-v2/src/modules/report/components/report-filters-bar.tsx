import { Building2 } from 'lucide-react'
import type { ComponentType } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

import { ALL_COMPANY, type ReportFiltersState } from '../hooks/use-report-filters'
import type { ReportExtraFiltersProps, ReportPeriod } from '../types/report-analytics'
import { ReportPeriodControl } from './report-period-control'

interface ReportFiltersBarProps {
  filters: ReportFiltersState
  /** Kỳ ĐÃ TÍNH LẠI trả về cùng dữ liệu — `undefined` khi chưa có lượt gọi nào về. */
  period?: ReportPeriod
  hideCompany?: boolean
  ExtraFilters?: ComponentType<ReportExtraFiltersProps>
}

/**
 * Thanh lọc kỳ của trang báo cáo kiểu Haravan: [lọc riêng của trang] · nút Kỳ
 * báo cáo (preset + khoảng ngày + so sánh gộp vào MỘT popover, xem
 * `ReportPeriodControl`) · Công ty.
 *
 * `items-start` (không phải `items-center`): nút Kỳ mang thêm một dòng "So với
 * …" mờ NGAY DƯỚI nó, cao hơn một ô Select thường — canh theo mép TRÊN thì mọi
 * ô lọc trên hàng vẫn thẳng hàng đỉnh, không bị kéo lệch xuống giữa cụm.
 */
export function ReportFiltersBar({
  filters,
  period,
  hideCompany = false,
  ExtraFilters,
}: ReportFiltersBarProps) {
  const { can } = usePermission()
  //  Ô công ty mượn danh mục của Nhân sự — thiếu quyền thì tắt hẳn, kẻo mở
  //  trang là ăn toast 403.
  const canReadCompany = !hideCompany && can('company', 'read')
  const { data: companies } = useCompanies(
    { page_size: 500, is_active: true },
    { enabled: canReadCompany },
  )

  return (
    <div className="flex flex-wrap items-start gap-2">
      {ExtraFilters && <ExtraFilters />}

      <ReportPeriodControl
        preset={filters.preset}
        from={filters.from}
        to={filters.to}
        compare={filters.compare}
        period={period}
        onApply={filters.applyPeriod}
      />

      {canReadCompany && (
        <Select value={filters.companyId} onValueChange={filters.setCompanyId}>
          <SelectTrigger
            className="w-auto min-w-40 max-md:min-w-0 max-md:flex-1"
            aria-label="Công ty"
          >
            <Building2 className="size-4 shrink-0 text-muted-foreground" aria-hidden />
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
    </div>
  )
}
