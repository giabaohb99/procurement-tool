import { useQuery } from '@tanstack/react-query'

import { apiGet } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import type { SupplierSurveys } from '../types/supplier-survey'

interface UseSupplierSurveysParams {
  /** Mã số thuế — khóa bắt dòng KSNCC. Rỗng thì backend chỉ bắt theo mã NCC. */
  taxCode: string
  /** Mã (viết tắt) NCC — khóa bắt dòng KSSP. */
  supplierCode: string
}

/**
 * Toàn bộ dòng khảo sát dính tới một nhà cung cấp.
 *
 * Backend trả MỘT LẦN cả hai nhóm, không phân trang — nên lọc và cắt trang đều
 * làm ở phía giao diện.
 */
export function useSupplierSurveys(
  { taxCode, supplierCode }: UseSupplierSurveysParams,
  options: { enabled?: boolean } = {},
) {
  const params = { tax_code: taxCode, supplier_code: supplierCode }

  return useQuery({
    queryKey: queryKeys.production.supplierSurveys(params),
    queryFn: () => apiGet<SupplierSurveys>('/api/survey-report/by-supplier', { params }),
    // Backend chặn `survey.read`; không quyền mà vẫn gọi là ăn toast 403 khi mở tab.
    enabled: (options.enabled ?? true) && Boolean(taxCode || supplierCode),
  })
}
