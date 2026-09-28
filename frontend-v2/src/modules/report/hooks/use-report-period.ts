import { useUrlParamState } from '@/shared/hooks/use-url-param-state'

export const ALL_COMPANY = 'all'
/** Số năm lùi lại trong ô chọn năm. */
const YEAR_SPAN = 5

/**
 * Kỳ báo cáo (năm + công ty) của các trang trong phân hệ Báo cáo — lưu trên URL
 * nên chép link là người nhận thấy đúng kỳ đang xem.
 *
 * Năm gõ tay trên URL sai dạng / ngoài dải thì quay về năm nay, không gọi API
 * với `year=NaN`.
 */
export function useReportPeriod() {
  const thisYear = new Date().getFullYear()
  const [yearParam, setYear] = useUrlParamState('year', String(thisYear))
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL_COMPANY)

  const parsed = Number(yearParam)
  const year =
    Number.isInteger(parsed) && parsed <= thisYear && parsed > thisYear - 50 ? parsed : thisYear
  const years = Array.from({ length: YEAR_SPAN }, (_, i) => thisYear - i)
  if (!years.includes(year)) years.push(year)

  return {
    year,
    years,
    setYear,
    companyId,
    setCompanyId,
    /** `undefined` = tất cả công ty — dạng tham số API cần. */
    company: companyId === ALL_COMPANY ? undefined : companyId,
  }
}

export type ReportPeriod = ReturnType<typeof useReportPeriod>
