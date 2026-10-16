import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { laborContractApi } from '../api/labor-contract-api'

/**
 * HĐLĐ sắp hết / đã hết hạn (duoc-CR-620). Chỉ nạp khi `enabled` (có `labor_contract.read`) —
 * không có quyền mà vẫn gọi thì người xem Tổng quan Nhân sự ăn toast 403 ngay lúc mở trang.
 */
export function useExpiringLaborContracts(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.laborContractsExpiring(),
    queryFn: () => laborContractApi.listExpiring(),
    enabled,
  })
}
