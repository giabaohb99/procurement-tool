import { z } from 'zod'

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
}
