import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { workScheduleApi } from '../api/work-schedule-api'
import { workShiftApi } from '../api/work-shift-api'
import type { WorkShiftBody, WorkShiftBulkBody, WorkShiftCopyWeekBody } from '../types/work-shift'

/**
 * Hook của XẾP CA THEO NGÀY (duoc-CR-761). Mọi lượt ghi — THÀNH CÔNG HAY LỖI (`onSettled`) — đều nạp lại lưới Xem lịch
 * (mọi tuần trong bộ nhớ) và "Ca của tôi": lỗi 409 (người khác vừa xếp, ngày vừa có đơn nghỉ) nghĩa là lưới đang cũ, phải
 * làm tươi để người dùng thấy đúng trạng thái trước khi thử lại.
 */

function useInvalidateShifts() {
  const client = useQueryClient()
  return () =>
    Promise.all([
      client.invalidateQueries({ queryKey: queryKeys.hr.workRosterRoot() }),
      client.invalidateQueries({ queryKey: queryKeys.hr.workShiftsRoot() }),
    ])
}

/**
 * Ca CỦA TÔI trong `[from, to]` — thẻ Trang cá nhân. `keepPreviousData`: bấm sang tuần khác không chớp trắng.
 * `refreshStamp` (id thông báo "ca" mới nhất) nằm trong khóa: chuông báo ca vừa đổi là thẻ tự nạp lại, không cần effect.
 */
export function useMyWorkShifts(fromDate: string, toDate: string, options: { enabled?: boolean; refreshStamp?: number } = {}) {
  return useQuery({
    queryKey: queryKeys.hr.myWorkShifts(fromDate, toDate, options.refreshStamp ?? 0),
    queryFn: () => workShiftApi.getMine({ from_date: fromDate, to_date: toDate }),
    placeholderData: keepPreviousData,
    retry: false,
    enabled: options.enabled ?? true,
  })
}

/**
 * Mẫu lịch đang áp của một nhân sự TẠI một ngày — để hộp xếp ca điền sẵn giờ mẫu tuần (kèm nghỉ trưa). Chỉ gọi khi
 * ô chưa có ca riêng. Lỗi (404 ngoài phạm vi…) thì hộp tự lùi về giờ vào–ra của ô lưới, không cần báo.
 */
export function useEffectiveScheduleOn(employeeId: number, onDate: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.workScheduleEffectiveOn(employeeId, onDate),
    queryFn: () => workScheduleApi.getEffective(employeeId, onDate),
    enabled: enabled && employeeId > 0 && onDate !== '',
    retry: false,
    staleTime: 60_000,
  })
}

export function useSaveWorkShift() {
  const invalidate = useInvalidateShifts()
  return useMutation({
    mutationFn: (vars: { employeeId: number; workDate: string; body: WorkShiftBody }) =>
      workShiftApi.save(vars.employeeId, vars.workDate, vars.body),
    onSettled: () => void invalidate(),
  })
}

export function useClearWorkShift() {
  const invalidate = useInvalidateShifts()
  return useMutation({
    mutationFn: (vars: { employeeId: number; workDate: string }) => workShiftApi.clear(vars.employeeId, vars.workDate),
    onSettled: () => void invalidate(),
  })
}

export function useBulkWorkShift() {
  const invalidate = useInvalidateShifts()
  return useMutation({
    mutationFn: (body: WorkShiftBulkBody) => workShiftApi.bulk(body),
    onSettled: () => void invalidate(),
  })
}

export function useCopyWorkShiftWeek() {
  const invalidate = useInvalidateShifts()
  return useMutation({
    mutationFn: (body: WorkShiftCopyWeekBody) => workShiftApi.copyWeek(body),
    onSettled: () => void invalidate(),
  })
}
