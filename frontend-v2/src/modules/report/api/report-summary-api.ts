import { apiGet } from '@/core/api'

import type {
  PrLinesSummary,
  PurchaseProgressSummary,
  SurveyProgressSummary,
  SurveyReportSummary,
} from '../types/report-summary'

/** Kỳ báo cáo: `company_id` bỏ trống = tất cả công ty. */
export type ReportSummaryParams = {
  year: string
  company_id?: string
}

/**
 * Bốn đường `/summary` của màn biểu đồ. Ba đường đầu nhận `year` thẳng; Báo cáo
 * khảo sát không có tham số năm nên dịch sang khoảng `date_from`/`date_to`.
 */
export const reportSummaryApi = {
  prLines: (params: ReportSummaryParams) =>
    apiGet<PrLinesSummary>('/api/reports/pr-lines/summary', { params }),
  purchaseProgress: (params: ReportSummaryParams) =>
    apiGet<PurchaseProgressSummary>('/api/purchase-progress/summary', { params }),
  surveyProgress: (params: ReportSummaryParams) =>
    apiGet<SurveyProgressSummary>('/api/survey-progress/summary', { params }),
  //  Báo cáo khảo sát không lọc theo công ty ở backend — cố ý không gửi.
  surveyReport: ({ year }: ReportSummaryParams) =>
    apiGet<SurveyReportSummary>('/api/survey-report/summary', {
      params: { date_from: `${year}-01-01`, date_to: `${year}-12-31` },
    }),
}
