import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { purchaseDocumentApi } from '../api/purchase-document-api'

/**
 * Sáu danh sách của phân hệ Thu mua. Tất cả đều CHỈ ĐỌC ở đợt này — thêm/sửa
 * chứng từ vẫn nằm ở bản `frontend` cũ cho tới khi màn chi tiết được dời qua.
 *
 * `keepPreviousData`: đổi trang hay đổi bộ lọc thì giữ bảng cũ trên màn hình
 * thay vì nháy sang khung rỗng rồi vẽ lại.
 */
function withDefaults(params: ListParams): ListParams {
  return { page: 1, page_size: appConfig.defaultPageSize, ...params }
}

export function usePurchaseRequests(params: ListParams = {}) {
  const query = withDefaults(params)
  return useQuery({
    queryKey: queryKeys.procurement.purchaseRequests(query),
    queryFn: () => purchaseDocumentApi.listPurchaseRequests(query),
    placeholderData: keepPreviousData,
  })
}

export function useSurveyRequests(params: ListParams = {}) {
  const query = withDefaults(params)
  return useQuery({
    queryKey: queryKeys.procurement.surveyRequests(query),
    queryFn: () => purchaseDocumentApi.listSurveyRequests(query),
    placeholderData: keepPreviousData,
  })
}

export function usePurchaseOrders(params: ListParams = {}) {
  const query = withDefaults(params)
  return useQuery({
    queryKey: queryKeys.procurement.purchaseOrders(query),
    queryFn: () => purchaseDocumentApi.listPurchaseOrders(query),
    placeholderData: keepPreviousData,
  })
}

export function useSurveys(params: ListParams = {}) {
  const query = withDefaults(params)
  return useQuery({
    queryKey: queryKeys.procurement.surveys(query),
    queryFn: () => purchaseDocumentApi.listSurveys(query),
    placeholderData: keepPreviousData,
  })
}

export function usePurchaseProgress(params: ListParams = {}) {
  const query = withDefaults(params)
  return useQuery({
    queryKey: queryKeys.procurement.purchaseProgress(query),
    queryFn: () => purchaseDocumentApi.listPurchaseProgress(query),
    placeholderData: keepPreviousData,
  })
}

export function useSurveyReport(params: ListParams = {}) {
  const query = withDefaults(params)
  return useQuery({
    queryKey: queryKeys.procurement.surveyReport(query),
    queryFn: () => purchaseDocumentApi.listSurveyReportLines(query),
    placeholderData: keepPreviousData,
  })
}
