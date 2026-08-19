import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { purchaseReportApi, type ReportScope } from '../api/purchase-report-api'
import type { ReportMatrix } from '../types/purchase-report'

/**
 * Báo cáo mua hàng.
 *
 * Bản v1 có nút "Lọc" phải bấm mới tải; ở đây đổi năm / công ty là react-query
 * tự gọi lại, nên bỏ nút đó. Nút "Cập nhật" thì GIỮ vì nó không phải nạp lại
 * cùng số liệu: nó bắt backend TÍNH LẠI snapshot ma trận (`refresh=1`).
 *
 * `keepPreviousData` khắp nơi: báo cáo tải lâu, nháy sang khung rỗng mỗi lần
 * đổi bộ lọc là mất hẳn ngữ cảnh đang đọc.
 */
export function useProcurementReport(params: ReportScope & { month?: string }) {
  return useQuery({
    queryKey: queryKeys.procurement.reportProcurement(params),
    queryFn: () => purchaseReportApi.getProcurement(params),
    placeholderData: keepPreviousData,
  })
}

export function useReportMatrix(params: ReportScope) {
  return useQuery({
    queryKey: queryKeys.procurement.reportMatrix(params),
    queryFn: () => purchaseReportApi.getMatrix(params),
    placeholderData: keepPreviousData,
  })
}

/**
 * Nút "Cập nhật" — tính lại snapshot ngay rồi ghi thẳng kết quả vào cache.
 *
 * Không dùng `invalidateQueries`: lần gọi lại sẽ KHÔNG kèm `refresh=1` nên
 * backend trả đúng cái snapshot cũ vừa muốn bỏ đi.
 */
export function useRefreshReportMatrix(params: ReportScope) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => purchaseReportApi.getMatrix({ ...params, refresh: 1 }),
    onSuccess: (data: ReportMatrix) => {
      queryClient.setQueryData(queryKeys.procurement.reportMatrix(params), data)
    },
  })
}

export function useRequestMatrix(params: ReportScope & { kind: string }, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.procurement.reportRequestMatrix(params),
    queryFn: () => purchaseReportApi.getRequestMatrix(params),
    placeholderData: keepPreviousData,
    enabled,
  })
}

/**
 * Bảng phẳng theo khoảng ngày. `enabled` do chỗ gọi quyết: chưa chọn đủ hai đầu
 * ngày thì đừng gọi, backend chỉ trả mảng rỗng.
 */
export function useReportRange(
  endpoint: string,
  params: { date_from: string; date_to: string; company_id?: string; kind?: string },
  enabled: boolean,
) {
  return useQuery({
    queryKey: queryKeys.procurement.reportRange(endpoint, params),
    queryFn: () => purchaseReportApi.getRange(endpoint, params),
    placeholderData: keepPreviousData,
    enabled,
  })
}

export function useShippingDetail(
  params: ReportScope & { carrier?: string; month?: string; page: number; page_size: number },
  enabled: boolean,
) {
  return useQuery({
    queryKey: queryKeys.procurement.reportShippingDetail(params),
    queryFn: () => purchaseReportApi.getShippingDetail(params),
    placeholderData: keepPreviousData,
    enabled,
  })
}

/** Chi phí theo ngày của một tháng. `month` rỗng = hộp thoại đang đóng. */
export function useDailyReport(month: string, companyId?: string) {
  const params = { month, company_id: companyId }
  return useQuery({
    queryKey: queryKeys.procurement.reportDaily(params),
    queryFn: () => purchaseReportApi.getDaily({ month, company_id: companyId }),
    enabled: !!month,
  })
}
