import { Printer } from 'lucide-react'

import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { ReportPrLinesTab } from '../components/report-pr-lines-tab'

const ALL_COMPANY = 'all'
const ALL_YEAR = 'all'

/**
 * Trang riêng của báo cáo "Chi tiết YC mua hàng" (bao-CR-296/299) — nội dung
 * dùng chung `ReportPrLinesTab` với tab cùng tên trong Báo cáo mua hàng, chỉ
 * thêm bộ lọc Năm / Công ty của riêng trang và nút In.
 *
 * Đổi Năm / Công ty là react-query tự tải lại, không có nút "Lọc" (giống trang
 * Báo cáo mua hàng).
 */
export function PrLinesReportPage() {
  const thisYear = new Date().getFullYear()
  const [year, setYear] = useUrlParamState('year', String(thisYear))
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL_COMPANY)

  const company = companyId === ALL_COMPANY ? undefined : companyId
  const { data: companies } = useCompanies({ page_size: 500, is_active: true })

  const yearLabel = year === ALL_YEAR ? 'Tất cả' : `Năm ${year}`
  const companyLabel =
    companies?.items.find((item) => String(item.id) === companyId)?.name ?? 'Tất cả công ty'

  return (
    <PageContainer>
      <PageHeader
        title="Chi tiết YC mua hàng"
        description={
          <span>
            Kỳ: {yearLabel} · {companyLabel}
          </span>
        }
        actions={
          <div className="flex flex-wrap items-center gap-2 print:hidden">
            <Select value={companyId} onValueChange={setCompanyId}>
              <SelectTrigger className="w-52">
                <SelectValue placeholder="Công ty" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_COMPANY}>Tất cả công ty</SelectItem>
                {(companies?.items ?? []).map((item) => (
                  <SelectItem key={item.id} value={String(item.id)}>
                    {item.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={year} onValueChange={setYear}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Năm" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_YEAR}>Tất cả</SelectItem>
                {[thisYear, thisYear - 1, thisYear - 2].map((item) => (
                  <SelectItem key={item} value={String(item)}>
                    {item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button variant="ghost" onClick={() => window.print()}>
              <Printer />
              In
            </Button>
          </div>
        }
      />

      <ReportPrLinesTab year={year} companyId={company} />
    </PageContainer>
  )
}
