import { departmentApi } from '@/modules/hr/api/department-api'
import { employeeApi } from '@/modules/hr/api/employee-api'
import type { SelectOption } from '@/shared/conditional-filter'

/**
 * Nguồn options cho các ô lọc THAM CHIẾU (phòng ban / nhân sự) — CR-088.
 *
 * Bộ lọc gửi đi ID chứ không gửi tên nữa. Ba tật của lọc theo tên, cả ba đều đã
 * gặp thật trên dữ liệu đang chạy:
 *
 *   đổi tên phòng          -> bộ lọc cũ trượt sạch, danh sách rỗng mà không báo gì
 *   hai người trùng tên    -> lọc một người ra đơn của cả hai
 *   `contains` khớp chuỗi con -> lọc "Hân" ra luôn "Nguyễn Thị Ngọc Hân"
 *
 * Lọc do SERVER làm (mỗi lần gõ là một lần gọi API) nên danh mục vài nghìn dòng
 * vẫn dùng được. Lấy 50 dòng đầu — combobox chỉ để CHỌN, không phải để duyệt hết.
 */

const PAGE_SIZE = 50

/** Danh mục phòng ban. Endpoint này tìm bằng `q` (tên phòng hoặc tên trưởng bộ phận). */
export async function fetchDepartmentOptions(search: string): Promise<SelectOption[]> {
  const res = await departmentApi.list({ q: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({ value: String(item.id), label: item.name }))
}

/**
 * Danh mục nhân sự. Kèm MÃ vào nhãn vì đây chính là màn có người trùng tên —
 * không có mã thì hai dòng giống hệt nhau, chọn xong không biết đã chọn ai.
 */
export async function fetchEmployeeOptions(search: string): Promise<SelectOption[]> {
  const res = await employeeApi.list({ full_name: search, is_active: true, page_size: PAGE_SIZE })
  return res.items.map((item) => ({
    value: String(item.id),
    label: item.code ? `${item.full_name} (${item.code})` : item.full_name,
  }))
}
