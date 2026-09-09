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
  //  ⚠️ Mọi `.max()` dưới đây phải khớp ĐÚNG `String(n)` ở
  //  `backend/app/modules/employee/model.py`. Khai RỘNG hơn cột thì người dùng
  //  gõ hết ô, không thấy lỗi nào, bấm Lưu mới ăn 422 từ backend — mà câu 422
  //  đó là tiếng Anh (`String should have at most…`). Khai HẸP hơn cột thì chặn
  //  nhầm, người dùng không dùng hết được ô. `employee-schema-stress.test.ts`
  //  canh từng cặp một.
  //
  //  Bỏ trống khi tạo mới thì backend tự sinh mã dạng NSU0001.
  code: z.string().trim().max(25, 'Mã tối đa 25 ký tự'),
  full_name: z.string().trim().min(1, 'Nhập họ tên').max(255, 'Họ tên tối đa 255 ký tự'),
  // Cũng là TÊN ĐĂNG NHẬP của tài khoản. Cho phép để trống (nhân sự chưa cấp tài khoản).
  email: z.string().trim().max(255, 'Email tối đa 255 ký tự'),
  phone: z.string().trim().max(25, 'Số điện thoại tối đa 25 ký tự'),
  // 0 = chưa gán phòng ban (backend dùng 0 làm sentinel thay cho NULL).
  department_id: z.number().int().min(0),
  //  CHỨC VỤ — duoc-CR-320: form gửi KHÓA (`position_id`), không gửi chữ nữa.
  //
  //  ⚠️ Cột chữ `position` vẫn tồn tại ở backend nhưng là **nhãn đã chép** từ
  //  danh mục, và **cố ý không có trong form**: gửi kèm một chuỗi thì backend
  //  ghi đè nó bằng tên trong danh mục (`position_service.sync_label`), nên ô
  //  chữ ở đây chỉ tạo ảo giác sửa được. `0` = chưa gán chức vụ.
  //
  //  CR-022 vẫn đúng: đây là CHỨC DANH in trên phiếu, KHÔNG cấp quyền gì.
  position_id: z.number().int().min(0),
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
  //  0 = chưa khai · 1 nam · 2 nữ · 3 khác. Dùng để LỌC loại nghỉ (thai sản chỉ
  //  áp cho nữ); chưa khai thì KHÔNG bị chặn loại nào, còn «Khác» thì CÓ — xem
  //  `employee/constants.GENDER_OTHER` ở backend.
  gender: z.number().int().min(0).max(3),

  //  PHÁP NHÂN. Hỏi ngay ở form TẠO NHANH (C2) — hồ sơ không gắn pháp nhân thì
  //  phạm vi dữ liệu của người đó rỗng ngay từ đầu.
  //
  //  Màn CHI TIẾT **sửa được** kể từ duoc-CR-342. Trước đó ô này chỉ xem vì đổi
  //  pháp nhân là đổi tập dữ liệu họ đọc được và phải kèm luật "phòng ban đang
  //  gán có thuộc pháp nhân mới không"; luật đó nay nằm ở
  //  `employee-tab-general.handleCompanyChange`. Đừng mở ô này ở một màn thứ ba
  //  mà không mang theo luật đó — thiếu nó thì hồ sơ lưu xuống ở trạng thái công
  //  ty A / phòng ban của công ty B.
  company_id: z.number().int().min(0),

  //  NGÀY SINH — thuộc nhóm NHẠY CẢM ở backend. Hỏi ngay từ form tạo nhanh vì
  //  đây là ô hành chính cần sớm nhất (hợp đồng, BHXH), và người nhập hồ sơ
  //  mới thì luôn có sẵn giấy tờ trong tay.
  date_of_birth: z.string().trim(),
})

export type EmployeeFormValues = z.infer<typeof employeeSchema>

export const EMPTY_EMPLOYEE_FORM: EmployeeFormValues = {
  code: '',
  full_name: '',
  email: '',
  phone: '',
  department_id: 0,
  position_id: 0,
  status: 'official',
  is_active: true,
  hire_date: '',
  gender: 0,
  company_id: 0,
  date_of_birth: '',
}

/**
 * HỒ SƠ ĐẦY ĐỦ — bản mở rộng dùng cho MÀN CHI TIẾT (duoc-CR-314 Đợt 2).
 *
 * Tách khỏi `employeeSchema` chứ không gộp một cái: hộp thoại TẠO NHANH cố ý
 * chỉ hỏi ~10 ô (bài học của HrOnline — bắt điền đủ 30+ ô ngay từ đầu thì không
 * ai nhập), còn màn chi tiết hỏi hết. Một schema cho cả hai thì hoặc hộp thoại
 * gửi thừa 20 ô rỗng và **ghi đè dữ liệu người khác vừa nhập**, hoặc phải nhớ
 * lọc tay ở một chỗ nào đó — thứ sẽ quên.
 *
 * ⚠️ **Không có `id_front_image` / `id_back_image`.** Hai ô ảnh CCCD chỉ đặt
 * được qua cửa upload riêng; backend cũng không khai chúng trong `EmployeeUpdate`.
 * Nhận đường dẫn từ client là cho phép trỏ ô ảnh vào một URL bên ngoài, rồi màn
 * hồ sơ và bản in sẽ tải nó về hộ.
 */
export const employeeProfileSchema = employeeSchema.extend({
  // Nhóm 1 — cá nhân
  place_of_birth: z.string().trim().max(255, 'Tối đa 255 ký tự'),
  ethnicity: z.string().trim().max(50, 'Tối đa 50 ký tự'),
  religion: z.string().trim().max(50, 'Tối đa 50 ký tự'),
  marital_status: z.number().int().min(0).max(3),
  children_count: z.number().int().min(0, 'Không âm').max(30, 'Tối đa 30'),
  personal_email: z.string().trim().max(255, 'Tối đa 255 ký tự'),
  tax_code: z.string().trim().max(20, 'Mã số thuế tối đa 20 ký tự'),
  education_level: z.number().int().min(0).max(5),
  major: z.string().trim().max(255, 'Tối đa 255 ký tự'),

  // Nhóm 2 — công việc
  manager_id: z.number().int().min(0),
  employment_type: z.number().int().min(0).max(6),
  job_level: z.number().int().min(0).max(6),
  work_location: z.string().trim().max(255, 'Tối đa 255 ký tự'),
  resign_date: z.string().trim(),

  // Nhóm 3 — liên hệ
  permanent_address: z.string().trim().max(500, 'Tối đa 500 ký tự'),
  current_address: z.string().trim().max(500, 'Tối đa 500 ký tự'),

  // Nhóm 4 — ngân hàng
  bank_account_no: z.string().trim().max(50, 'Tối đa 50 ký tự'),
  bank_account_name: z.string().trim().max(255, 'Tối đa 255 ký tự'),
  bank_name: z.string().trim().max(100, 'Tối đa 100 ký tự'),
  bank_branch: z.string().trim().max(255, 'Tối đa 255 ký tự'),

  // Nhóm 5 — giấy tờ, BHXH/BHYT
  id_number: z.string().trim().max(20, 'Số CCCD tối đa 20 ký tự'),
  id_issue_date: z.string().trim(),
  id_issue_place: z.string().trim().max(255, 'Tối đa 255 ký tự'),
  id_expiry_date: z.string().trim(),
  social_insurance_no: z.string().trim().max(20, 'Tối đa 20 ký tự'),
  health_care_place: z.string().trim().max(255, 'Tối đa 255 ký tự'),
  health_care_code: z.string().trim().max(20, 'Tối đa 20 ký tự'),
})

export type EmployeeProfileFormValues = z.infer<typeof employeeProfileSchema>

export const EMPTY_EMPLOYEE_PROFILE_FORM: EmployeeProfileFormValues = {
  ...EMPTY_EMPLOYEE_FORM,
  place_of_birth: '',
  ethnicity: '',
  religion: '',
  marital_status: 0,
  children_count: 0,
  personal_email: '',
  tax_code: '',
  education_level: 0,
  major: '',
  manager_id: 0,
  employment_type: 0,
  job_level: 0,
  work_location: '',
  resign_date: '',
  permanent_address: '',
  current_address: '',
  bank_account_no: '',
  bank_account_name: '',
  bank_name: '',
  bank_branch: '',
  id_number: '',
  id_issue_date: '',
  id_issue_place: '',
  id_expiry_date: '',
  social_insurance_no: '',
  health_care_place: '',
  health_care_code: '',
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
    date_of_birth: employee.date_of_birth ?? '',
    gender: employee.gender ?? 0,
    //  Cột mới (duoc-CR-320): hồ sơ cũ có thể chưa có khóa nào, và `undefined`
    //  vào ô chọn là React đổi ô từ "có điều khiển" sang "không điều khiển".
    position_id: employee.position_id ?? 0,
  }
}

/**
 * Hồ sơ từ API → giá trị form ĐẦY ĐỦ (màn chi tiết).
 *
 * ⚠️ Cùng bẫy `null` với `hire_date`: bốn cột ngày (`date_of_birth`,
 * `resign_date`, `id_issue_date`, `id_expiry_date`) là `DATE NULL` nên API trả
 * `null` cho hồ sơ chưa khai, mà `null` ĐÈ được lên mặc định `''` — ô ngày nhận
 * `null` là mở hồ sơ ra đã đỏ lỗi validate, chưa gõ gì.
 *
 * ⚠️ **Trường NHẠY CẢM về rỗng khi người xem không có `employee_sensitive.read`**
 * (backend che ở tầng serializer). Nghĩa là người đó bấm Lưu sẽ **ghi đè rỗng
 * lên dữ liệu thật**. Chốt chặn nằm ở màn hình: xem `pickWritableProfile`.
 */
export function employeeProfileFormValues(
  employee?: Employee | null,
): EmployeeProfileFormValues {
  if (!employee) return { ...EMPTY_EMPLOYEE_PROFILE_FORM }
  return {
    ...EMPTY_EMPLOYEE_PROFILE_FORM,
    ...employee,
    hire_date: employee.hire_date ?? '',
    date_of_birth: employee.date_of_birth ?? '',
    resign_date: employee.resign_date ?? '',
    id_issue_date: employee.id_issue_date ?? '',
    id_expiry_date: employee.id_expiry_date ?? '',
    gender: employee.gender ?? 0,
    position_id: employee.position_id ?? 0,
  }
}

/**
 * 15 trường mà backend CHE khi thiếu `employee_sensitive.read`.
 *
 * Danh sách này phải khớp `SENSITIVE_FIELDS` ở
 * `backend/app/modules/employee/sensitive.py`. Hai ô ảnh CCCD nằm trong nhóm
 * nhạy cảm ở backend nhưng KHÔNG có trong form (đặt qua cửa upload), nên không
 * liệt kê ở đây.
 */
export const SENSITIVE_PROFILE_FIELDS = [
  'date_of_birth',
  'tax_code',
  'permanent_address',
  'current_address',
  'bank_account_no',
  'bank_account_name',
  'bank_name',
  'bank_branch',
  'id_number',
  'id_issue_date',
  'id_issue_place',
  'id_expiry_date',
  'social_insurance_no',
] as const satisfies readonly (keyof EmployeeProfileFormValues)[]

/**
 * Bỏ các ô NHẠY CẢM khỏi payload khi người lưu không được xem chúng.
 *
 * ⚠️ Đây là chốt chống **mất dữ liệu**, không phải chốt bảo mật. Tình huống có
 * thật: hành chính có `employee.write` nhưng không có `employee_sensitive.read`
 * mở hồ sơ ra sửa số điện thoại. Backend đã che nên form nhận về số tài khoản
 * ngân hàng là chuỗi RỖNG; bấm Lưu là PATCH rỗng đè lên dữ liệu thật, và không
 * ai biết cho tới kỳ trả lương.
 *
 * Backend cố ý KHÔNG tự chặn: nó không phân biệt được "gửi rỗng vì bị che" với
 * "gửi rỗng vì người ta muốn xóa ô đó". Chỗ duy nhất biết là nơi dựng form.
 */
export function pickWritableProfile(
  values: EmployeeProfileFormValues,
  canReadSensitive: boolean,
): Partial<EmployeeProfileFormValues> {
  if (canReadSensitive) return values
  const out: Partial<EmployeeProfileFormValues> = { ...values }
  for (const field of SENSITIVE_PROFILE_FIELDS) delete out[field]
  return out
}
