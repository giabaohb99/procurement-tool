import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import type { DocumentDashboard } from '../types/document-dashboard'

/** Bộ lọc của thanh trên cùng trang. Bỏ trống hết = toàn bộ phạm vi xem được. */
export interface DashboardParams {
  company_id?: number
  department_id?: number
  /** `YYYY-MM-DD`. Lọc theo NGÀY LẬP văn bản, không phải ngày hiệu lực. */
  from_date?: string
  to_date?: string
}

/** Số liệu trang tổng quan Văn thư. Một lần gọi cho cả trang. */
export function useDocumentDashboard(params: DashboardParams = {}) {
  return useQuery({
    queryKey: queryKeys.document.dashboard({ ...params }),
    queryFn: () => apiGet<DocumentDashboard>('/api/documents/dashboard', { params }),
    //  Giữ số liệu cũ trong lúc đổi bộ lọc: mất đi một nhịp là năm thẻ KPI và
    //  ba biểu đồ cùng nháy về khung xám rồi hiện lại, cả trang giật một cái.
    placeholderData: keepPreviousData,
  })
}
