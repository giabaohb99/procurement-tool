import { apiDelete, apiGet, apiPatch, apiPost, httpClient } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type {
  Employee,
  EmployeeContact,
  EmployeeDetail,
  EmployeeFamily,
} from '../types/employee'
import type {
  EmployeeFormValues,
  EmployeeProfileFormValues,
} from '../schemas/employee-schema'

const BASE_URL = '/api/employees'

/**
 * Ô NGÀY rỗng phải gửi lên `null`, không gửi chuỗi rỗng.
 *
 * Năm cột ngày đều là `DATE NULL`; `""` không phải ngày hợp lệ nên Pydantic trả
 * 422 và người dùng ăn lỗi khi mở một hồ sơ cũ ra sửa đúng cái tên. Đặt ở tầng
 * API để CẢ hộp thoại tạo mới lẫn màn chi tiết dùng chung một luật.
 *
 * ⚠️ Chỉ đụng tới khóa CÓ MẶT trong payload. `PATCH` phân biệt "không gửi
 * trường" với "gửi null để xóa" — thêm khóa vào là biến một lần lưu 10 ô thành
 * lệnh xóa 4 ô ngày mà người dùng không đụng tới.
 */
const DATE_FIELDS = [
  'hire_date',
  'date_of_birth',
  'resign_date',
  'id_issue_date',
  'id_expiry_date',
] as const

function toEmployeePayload(values: Record<string, unknown>) {
  const out = { ...values }
  for (const field of DATE_FIELDS) {
    if (field in out) out[field] = out[field] ? out[field] : null
  }
  return out
}

/** Tầng API của phân hệ Nhân sự — chỉ gọi HTTP, không chứa logic React. */
export const employeeApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<Employee>>(BASE_URL, { params }),

  getById: (id: number) => apiGet<EmployeeDetail>(`${BASE_URL}/${id}`),

  create: (payload: EmployeeFormValues) =>
    apiPost<Employee>(BASE_URL, toEmployeePayload(payload)),

  update: (
    id: number,
    payload: Partial<EmployeeFormValues> | Partial<EmployeeProfileFormValues>,
  ) => apiPatch<Employee>(`${BASE_URL}/${id}`, toEmployeePayload(payload)),

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

  // ── Hai bảng con (duoc-CR-314) ────────────────────────────────────────────
  //  ⚠️ Cả bốn cửa dưới đây trả **403** khi người gọi không có
  //  `employee_sensitive.read` — toàn bộ hai bảng thuộc nhóm nhạy cảm. Nơi gọi
  //  PHẢI tắt query bằng `enabled` chứ đừng để nó cứ mount là bắn: người dùng
  //  ăn toast 403 ngay lúc mở tab, đúng cái bẫy đã dính ở tab «Công nợ» của
  //  Nhà cung cấp (CR-106).

  /** Người báo tin trong trường hợp cần thiết. */
  getContacts: (id: number) => apiGet<EmployeeContact[]>(`${BASE_URL}/${id}/contacts`),

  /** ĐẶT LẠI cả bảng một lượt. Dòng để trống họ tên bị backend bỏ qua. */
  setContacts: (id: number, items: Omit<EmployeeContact, 'id' | 'sort_order'>[]) =>
    httpClient
      .put<{ data: EmployeeContact[] }>(`${BASE_URL}/${id}/contacts`, { items })
      .then((res) => res.data.data),

  /** Thành viên hộ gia đình (kê khai BHXH). */
  getFamilies: (id: number) => apiGet<EmployeeFamily[]>(`${BASE_URL}/${id}/families`),

  setFamilies: (id: number, items: Omit<EmployeeFamily, 'id' | 'sort_order'>[]) =>
    httpClient
      .put<{ data: EmployeeFamily[] }>(`${BASE_URL}/${id}/families`, { items })
      .then((res) => res.data.data),

  /**
   * Ảnh CCCD mặt trước / mặt sau.
   *
   * Cửa RIÊNG chứ không phải một ô trong form: nhận đường dẫn từ client là cho
   * phép trỏ ô ảnh giấy tờ tùy thân vào một URL bên ngoài, rồi màn hồ sơ và bản
   * in sẽ tải nó về hộ. Backend cũng không khai hai ô này trong `EmployeeUpdate`.
   */
  uploadIdImage: (id: number, side: 'front' | 'back', file: File) => {
    const body = new FormData()
    body.append('file', file)
    return apiPost<Record<string, string>>(`${BASE_URL}/${id}/id-image/${side}`, body)
  },

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
