import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'
import { usePermission } from '@/core/authorization/use-permission'
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

/** Số liệu trang tổng quan Văn thư. Một lần gọi cho cả trang.
 *
 * ⚠️ **Tắt khi thiếu `document.read`.** Tổng quan là trang mặc định của phân hệ,
 * mà cửa vào phân hệ mở cho cả người KHÔNG có quyền trên văn bản — người duyệt
 * trong luồng và người chỉ giữ sổ (xem `module-visibility.ts`). Không có nhánh
 * tắt thì họ vừa bấm vào Văn thư là ăn ngay một toast **403** của
 * `/api/documents/dashboard`, trước khi kịp thấy menu có mục nào dành cho mình.
 */
export function useDocumentDashboard(params: DashboardParams = {}) {
  const { can } = usePermission()

  return useQuery({
    queryKey: queryKeys.document.dashboard({ ...params }),
    queryFn: () => apiGet<DocumentDashboard>('/api/documents/dashboard', { params }),
    //  Giữ số liệu cũ trong lúc đổi bộ lọc: mất đi một nhịp là năm thẻ KPI và
    //  ba biểu đồ cùng nháy về khung xám rồi hiện lại, cả trang giật một cái.
    placeholderData: keepPreviousData,
    enabled: can('document', 'read'),
  })
}
