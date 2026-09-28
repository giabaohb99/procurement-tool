import { useMutation, useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { employeeApi } from '../api/employee-api'
import type { SelfContactPayload } from '../schemas/self-contact-schema'
import type { EmployeeContact } from '../types/employee'

/**
 * TỰ SỬA LIÊN HỆ ở Trang cá nhân (bao-CR-508) — ba ô liên hệ + người báo tin
 * của CHÍNH MÌNH, không cần khóa `employee.write`.
 */

/**
 * Nạp lại MỌI chỗ đang hiện liên hệ của người này sau khi họ tự sửa.
 *
 * ⚠️ Một thay đổi, bốn nơi đọc — sót chỗ nào là chỗ đó hiện số cũ tới lúc hết
 * `staleTime`, và người dùng tưởng lưu chưa ăn:
 * - `myEmployee` — Trang cá nhân (khóa cha, quét luôn `myEmployeeContacts`);
 * - `employee(id)` — màn hồ sơ ở phân hệ Nhân sự nếu đang mở ở tab khác (khóa
 *   cha, quét luôn `employeeContacts(id)`);
 * - `employees()` — các trang danh sách nhân sự (cột Số điện thoại). `{}` khớp
 *   từng phần với MỌI bộ tham số, nên một lời gọi là đủ;
 * - `auth.me` — số điện thoại ở thẻ «Tài khoản» đọc từ phiên đăng nhập.
 */
export function invalidateSelfContactQueries(queryClient: QueryClient, employeeId: number) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: queryKeys.hr.myEmployee() }),
    queryClient.invalidateQueries({ queryKey: queryKeys.hr.employee(employeeId) }),
    queryClient.invalidateQueries({ queryKey: queryKeys.hr.employees() }),
    queryClient.invalidateQueries({ queryKey: queryKeys.auth.me() }),
  ])
}

/** Người báo tin của chính mình. Tắt khi tài khoản chưa gắn hồ sơ (cửa trả 400). */
export function useMyContacts(enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.myEmployeeContacts(),
    queryFn: () => employeeApi.getMyContacts(),
    enabled,
  })
}

export function useUpdateMyContact(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: SelfContactPayload) => employeeApi.updateMyContact(payload),
    onSuccess: () => {
      toast.success('Đã cập nhật thông tin liên hệ')
      void invalidateSelfContactQueries(queryClient, employeeId)
    },
  })
}

export function useSaveMyContacts(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (items: Omit<EmployeeContact, 'id' | 'sort_order'>[]) =>
      employeeApi.setMyContacts(items),
    onSuccess: () => {
      toast.success('Đã cập nhật người báo tin')
      void invalidateSelfContactQueries(queryClient, employeeId)
    },
  })
}
