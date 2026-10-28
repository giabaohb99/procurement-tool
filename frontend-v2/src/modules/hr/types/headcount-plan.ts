import type { HrCostItem } from './hr-cost'

/**
 * KẾ HOẠCH NHÂN SỰ THEO KỲ (duoc-CR-690, thay bản một-dòng của CR-689) — khớp hợp đồng API ở
 * `plans/261027-1045-kho-mau-bao-cao-nhan-su/phase-22-ke-hoach-theo-ky-backend.md`.
 *
 * Mọi ô TIỀN là `null` khi người xem không được xem lương của pháp nhân đó (`can_see_payroll` ở
 * backend) — định biên thì luôn có. Trường đánh dấu `?:` là trường hợp đồng chưa chốt hẳn: giao diện
 * có nhánh dự phòng khi máy chủ chưa trả.
 */

/** Một dòng của danh sách — khung CRUD chung đòi `type` để thỏa `CrudRecord`. */
export type HeadcountPlanListItem = {
  id: number
  year: number
  period_type: number
  period_no: number
  company_id: number
  company_name: string
  /** `0` = kế hoạch của CẢ pháp nhân. */
  department_id: number
  department_name: string
  /** Định biên kỳ con cuối (tổng mọi dòng vị trí). */
  headcount_end: number | null
  /** Tổng chi phí cả kỳ; `null` = bị che (không phải «chưa lập»). */
  total_cost: number | null
  basis_no: string
  basis_date: string | null
  note: string
  /** «2026» · «H2-2026» · «Q3-2026» · «07/2026» — backend dựng sẵn; vắng thì giao diện tự dựng. */
  period_label?: string
  updated_at?: string | null
}

/** Một dòng vị trí. `position_id = 0` = dòng «Không theo vị trí» (chỉ nhập tổng phòng). */
export interface HeadcountPlanLine {
  id?: number
  position_id: number
  position_name?: string
  /** Định biên từng kỳ con — độ dài = số kỳ con của loại kỳ. */
  headcounts: number[]
  /**
   * Số tiền / người / tháng của từng khoản «nhập theo vị trí», khóa theo `code` của khoản. Cả object là
   * `null` khi người xem không được xem tiền — gửi lại `null` là backend giữ nguyên số đang lưu.
   */
  amounts: Record<string, number> | null
  note: string
}

/**
 * Văn bản liên kết. Người xem không đọc được văn bản thì backend CHỈ trả `{document_id, can_read:false}`
 * — không số, không trích yếu. Văn bản đã xóa: `{document_id, deleted:true}`.
 */
export interface HeadcountPlanDocumentLink {
  document_id: number
  code?: string
  title?: string
  status?: number
  /** Chỉ có ở văn bản vừa chọn trên form (lấy từ danh sách văn bản); bản đã lưu tra nhãn theo `status`. */
  status_label?: string
  can_read?: boolean
  deleted?: boolean
}

export interface HeadcountPlanPeriod {
  key: string
  label: string
  months: number[]
}

/** Một dòng của bảng tự tính — khoản (`code`) hoặc nhóm (`group_id`). */
export interface HeadcountPlanComputedRow {
  code?: string
  group_id?: number
  name: string
  values: (number | null)[]
  total: number | null
}

/** Kết quả bộ tính (`costing.compute_plan`) — cả `GET /{id}` lẫn `POST /compute` trả hình này. */
export interface HeadcountPlanComputed {
  periods: HeadcountPlanPeriod[]
  /** Định biên cuối mỗi kỳ con. */
  headcount: number[]
  items: HeadcountPlanComputedRow[]
  groups: HeadcountPlanComputedRow[]
  /** `null` khi bị che tiền (cùng lúc `items` / `groups` rỗng và `money_hidden: true`). */
  total: { values: (number | null)[]; total: number | null } | null
  avg_per_head: number | null
  money_hidden?: boolean
  /** Chỉ có ở chi tiết kế hoạch ĐÃ LƯU (`GET /{id}`), không có ở bản xem trước `/compute`. */
  actual?: HeadcountPlanActual
}

/**
 * THỰC TẾ so với kế hoạch (phase 24, tài liệu 06 §6) — mỗi mảng dài bằng số kỳ con; `null` = kỳ con
 * tương lai. Che tiền: `values` / `planned_comparable` / `remaining` là `null`, `headcount` vẫn có.
 * «Phần so được» = chỉ các khoản có nguồn thực tế (`covered_codes`); khoản không có nguồn nằm ở
 * `missing_codes` để ghi «thực tế chưa gồm…», không so táo với cam.
 */
export interface HeadcountPlanActual {
  values: (number | null)[] | null
  planned_comparable: (number | null)[] | null
  remaining: (number | null)[] | null
  headcount: (number | null)[]
  covered_codes: string[]
  missing_codes: string[]
  /** Số tháng ĐÃ QUA được tính của từng kỳ con; nhỏ hơn số tháng của kỳ con = kỳ đang chạy. */
  months_counted: (number | null)[]
  /** Phạm vi HĐLĐ của người xem bỏ bớt HĐ của nơi này (vd loại trừ một phòng) → backend không so, tiền để null. */
  limited_scope?: boolean
}

/** Chi tiết một kế hoạch — `GET /api/headcount-plans/{id}`. */
export interface HeadcountPlanDetail extends HeadcountPlanListItem {
  approver_employee_id: number
  approver_name?: string
  template_id: number
  cost_items: HrCostItem[]
  lines: HeadcountPlanLine[]
  documents: HeadcountPlanDocumentLink[]
  /** `null` khi dữ liệu cũ sai luật tính — trang vẫn mở được. */
  computed: HeadcountPlanComputed | null
  /** Người xem được xem tiền của pháp nhân của kế hoạch này. */
  can_see_money?: boolean
  /**
   * Tệp đính kèm bị ẩn (có thể là bảng tính chi phí) — cùng luật che tiền; khi đó `files` rỗng và
   * cửa `/api/attachments` cũng chặn, nên giao diện không dựng khối tệp.
   */
  files_hidden?: boolean
}

/** `POST /` trả chi tiết + tên khoản của mẫu bị BỎ khi chép (mọi tháng rơi nằm ngoài kỳ). */
export interface HeadcountPlanCreateResult extends HeadcountPlanDetail {
  skipped_items?: string[]
}

/** Số người đang làm + lương bình quân theo vị trí — `GET /position-stats`. */
export interface HeadcountPlanPositionStat {
  position_id: number
  position_name: string
  current_count: number
  avg_base_salary: number | null
  avg_allowance: number | null
}

/**
 * Bản nháp gửi `POST /compute` (`PlanDraft` ở backend — `extra="forbid"`, KHÔNG có `document_ids`).
 * Khoản không mang `id`; dòng không mang `position_name`.
 */
export interface HeadcountPlanDraftPayload {
  year: number
  period_type: number
  period_no: number
  company_id: number
  department_id: number
  basis_no: string
  basis_date: string | null
  approver_employee_id: number
  note: string
  cost_items: HeadcountPlanCostItemPayload[]
  lines: HeadcountPlanLinePayload[]
}

export type HeadcountPlanCostItemPayload = Omit<HrCostItem, 'id' | 'rate' | 'factor'> & { rate: number; factor: number }
export type HeadcountPlanLinePayload = Omit<HeadcountPlanLine, 'id' | 'position_name'>

/** `PUT /{id}` — thay nguyên header + khoản + dòng + văn bản liên kết. */
export interface HeadcountPlanPayload extends HeadcountPlanDraftPayload {
  document_ids: number[]
}

/**
 * `POST /` — tạo mới. `cost_items` vắng = backend CHÉP từ `template_id` (bỏ khoản rơi ngoài kỳ, trả
 * `skipped_items`); có = dùng đúng bộ khoản người dùng đã sửa trên form.
 */
export interface HeadcountPlanCreatePayload extends Omit<HeadcountPlanPayload, 'cost_items'> {
  template_id: number
  cost_items?: HeadcountPlanCostItemPayload[]
}

/** Kết quả nhập CSV dòng vị trí vào MỘT kế hoạch. */
export interface HeadcountPlanLinesImportResult {
  created?: number
  updated?: number
}

/** Giá trị «Toàn pháp nhân» của ô phòng ban — `0` là giá trị THẬT, không phải «chưa chọn». */
export const WHOLE_COMPANY_DEPARTMENT_ID = 0
export const WHOLE_COMPANY_LABEL = 'Toàn pháp nhân'
/** Dòng «Không theo vị trí» mang `position_id = 0`. */
export const NO_POSITION_ID = 0
export const NO_POSITION_LABEL = 'Không theo vị trí'
