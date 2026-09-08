/**
 * Bốn bộ mã SỐ của hồ sơ nhân sự — bản TypeScript của
 * `backend/app/modules/employee/constants.py`.
 *
 * ⚠️ **Gõ tay, và bắt buộc phải gõ tay.** `backend/scripts/gen_status_ts.py`
 * chỉ sinh cho bộ mã CHUỖI (`status_catalog.py`); bộ mã SỐ theo R2/QĐ-11 không
 * đi qua đó — `hr/types/leave.ts` cũng cùng cảnh. Đổi một con số ở backend thì
 * phải sửa ở đây, không có gì canh hộ.
 *
 * ⚠️ `0` ở CẢ BỐN bộ nghĩa là **chưa khai**, không phải một giá trị nghiệp vụ.
 * Nhãn của nó để RỖNG chứ không phải "Chưa khai": ô chọn hiện mục rỗng thì
 * người dùng đọc ra "chưa chọn", còn chữ "Chưa khai" đọc như một lựa chọn đã
 * chọn xong. Nơi nào cần chữ thì tự đặt `placeholder`.
 */

export interface CodeOption {
  value: number
  label: string
}

/** Bỏ mục `0` đi — dùng cho ô chọn có `placeholder` riêng. */
function withoutUnknown(options: readonly CodeOption[]): CodeOption[] {
  return options.filter((o) => o.value !== 0)
}

/** Nhãn của một mã. Mã lạ (dữ liệu cũ) → chuỗi rỗng, cùng luật với backend. */
export function codeLabel(options: readonly CodeOption[], value?: number | null): string {
  return options.find((o) => o.value === (value ?? 0))?.label ?? ''
}

// ── Tình trạng hôn nhân ─────────────────────────────────────────────────────
export const MARITAL_STATUS_OPTIONS: readonly CodeOption[] = [
  { value: 0, label: '' },
  { value: 1, label: 'Độc thân' },
  { value: 2, label: 'Có gia đình' },
  { value: 3, label: 'Ly hôn' },
]

// ── Trình độ học vấn ────────────────────────────────────────────────────────
export const EDUCATION_LEVEL_OPTIONS: readonly CodeOption[] = [
  { value: 0, label: '' },
  { value: 1, label: 'Phổ thông' },
  { value: 2, label: 'Trung cấp' },
  { value: 3, label: 'Cao đẳng' },
  { value: 4, label: 'Đại học' },
  { value: 5, label: 'Sau đại học' },
]

// ── Hình thức làm việc ──────────────────────────────────────────────────────
export const EMPLOYMENT_TYPE_OPTIONS: readonly CodeOption[] = [
  { value: 0, label: '' },
  { value: 1, label: 'Toàn thời gian' },
  { value: 2, label: 'Bán thời gian' },
  { value: 3, label: 'Thời vụ' },
  { value: 4, label: 'Cộng tác viên' },
  { value: 5, label: 'Thử việc' },
  { value: 6, label: 'Thực tập' },
]

// ── Cấp bậc ─────────────────────────────────────────────────────────────────
//  ⚠️ ĐỪNG dùng cấp bậc để suy ra người duyệt. Đây là thông tin nhân sự (lọc
//  danh sách, báo cáo cơ cấu); người duyệt suy từ `manager_id` và từ trưởng bộ
//  phận trong bảng phòng ban.
export const JOB_LEVEL_OPTIONS: readonly CodeOption[] = [
  { value: 0, label: '' },
  { value: 1, label: 'Nhân viên' },
  { value: 2, label: 'Tổ trưởng' },
  { value: 3, label: 'Phó phòng' },
  { value: 4, label: 'Trưởng phòng' },
  { value: 5, label: 'Giám đốc khối' },
  { value: 6, label: 'Ban tổng giám đốc' },
]

// ── Quan hệ nhân thân ───────────────────────────────────────────────────────
//  Dùng CHUNG cho cả hai bảng con, và **không lọc theo giới tính** (khách chốt
//  08/09/2026). Bảng hộ gia đình ghi quan hệ với CHỦ HỘ, bảng người báo tin ghi
//  quan hệ với NHÂN VIÊN — cùng một bộ từ, khác gốc quy chiếu.
//
//  ⚠️ `99` = «Khác» là CỐ Ý nhảy số: chừa chỗ cho quan hệ thêm về sau được đánh
//  liền mạch, và «Khác» thì luôn đứng cuối. Khớp `constants.RELATION_LABELS`.
export const RELATION_OPTIONS: readonly CodeOption[] = [
  { value: 0, label: '' },
  { value: 1, label: 'Chủ hộ' },
  { value: 2, label: 'Cha' },
  { value: 3, label: 'Mẹ' },
  { value: 4, label: 'Vợ' },
  { value: 5, label: 'Chồng' },
  { value: 6, label: 'Con trai' },
  { value: 7, label: 'Con gái' },
  { value: 8, label: 'Anh trai' },
  { value: 9, label: 'Chị gái' },
  { value: 10, label: 'Em trai' },
  { value: 11, label: 'Em gái' },
  { value: 12, label: 'Ông' },
  { value: 13, label: 'Bà' },
  { value: 99, label: 'Khác' },
]

/**
 * Tình trạng hôn nhân «Có gia đình» — ô «Số con» CHỈ hiện khi bằng mã này
 * (khách chốt 08/09/2026).
 *
 * ⚠️ Luật cũ là "ẩn khi Độc thân", tức *Ly hôn* và *Chưa khai* vẫn thấy ô đó.
 * Khách đổi sang chiều ngược lại: hỏi số con chỉ khi đã khai có gia đình. Hệ
 * quả phải biết — người **ly hôn** không nhập được số con qua màn này nữa; dữ
 * liệu cũ vẫn nguyên trong DB và vẫn được gửi lên khi lưu (ô ẩn chỉ là chuyện
 * hiển thị, xem chỗ dùng), chỉ là không sửa được cho tới khi đổi ô hôn nhân.
 */
export const MARITAL_MARRIED = 2

/** Bộ dùng cho Ô LỌC — bỏ mục rỗng, vì "lọc theo chưa khai" không có nghĩa. */
export const EMPLOYMENT_TYPE_FILTER_OPTIONS = withoutUnknown(EMPLOYMENT_TYPE_OPTIONS)
export const JOB_LEVEL_FILTER_OPTIONS = withoutUnknown(JOB_LEVEL_OPTIONS)

/** Trần số khóa của ô JSON tùy biến — khớp `constants.MAX_EXTRA_FIELDS`. */
export const MAX_EXTRA_FIELDS = 20

/**
 * Trần số dòng của MỘT bảng con (người báo tin / hộ gia đình).
 *
 * ⚠️ Phải khớp `MAX_PEOPLE_ROWS` ở `backend/app/modules/employee/field_limits.py`.
 * Khai rộng hơn thì người dùng gõ đủ số dòng, bấm Lưu mới ăn 422 **tiếng Anh**
 * (`List should have at most 30 items…`) và mất trắng công gõ — đã dựng lại
 * được trên trình duyệt thật 08/09/2026.
 */
export const MAX_PEOPLE_ROWS = 30
