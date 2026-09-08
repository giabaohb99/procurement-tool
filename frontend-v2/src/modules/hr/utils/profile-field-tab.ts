/**
 * Trường nào của hồ sơ nhân sự nằm ở TAB nào.
 *
 * ⚠️ Sinh ra để vá một lỗi đến từ chính thiết kế 5 tab (duoc-CR-316):
 *
 *   Người dùng nhập sai một ô ở tab «Giấy tờ & BHXH», chuyển sang tab «Chung»,
 *   bấm **Lưu** → **không có gì xảy ra**. Không toast, không lỗi trên màn,
 *   không một lời gọi API nào. Nút Lưu đọc ra như bị hỏng.
 *
 * Vì sao: react-hook-form chặn submit khi còn lỗi, và câu lỗi được vẽ ở
 * `FormMessage` NGAY DƯỚI Ô ĐÓ — mà Radix `Tabs` **hủy mount** nội dung tab
 * đang ẩn. Câu lỗi tồn tại trong `formState`, nhưng không có chỗ nào trên màn
 * hình để hiện ra.
 *
 * Đây là kiểu lỗi tệ nhất của một biểu mẫu: người dùng bấm nút và **không nhận
 * được tín hiệu nào** — họ không biết là mình sai, cũng không biết sai ở đâu.
 * Bảng dưới đây cho phép nhảy thẳng tới tab chứa ô sai.
 */

export type ProfileTabKey = 'general' | 'contact' | 'documents' | 'leave' | 'account'

/**
 * ⚠️ Thêm ô mới vào một tab thì phải thêm tên nó vào đây.
 *
 * Thiếu tên thì `tabOfField` trả `general` — người dùng bị đá về tab Chung mà
 * không thấy ô nào đỏ, tức quay lại đúng cái lỗi đang vá. Có test đối chiếu
 * bảng này với schema, nên bỏ sót là đỏ chứ không im lặng.
 */
const FIELD_TAB: Record<string, ProfileTabKey> = {
  // Tab «Chung» — nhóm 1 (cá nhân) + nhóm 2 (công việc)
  code: 'general',
  full_name: 'general',
  gender: 'general',
  date_of_birth: 'general',
  place_of_birth: 'general',
  ethnicity: 'general',
  religion: 'general',
  marital_status: 'general',
  children_count: 'general',
  personal_email: 'general',
  tax_code: 'general',
  education_level: 'general',
  major: 'general',
  company_id: 'general',
  department_id: 'general',
  position_id: 'general',
  manager_id: 'general',
  employment_type: 'general',
  job_level: 'general',
  work_location: 'general',
  status: 'general',
  is_active: 'general',
  hire_date: 'general',
  resign_date: 'general',

  // Tab «Liên hệ & Ngân hàng» — nhóm 3 + nhóm 4
  email: 'contact',
  phone: 'contact',
  permanent_address: 'contact',
  current_address: 'contact',
  bank_account_no: 'contact',
  bank_account_name: 'contact',
  bank_name: 'contact',
  bank_branch: 'contact',

  // Tab «Giấy tờ & BHXH» — nhóm 5
  id_number: 'documents',
  id_issue_date: 'documents',
  id_issue_place: 'documents',
  id_expiry_date: 'documents',
  social_insurance_no: 'documents',
  health_care_place: 'documents',
  health_care_code: 'documents',
}

/** Danh sách tên trường đã khai — dùng cho test đối chiếu với schema. */
export const MAPPED_PROFILE_FIELDS = Object.keys(FIELD_TAB)

/** Tab chứa một ô. Ô lạ → `general` (nơi có nút quay lại rõ nhất). */
export function tabOfField(field: string): ProfileTabKey {
  return FIELD_TAB[field] ?? 'general'
}

/**
 * Tab chứa ô SAI ĐẦU TIÊN, cùng tên ô đó — để câu thông báo nói được sai ở đâu.
 *
 * `errors` là `formState.errors` của react-hook-form. Không có lỗi nào (hoặc
 * toàn lỗi của ô không khai trong bảng) thì trả `null`, và nơi gọi giữ nguyên
 * tab đang xem.
 */
export function firstInvalidTab(
  errors: Record<string, unknown>,
): { tab: ProfileTabKey; field: string } | null {
  const field = Object.keys(errors ?? {})[0]
  if (!field) return null
  return { tab: tabOfField(field), field }
}
