import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { leaveBalanceMatrixApi, type LeaveBalanceMatrixParams } from '../api/leave-balance-matrix-api'

/**
 * Ma trận "Theo nhân sự" của Quỹ phép năm (duoc-CR-717). Khóa nằm dưới `['hr','leave-balances']`
 * nên Cấp quỹ / điều chỉnh / duyệt đơn (đều dọn `hr.all`) làm mới luôn bảng này.
 *
 * `keepPreviousData`: đổi trang hay gõ tìm thì bảng giữ trang cũ tới khi trang mới về, không chớp
 * về khung xương — mà cột của bảng dựng theo `columns` nên chớp trắng là cả bảng nhảy bố cục.
 */
export function useLeaveBalanceMatrix(params: LeaveBalanceMatrixParams) {
  return useQuery({
    queryKey: queryKeys.hr.leaveBalanceMatrix({ ...params }),
    queryFn: () => leaveBalanceMatrixApi.get(params),
    placeholderData: keepPreviousData,
  })
}
