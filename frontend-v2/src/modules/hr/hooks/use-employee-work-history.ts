import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { authService } from '@/core/auth/auth-service'
import { useAuthStore } from '@/core/auth/auth-store'
import { queryKeys } from '@/shared/constants/query-keys'
import { employeeWorkHistoryApi } from '../api/employee-work-history-api'
import type { EmployeeWorkHistoryPayload } from '../types/employee-work-history'

/** Dòng lịch sử của MỘT hồ sơ. `0` = chưa biết id (đang tải trang chi tiết). */
export function useEmployeeWorkHistory(employeeId: number) {
  return useQuery({
    queryKey: queryKeys.hr.employeeWorkHistory(employeeId),
    queryFn: () => employeeWorkHistoryApi.list(employeeId),
    enabled: employeeId > 0,
  })
}

/** Quá trình công tác của CHÍNH MÌNH — `/me/work-history`, Trang cá nhân dùng (phase 05). */
export function useMyWorkHistory() {
  return useQuery({
    queryKey: queryKeys.hr.myWorkHistory(),
    queryFn: () => employeeWorkHistoryApi.listMine(),
  })
}

/**
 * Dọn cache sau khi LƯU/ÁP một dòng.
 *
 * Luôn dọn `employeeWorkHistory(id)`. Khi dòng đã ÁP vào hồ sơ
 * (`applied_changes` không rỗng) thì dọn thêm đúng bốn nhánh mà hồ sơ có thể
 * vừa đổi: `employee(id)` (chip chức vụ/tình trạng ở thẻ tiêu đề),
 * `employeeDepartments(id)` (kiêm nhiệm), `employees()` (danh sách — tên/trạng
 * thái hiện ở đó), `myEmployee()` (Trang cá nhân nếu tự xem được hồ sơ mình,
 * vd quản trị hệ thống).
 */
/**
 * Low FE (code review 03/10/2026) — hồ sơ vừa áp thay đổi là CHÍNH hồ sơ của
 * người đang đăng nhập (chỉ xảy ra khi quản trị hệ thống tự sửa, A9/Q3 cho
 * phép ngoại lệ đó) thì phải làm mới CẢ thẻ «Quá trình công tác» ở Trang cá
 * nhân LẪN thông tin tài khoản đang đăng nhập — không thì sidebar/avatar vẫn
 * hiện chức vụ/phòng ban CŨ tới lần đăng nhập sau. `authService.me()` thất bại
 * thì bỏ qua (best-effort): không được chặn luồng áp hồ sơ vì một lần gọi lại
 * hồ sơ cá nhân không thành.
 */
async function refreshOwnProfileIfSelf(queryClient: QueryClient, employeeId: number) {
  const currentUser = useAuthStore.getState().user
  if (!currentUser || currentUser.employee_id !== employeeId) return

  void queryClient.invalidateQueries({ queryKey: queryKeys.hr.myWorkHistory() })
  try {
    const me = await authService.me()
    useAuthStore.getState().setUser(me)
  } catch {
    //  best-effort — xem docstring của hàm.
  }
}

function invalidateAfterChange(
  queryClient: QueryClient,
  employeeId: number,
  appliedToProfile: boolean,
) {
  void queryClient.invalidateQueries({ queryKey: queryKeys.hr.employeeWorkHistory(employeeId) })
  if (!appliedToProfile) return
  void queryClient.invalidateQueries({ queryKey: queryKeys.hr.employee(employeeId) })
  void queryClient.invalidateQueries({ queryKey: queryKeys.hr.employeeDepartments(employeeId) })
  void queryClient.invalidateQueries({ queryKey: queryKeys.hr.employees() })
  void queryClient.invalidateQueries({ queryKey: queryKeys.hr.myEmployee() })
  void refreshOwnProfileIfSelf(queryClient, employeeId)
}

/** Toast cảnh báo (không chặn) + toast kết quả áp, dùng chung cho lưu và áp. */
function notifySaveResult(warnings: string[], appliedChanges: string[]) {
  for (const warning of warnings) toast.warning(warning)
  if (appliedChanges.length > 0) {
    toast.success(`Đã áp vào hồ sơ: ${appliedChanges.join('; ')}`)
  } else {
    toast.success('Đã lưu quá trình công tác')
  }
}

export function useSaveEmployeeWorkHistory(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id?: number; payload: EmployeeWorkHistoryPayload }) =>
      id
        ? employeeWorkHistoryApi.update(employeeId, id, payload)
        : employeeWorkHistoryApi.create(employeeId, payload),
    onSuccess: (result) => {
      notifySaveResult(result.warnings, result.applied_changes)
      invalidateAfterChange(queryClient, employeeId, result.applied_changes.length > 0)
    },
  })
}

export function useDeleteEmployeeWorkHistory(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => employeeWorkHistoryApi.remove(employeeId, id),
    onSuccess: () => {
      toast.success('Đã xóa dòng quá trình công tác')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.employeeWorkHistory(employeeId) })
    },
  })
}

export function useApplyEmployeeWorkHistory(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => employeeWorkHistoryApi.apply(employeeId, id),
    onSuccess: (result) => {
      notifySaveResult([], result.applied_changes)
      invalidateAfterChange(queryClient, employeeId, true)
    },
  })
}
