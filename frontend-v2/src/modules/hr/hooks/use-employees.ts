import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { employeeApi } from '../api/employee-api'
import type { EmployeeFormValues } from '../schemas/employee-schema'

/**
 * Danh sách nhân viên có phân trang + lọc.
 * Whitelist lọc của backend: `code`, `full_name`, `email`, `position`,
 * `department_id`, `status`, `is_active` — gửi key ngoài danh sách này là vô ích.
 */
export function useEmployees(params: ListParams = {}, options: { enabled?: boolean } = {}) {
  const query: ListParams = {
    page: 1,
    page_size: appConfig.defaultPageSize,
    ...params,
  }

  return useQuery({
    queryKey: queryKeys.hr.employees(query),
    queryFn: () => employeeApi.list(query),
    placeholderData: keepPreviousData,
    //  `enabled` cho phân hệ khác MƯỢN danh bạ này tắt lời gọi khi người dùng
    //  không có `employee.read` — cứ mount là gọi thì họ ăn toast 403 ngay lúc
    //  mở màn (bẫy đã dính ở tab «Công nợ» của Nhà cung cấp).
    enabled: options.enabled ?? true,
  })
}

/** Một hồ sơ nhân sự (bản chi tiết, có thêm `user_id`). */
export function useEmployee(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.employee(id),
    queryFn: () => employeeApi.getById(id),
    enabled: id > 0,
  })
}

/**
 * Tạo mới HOẶC cập nhật — gộp một hook vì hai màn dùng chung một form.
 * Lỗi đã được http-client toast sẵn (không phải GET) nên ở đây chỉ lo báo
 * thành công và làm mới cache.
 */
/** Phòng chính + phòng kiêm nhiệm của một nhân sự, tách bạch hai khóa. */
export function useEmployeeDepartments(employeeId: number) {
  return useQuery({
    queryKey: queryKeys.hr.employeeDepartments(employeeId),
    queryFn: () => employeeApi.getDepartments(employeeId),
    enabled: employeeId > 0,
  })
}

export function useSaveEmployeeDepartments(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (extraDepartmentIds: number[]) =>
      employeeApi.setDepartments(employeeId, extraDepartmentIds),
    onSuccess: () => {
      toast.success('Đã cập nhật kiêm nhiệm')
      //  Đổi kiêm nhiệm là đổi phạm vi dữ liệu, nạp lại cả nhánh nhân sự.
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

export function useSaveEmployee() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: EmployeeFormValues }) =>
      id ? employeeApi.update(id, values) : employeeApi.create(values),

    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật nhân sự' : 'Đã thêm nhân sự')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

export function useDeleteEmployee() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => employeeApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa nhân sự')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

/** Đổi ảnh đại diện. Ảnh nằm trên tài khoản đăng nhập nên phải nạp lại hồ sơ. */
export function useUploadEmployeeAvatar(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => employeeApi.uploadAvatar(employeeId, file),
    onSuccess: () => {
      toast.success('Đã cập nhật ảnh đại diện')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

/** Đặt/gỡ chữ ký của nhân sự (HR làm hộ). Cùng cơ chế avatar (lưu ở tài khoản). */
export function useUploadEmployeeSignature(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => employeeApi.uploadSignature(employeeId, file),
    onSuccess: () => {
      toast.success('Đã cập nhật chữ ký')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

export function useRemoveEmployeeSignature(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => employeeApi.removeSignature(employeeId),
    onSuccess: () => {
      toast.success('Đã gỡ chữ ký')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}
