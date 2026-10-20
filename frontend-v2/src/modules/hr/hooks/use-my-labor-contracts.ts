import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { myLaborContractApi } from '../api/my-labor-contract-api'

/** HĐLĐ đã ký / chấm dứt / hết hạn của CHÍNH MÌNH (duoc-CR-652). */
export function useMyLaborContracts() {
  return useQuery({
    queryKey: queryKeys.hr.myLaborContracts(),
    queryFn: () => myLaborContractApi.list(),
  })
}
