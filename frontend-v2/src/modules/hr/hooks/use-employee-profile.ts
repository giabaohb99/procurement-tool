import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { useAuth } from '@/core/auth/use-auth'
import { usePermission } from '@/core/authorization/use-permission'
import { queryKeys } from '@/shared/constants/query-keys'
import { employeeApi } from '../api/employee-api'
import type { EmployeeContact, EmployeeFamily } from '../types/employee'

/**
 * Hook của HỒ SƠ MỞ RỘNG — hai bảng con và ảnh CCCD (duoc-CR-314 Đợt 2).
 *
 * Tách khỏi `use-employees.ts` (đã 132 dòng) vì đây là một cụm việc riêng, và
 * cả cụm chung một điều kiện bật/tắt: **quyền `employee_sensitive.read`**.
 */

/**
 * Người xem có được đọc nhóm nhạy cảm của hồ sơ này không.
 *
 * Hai đường, giống hệt `backend/.../sensitive.py::can_read_sensitive`:
 * có khóa quyền, HOẶC đang xem hồ sơ của chính mình.
 *
 * ⚠️ Đây CHỈ để ẩn tab / tắt query cho đỡ vướng mắt và tránh toast 403. Chốt
 * thật nằm ở backend — nó che ở tầng serializer nên dù giao diện có vẽ ô ra thì
 * giá trị vẫn rỗng.
 */
export function useCanReadSensitive(employeeId: number): boolean {
  const { can } = usePermission()
  const { user } = useAuth()
  if (can('employee_sensitive', 'read')) return true
  //  Chặn `employee_id = 0`: tài khoản chưa gắn nhân sự (admin, tài khoản hệ
  //  thống) mang `0`, và so bằng mà không chặn thì «chưa gắn ai» khớp mọi hồ sơ.
  const me = user?.employee_id ?? 0
  return me > 0 && me === employeeId
}

export function useEmployeeContacts(employeeId: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.employeeContacts(employeeId),
    queryFn: () => employeeApi.getContacts(employeeId),
    //  ⚠️ `enabled` KHÔNG phải tối ưu. Cửa này trả 403 khi thiếu quyền, và
    //  http-client tự toast lỗi non-GET… nhưng GET 403 vẫn làm tab hiện trạng
    //  thái lỗi. Tắt hẳn thì tab chỉ nói "bạn không có quyền xem" một lần.
    enabled: employeeId > 0 && enabled,
  })
}

export function useSaveEmployeeContacts(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (items: Omit<EmployeeContact, 'id' | 'sort_order'>[]) =>
      employeeApi.setContacts(employeeId, items),
    onSuccess: () => {
      toast.success('Đã cập nhật người báo tin')
      void queryClient.invalidateQueries({
        queryKey: queryKeys.hr.employeeContacts(employeeId),
      })
    },
  })
}

export function useEmployeeFamilies(employeeId: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.hr.employeeFamilies(employeeId),
    queryFn: () => employeeApi.getFamilies(employeeId),
    enabled: employeeId > 0 && enabled,
  })
}

export function useSaveEmployeeFamilies(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (items: Omit<EmployeeFamily, 'id' | 'sort_order'>[]) =>
      employeeApi.setFamilies(employeeId, items),
    onSuccess: () => {
      toast.success('Đã cập nhật thành viên hộ gia đình')
      void queryClient.invalidateQueries({
        queryKey: queryKeys.hr.employeeFamilies(employeeId),
      })
    },
  })
}

/** Tải ảnh CCCD một mặt. Đường dẫn nằm trên chính hồ sơ nên phải nạp lại nó. */
export function useUploadIdImage(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ side, file }: { side: 'front' | 'back'; file: File }) =>
      employeeApi.uploadIdImage(employeeId, side, file),
    onSuccess: () => {
      toast.success('Đã cập nhật ảnh CCCD')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.employee(employeeId) })
    },
  })
}
