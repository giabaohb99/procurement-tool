import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { reportSummaryApi, type ReportSummaryParams } from '../api/report-summary-api'

//  `keepPreviousData`: đổi năm / công ty mà biểu đồ nháy về khung rỗng là mất
//  ngữ cảnh đang so — giữ số cũ tới khi số mới về.

export function usePrLinesSummary(params: ReportSummaryParams) {
  return useQuery({
    queryKey: queryKeys.report.prLinesSummary(params),
    queryFn: () => reportSummaryApi.prLines(params),
    placeholderData: keepPreviousData,
  })
}

export function usePurchaseProgressSummary(params: ReportSummaryParams) {
  return useQuery({
    queryKey: queryKeys.report.purchaseProgressSummary(params),
    queryFn: () => reportSummaryApi.purchaseProgress(params),
    placeholderData: keepPreviousData,
  })
}

export function useSurveyProgressSummary(params: ReportSummaryParams) {
  return useQuery({
    queryKey: queryKeys.report.surveyProgressSummary(params),
    queryFn: () => reportSummaryApi.surveyProgress(params),
    placeholderData: keepPreviousData,
  })
}

export function useSurveyReportSummary(params: ReportSummaryParams) {
  return useQuery({
    queryKey: queryKeys.report.surveyReportSummary({ year: params.year }),
    queryFn: () => reportSummaryApi.surveyReport(params),
    placeholderData: keepPreviousData,
  })
}
