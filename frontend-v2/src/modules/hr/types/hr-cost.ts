/**
 * Danh mục CHI PHÍ NHÂN SỰ do người dùng tự định nghĩa (duoc-CR-690, tài liệu 06 §4): nhóm chi phí,
 * mẫu khoản chi phí, và MỘT khoản (cùng hình dạng cho khoản của mẫu lẫn khoản đã chép vào kế hoạch).
 *
 * Khai `type` (không `interface`) cho hai bản ghi đi qua khung CRUD chung — thỏa ràng buộc `CrudRecord`.
 */

/** Nhóm chi phí — `tab_hr_cost_group`. */
export type HrCostGroup = {
  id: number
  name: string
  sort_order: number
  is_active: boolean
  updated_at?: string | null
}

/**
 * MỘT khoản chi phí. `code` là khóa tham chiếu: khoản % trỏ khoản gốc bằng `base_codes`, dòng vị trí
 * giữ số tiền của khoản «nhập theo vị trí» trong `amounts[code]`. Đổi `code` thì phải đổi theo cả hai
 * chỗ đó (`renameCostItemCode`).
 *
 * Hai ô TIỀN (`cap_amount`, `amount`) là `null` khi người xem không được xem lương của pháp nhân.
 */
export interface HrCostItem {
  id?: number
  code: string
  name: string
  group_id: number
  calc_method: number
  /** % cho cách tính PERCENT_OF (17.5 = 17,5%). */
  rate: number | null
  /** Hệ số cho MONTHS_OF (1 = một tháng lương). */
  factor: number | null
  /** Trần / người cho PERCENT_OF; `0` = không trần. */
  cap_amount: number | null
  /** Số tiền cho PER_HEAD_ONCE / LUMP_SUM. */
  amount: number | null
  base_codes: string[]
  applies_to: number
  position_ids: number[]
  /** Tháng rơi vào 1..12; rỗng = mỗi tháng của kỳ. */
  months: number[]
  actual_source: number
  sort_order: number
}

/** Mẫu khoản chi phí — `tab_hr_cost_template`. Danh sách có thể chỉ trả `item_count`. */
export type HrCostTemplate = {
  id: number
  name: string
  note: string
  is_active: boolean
  item_count?: number
  items?: HrCostItem[]
  updated_at?: string | null
}

/** Thân gửi lên khi tạo / sửa mẫu — `items` THAY NGUYÊN danh sách. */
export interface HrCostTemplatePayload {
  name: string
  note: string
  is_active: boolean
  items: HrCostItem[]
}
