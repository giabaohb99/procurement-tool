import { apiDelete, apiGet, apiPatch, apiPost, httpClient } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { Employee, EmployeeDetail } from '../types/employee'
import type { EmployeeFormValues } from '../schemas/employee-schema'

const BASE_URL = '/api/employees'

/** Tầng API của phân hệ Nhân sự — chỉ gọi HTTP, không chứa logic React. */
export const employeeApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<Employee>>(BASE_URL, { params }),

  getById: (id: number) => apiGet<EmployeeDetail>(`${BASE_URL}/${id}`),

  create: (payload: EmployeeFormValues) => apiPost<Employee>(BASE_URL, payload),

  update: (id: number, payload: Partial<EmployeeFormValues>) =>
    apiPatch<Employee>(`${BASE_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),

  /**
   * KIÊM NHIỆM — những phòng người này phụ trách THÊM, ngoài phòng chính.
   *
   * Cửa RIÊNG chứ không nhét vào `update`: đổi phòng ban là đổi PHẠM VI DỮ LIỆU
   * của người đó, nên backend gác nó bằng ba chốt chống vượt quyền mà cột
   * `department_id` thường không có (xem `employee/department_service.py`).
   */
  getDepartments: (id: number) =>
    apiGet<{ primary_department_id: number; extra_department_ids: number[] }>(
      `${BASE_URL}/${id}/departments`,
    ),

  /** Chỉ đặt phòng KIÊM NHIỆM. Phòng chính đổi ở ô «Phòng ban» của hồ sơ. */
  setDepartments: (id: number, extraDepartmentIds: number[]) =>
    httpClient.put(`${BASE_URL}/${id}/departments`, {
      extra_department_ids: extraDepartmentIds,
    }),

  /**
   * Ảnh lưu vào TÀI KHOẢN đăng nhập của nhân sự (`tab_user.avatar`), cùng chỗ
   * với ảnh người dùng tự đổi ở trang cá nhân. Nhân sự chưa có tài khoản thì
   * backend trả 400 — xem `employee/controller.py`.
   */
  uploadAvatar: (id: number, file: File) => {
    const body = new FormData()
    body.append('file', file)
    return apiPost<{ avatar: string }>(`${BASE_URL}/${id}/avatar`, body)
  },

  /** Ảnh chữ ký, cùng cơ chế avatar (lưu ở `tab_user.signature`). Nhân sự chưa
   *  có tài khoản thì backend trả 400. */
  uploadSignature: (id: number, file: File) => {
    const body = new FormData()
    body.append('file', file)
    return apiPost<{ signature: string }>(`${BASE_URL}/${id}/signature`, body)
  },

  /** Gỡ chữ ký (chỉ xóa liên kết, file storage giữ nguyên). */
  removeSignature: (id: number) => apiDelete<{ signature: string }>(`${BASE_URL}/${id}/signature`),

  /**
   * Đặt mật khẩu. Nhân sự CHƯA có tài khoản thì backend tự tạo tài khoản mới
   * (email của nhân sự + vai trò mặc định "Nhân sự") rồi đặt luôn mật khẩu này.
   * Câu thông báo phân biệt hai trường hợp nằm ở `message` nên gọi thẳng
   * `httpClient` thay vì `apiPost` (hàm đó bóc mất phong bì).
   */
  setPassword: async (id: number, password: string) => {
    const res = await httpClient.post<{ success: true; message?: string }>(
      `${BASE_URL}/${id}/set-password`,
      { password },
    )
    return res.data.message ?? ''
  },
}
