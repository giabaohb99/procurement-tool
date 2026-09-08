import { z } from 'zod'

import type { Employee } from '../types/employee'

/**
 * Form hồ sơ nhân sự. Bám sát `EmployeeCreate` của backend để không dính 422.
 *
 * ⚠️ QUY ƯỚC CHO MỌI SCHEMA FORM (giống `supplier-schema.ts`): KHÔNG dùng
 * `.default()` và `.coerce` — chúng làm kiểu ĐẦU VÀO khác kiểu ĐẦU RA, còn
 * react-hook-form chỉ suy ra một kiểu. Giá trị khởi tạo đặt ở `defaultValues`.
 */
export const employeeSchema = z.object({
  // Bỏ trống khi tạo mới thì backend tự sinh mã dạng NSU0001.
  code: z.string().trim().max(50, 'Mã tối đa 50 ký tự'),
  full_name: z.string().trim().min(1, 'Nhập họ tên').max(255, 'Họ tên tối đa 255 ký tự'),
  // Cũng là TÊN ĐĂNG NHẬP của tài khoản. Cho phép để trống (nhân sự chưa cấp tài khoản).
  email: z.string().trim().max(150, 'Email tối đa 150 ký tự'),
  phone: z.string().trim().max(30, 'Số điện thoại tối đa 30 ký tự'),
  // 0 = chưa gán phòng ban (backend dùng 0 làm sentinel thay cho NULL).
  department_id: z.number().int().min(0),
  // CR-022: CHỨC DANH hiển thị trên phiếu, KHÔNG cấp quyền.
  position: z.string().trim().max(100, 'Chức vụ tối đa 100 ký tự'),
  // B-03: gửi lên là MÃ (`official`…). Vẫn để CHUỖI tự do chứ không ràng enum: dòng
  // chưa chạy migration mang giá trị lạ thì ràng enum là mở form lên đã lặng lẽ ghi đè
  // trạng thái thật. Mã lạ có backend chặn bằng 422, chặn hai lần không thêm gì.
  status: z.string().trim().min(1, 'Chọn tình trạng làm việc'),
  is_active: z.boolean(),

  //  NGÀY VÀO LÀM — mốc tính THÂM NIÊN, tức số ngày phép cộng thêm mỗi năm
  //  (`tab_leave_type_seniority`). Chuỗi `YYYY-MM-DD`, rỗng = chưa khai.
  //
  //  ⚠️ Để trống được, cố ý: hồ sơ cũ chưa ai nhập, và bắt buộc thì mở form
  //  lên sửa số điện thoại cũng không lưu nổi cho tới khi tra ra ngày vào làm.
  //  Backend coi rỗng là 0 năm và màn Quỹ phép trưng cảnh báo ra.
  hire_date: z.string().trim(),
  //  0 = chưa khai · 1 nam · 2 nữ. Dùng để LỌC loại nghỉ (thai sản chỉ áp cho
  //  nữ); chưa khai thì KHÔNG bị chặn loại nào.
  gender: z.number().int().min(0).max(2),
})

export type EmployeeFormValues = z.infer<typeof employeeSchema>

export const EMPTY_EMPLOYEE_FORM: EmployeeFormValues = {
  code: '',
  full_name: '',
  email: '',
  phone: '',
  department_id: 0,
  position: '',
  status: 'official',
  is_active: true,
  hire_date: '',
  gender: 0,
}

/**
 * Hồ sơ từ API → giá trị form.
 *
 * ⚠️ Không dùng thẳng `{ ...EMPTY_EMPLOYEE_FORM, ...employee }` như trước: cột
 * `hire_date` là `DATE NULL` nên API trả `null` cho hồ sơ chưa khai, mà `null`
 * ĐÈ được lên giá trị mặc định `''` — ô ngày nhận `null` là mở hồ sơ ra đã đỏ
 * lỗi validate, chưa gõ gì. Đi qua hàm này thì cả hai màn (hộp thoại tạo mới và
 * màn chi tiết) cùng một luật.
 */
export function employeeFormValues(employee?: Employee | null): EmployeeFormValues {
  if (!employee) return { ...EMPTY_EMPLOYEE_FORM }
  return {
    ...EMPTY_EMPLOYEE_FORM,
    ...employee,
    hire_date: employee.hire_date ?? '',
    gender: employee.gender ?? 0,
  }
}
