import { Table2 } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Button } from '@/shared/ui/button'
import { PageHeader } from '@/shared/ui/page-header'

import type { ReportPeriod } from '../hooks/use-report-period'
import { ReportPeriodFilters } from './report-period-filters'

interface ReportChartPageHeaderProps {
  title: string
  description: string
  period: ReportPeriod
  /** Trang BẢNG gốc bên Thu mua — nơi soi từng dòng. */
  tablePath: string
  /** Nguồn không lọc theo công ty. */
  hideCompany?: boolean
}

/**
 * Đầu trang của một báo cáo BIỂU ĐỒ: tiêu đề · nút «Xem bảng chi tiết» · kỳ.
 *
 * Nút dẫn sang bảng mang theo `year` + `company_id`: trang bảng nào đọc hai
 * tham số đó từ URL thì mở đúng kỳ, trang nào không đọc thì bỏ qua vô hại.
 */
export function ReportChartPageHeader({
  title,
  description,
  period,
  tablePath,
  hideCompany = false,
}: ReportChartPageHeaderProps) {
  const qs = new URLSearchParams({ year: String(period.year) })
  if (period.company && !hideCompany) qs.set('company_id', period.company)

  return (
    <PageHeader
      title={title}
      description={<span className="max-md:hidden">{description}</span>}
      actions={
        <ReportPeriodFilters period={period} hideCompany={hideCompany}>
          <Button variant="outline" asChild>
            <Link to={`${tablePath}?${qs.toString()}`}>
              <Table2 />
              Xem bảng chi tiết
            </Link>
          </Button>
        </ReportPeriodFilters>
      }
    />
  )
}
