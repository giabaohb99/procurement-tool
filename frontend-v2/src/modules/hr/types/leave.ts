/**
 * Kiểu dữ liệu của phân hệ Nghỉ phép (CR-259).
 *
 * Cột trạng thái / buổi / đơn vị là **SỐ** (R2/QĐ-11) — backend trả kèm nhãn
 * tiếng Việt ở khóa `*_label`. So sánh thì so SỐ với hằng số dưới đây, hiện thì
 * hiện nhãn. Không bao giờ so chuỗi tiếng Việt.
 *
 * ⚠️ Các hằng số dưới đây phải khớp `backend/app/modules/leave/constants.py`.
 * Chúng KHÔNG do `gen_status_ts.py` sinh: kịch bản đó chỉ sinh cho bộ mã CHUỖI
 * khai qua `status_catalog`, còn bộ mã số thì cả `document` lẫn `vehicle_booking`
 * đều khai tay ở hai đầu — theo đúng khuôn đó.
 */

// ── Trạng thái đơn ─────────────────────────────────────────────────────────────

export const LEAVE_STATUS = {
  DRAFT: 1,
  PENDING: 2,
  APPROVED: 3,
  REJECTED: 4,
  RETURNED: 5,
  CANCELLED: 6,
} as const

export type LeaveStatus = (typeof LEAVE_STATUS)[keyof typeof LEAVE_STATUS]

export const LEAVE_STATUS_LABELS: Record<number, string> = {
  [LEAVE_STATUS.DRAFT]: 'Nháp',
  [LEAVE_STATUS.PENDING]: 'Chờ duyệt',
  [LEAVE_STATUS.APPROVED]: 'Đã duyệt',
  [LEAVE_STATUS.REJECTED]: 'Từ chối',
  [LEAVE_STATUS.RETURNED]: 'Trả về chỉnh sửa',
  [LEAVE_STATUS.CANCELLED]: 'Đã hủy',
}

/** Sửa được khi chưa vào luồng hoặc vừa bị trả về — khớp `EDITABLE_STATUSES`. */
export const EDITABLE_LEAVE_STATUSES: number[] = [
  LEAVE_STATUS.DRAFT,
  LEAVE_STATUS.RETURNED,
]

// ── Phạm vi danh sách đơn nghỉ phép ────────────────────────────────────────────

export const LEAVE_SCOPE = {
  ALL: 'all',
  TO_APPROVE: 'to-approve',
  MINE: 'mine',
  HANDLED: 'handled',
} as const

export type LeaveScope = (typeof LEAVE_SCOPE)[keyof typeof LEAVE_SCOPE]

// ── Buổi nghỉ ──────────────────────────────────────────────────────────────────

export const LEAVE_SESSION = { FULL: 1, MORNING: 2, AFTERNOON: 3, HOURLY: 4 } as const

export const LEAVE_SESSION_LABELS: Record<number, string> = {
  [LEAVE_SESSION.FULL]: 'Cả ngày',
  [LEAVE_SESSION.MORNING]: 'Buổi sáng',
  [LEAVE_SESSION.AFTERNOON]: 'Buổi chiều',
  [LEAVE_SESSION.HOURLY]: 'Theo giờ',
}

/** Đơn khai theo GIỜ — hai ô buổi đều là «Theo giờ», và chỉ trong MỘT ngày. */
export function isHourlyLeave(fromSession: number, toSession: number): boolean {
  return fromSession === LEAVE_SESSION.HOURLY || toSession === LEAVE_SESSION.HOURLY
}

// ── Đơn vị nghỉ (QĐ-NP4) ───────────────────────────────────────────────────────

//  Bản này CHỈ dùng `DAY`. Hai giá trị kia khai sẵn cho lúc có Lịch làm việc.
export const LEAVE_UNIT = { DAY: 1, HALF_DAY: 2, HOUR: 3 } as const

export const LEAVE_UNIT_LABELS: Record<number, string> = {
  [LEAVE_UNIT.DAY]: 'Ngày',
  [LEAVE_UNIT.HALF_DAY]: 'Nửa ngày',
  [LEAVE_UNIT.HOUR]: 'Giờ',
}

// ── Giới tính ──────────────────────────────────────────────────────────────────

//  `0` là CHƯA KHAI, không phải "khác" — và chưa khai thì không bị chặn loại
//  nghỉ nào. Xem `constants.GENDER_UNKNOWN` ở backend.
export const GENDER = { UNKNOWN: 0, MALE: 1, FEMALE: 2 } as const

export const GENDER_LABELS: Record<number, string> = {
  [GENDER.UNKNOWN]: 'Mọi giới',
  [GENDER.MALE]: 'Nam',
  [GENDER.FEMALE]: 'Nữ',
}

// ── Số dư cuối năm ─────────────────────────────────────────────────────────────

//  Ba nước LOẠI TRỪ nhau nên là một ô chọn, không phải hai công tắc — xem
//  `constants.YEAR_END_*` ở backend.
export const YEAR_END_MODE = { DROP: 0, CARRY: 1, CONVERT: 2 } as const

export const YEAR_END_MODE_LABELS: Record<number, string> = {
  [YEAR_END_MODE.DROP]: 'Hết năm là mất',
  [YEAR_END_MODE.CARRY]: 'Mang sang năm sau',
  [YEAR_END_MODE.CONVERT]: 'Quy đổi sang loại nghỉ khác',
}

// ── Bản ghi ────────────────────────────────────────────────────────────────────

/**
 * ⚠️ `type` chứ KHÔNG phải `interface`. Lớp CRUD khai báo nhận
 * `CrudConfig<CrudRecord>` (`Record<string, unknown>`), và TypeScript chỉ cấp
 * chỉ mục ngầm cho **type alias** — `interface` thì không, nên
 * `CrudConfig<LeaveType>` không gán được và typecheck đỏ. Cùng khuôn với
 * `production/types/unit.ts`.
 */
export type LeaveType = {
  id: number
  code: string
  name: string
  is_paid: boolean
  /** Có TRỪ vào quỹ phép năm không. Tách khỏi `is_paid` — xem model backend. */
  counts_balance: boolean
  annual_quota_days: number
  /** `0` = không giới hạn. */
  max_days_per_request: number
  /** Số dư cuối năm đi đâu — xem `YEAR_END_MODE`. */
  year_end_mode: number
  /** Trần MANG ĐI, tính trước khi nhân tỷ lệ. `0` = không trần. */
  carry_over_max_days: number
  /** Phần mang sang hết hạn cuối tháng thứ mấy của năm sau. `0` = không hết hạn. */
  carry_over_expire_month: number
  /** Loại nghỉ ĐÍCH khi quy đổi. `0` = chưa chọn. */
  convert_to_type_id: number
  /** 1 ngày dư → bao nhiêu ngày ở loại đích. 2 đổi 1 thì ghi `0.5`. */
  convert_ratio: number
  /** `0` = mọi giới. */
  gender: number
  require_attachment: boolean
  /** Tính số ngày có trừ T7/CN và ngày lễ không. */
  exclude_holiday: boolean
  sort_order: number
  is_active: boolean
  note: string
}

export interface SeniorityTier {
  id: number
  leave_type_id: number
  years_from: number
  /** `0` = bậc cuối, không có trần trên. */
  years_to: number
  extra_days: number
  note: string
}

/** `type` chứ không `interface` — xem ghi chú ở `LeaveType`. */
export type Holiday = {
  id: number
  /** `0` = áp cho MỌI pháp nhân. */
  company_id: number
  date: string
  name: string
  /** Lặp hằng năm theo ngày/tháng. Tết Âm không lặp được. */
  is_recurring: boolean
  is_active: boolean
}

export interface LeaveBalance {
  id: number
  employee_id: number
  employee_name?: string
  year: number
  leave_type_id: number
  leave_type_name?: string
  company_id: number
  allocated_days: number
  seniority_days: number
  carried_days: number
  adjusted_days: number
  used_days: number
  /** Đang giữ chỗ cho đơn chờ duyệt — đã trừ khỏi `remaining_days`. */
  pending_days: number
  /** Đã mang khỏi dòng này lúc kết sổ cuối năm — cũng đã trừ khỏi `remaining_days`. */
  carried_out_days: number
  /** Phần mang sang đã HẾT HẠN. Chỉ để giải thích, không nằm trong công thức. */
  carried_expired_days: number
  note: string
  total_days: number
  remaining_days: number
}

export interface LeaveHandover {
  id: number
  employee_id: number
  employee_name?: string
  content: string
  sort_order: number
}

/**
 * MỘT LOẠI NGHỈ trong tờ đơn — *"3 ngày phép năm + 1 ngày không lương"*.
 *
 * ⚠️ **Không có ngày riêng.** Dòng chỉ chia TỔNG SỐ NGÀY của cả đơn, không gắn với
 * khoảng ngày nào (`LeavePeriod`, duoc-CR-683). Quỹ phép trừ theo (người × năm × loại nghỉ) nên hai
 * loại là hai lượt trừ vào hai sổ khác nhau — đó là lý do có bảng dòng.
 */
export interface LeaveRequestLine {
  id: number
  leave_type_id: number
  leave_type_name?: string
  days: number
  sort_order: number
}

/**
 * MỘT KHOẢNG NGÀY LIỀN của tờ đơn (duoc-CR-683) — *"27/10 cả ngày + 03/11 chiều → 07/11"*
 * là một đơn hai khoảng. Backend luôn trả ≥1 khoảng; đơn cũ = đúng một khoảng bằng đầu đơn.
 *
 * ⚠️ Đầu đơn (`from_date` … `to_date`) là BAO NGOÀI của các khoảng, nuốt cả ngày khe ở
 * giữa. Hỏi «ngày D có nghỉ không» thì đi qua `utils/leave-periods.ts`, đừng so đầu đơn.
 */
export interface LeavePeriod {
  id: number
  from_date: string
  from_session: number
  from_session_label?: string
  to_date: string
  to_session: number
  to_session_label?: string
  /** Số ngày tính cho riêng khoảng này — chỉ để hiện, quỹ phép trừ theo dòng loại nghỉ. */
  days: number
  sort_order: number
}

/** Trần số khoảng ngày của một đơn — khớp `MAX_PERIODS` ở `leave/schema.py`. */
export const MAX_LEAVE_PERIODS = 20

export interface LeaveRequest {
  id: number
  code: string
  company_id: number
  company_name?: string
  department_id: number
  department_name?: string
  employee_id: number
  employee_name?: string
  employee_position?: string
  /**
   * Loại nghỉ CHÍNH — dòng chiếm nhiều ngày nhất. Cột dẫn xuất do backend đặt,
   * dùng cho bộ lọc và cột gọn của Lịch nghỉ. Bản kê đủ nằm ở `lines`.
   */
  leave_type_id: number
  leave_type_name?: string
  /** Rỗng ở những đường trả về không gom bản kê — luôn đọc kèm `?? []`. */
  lines?: LeaveRequestLine[]
  /** Bao ngoài: ngày đầu của khoảng ĐẦU và ngày cuối của khoảng CUỐI — xem `LeavePeriod`. */
  from_date: string
  to_date: string
  from_session: number
  to_session: number
  /**
   * Các khoảng ngày của đơn. Có thể vắng ở bản dump cũ / tab trình duyệt cũ — luôn đọc qua
   * `periodsOf(request)` (rơi về một khoảng dựng từ đầu đơn), đừng đọc thẳng.
   */
  periods?: LeavePeriod[]
  /** `HH:MM:SS` — chỉ có khi buổi là «Theo giờ». */
  from_time?: string | null
  to_time?: string | null
  unit: number
  total_days: number
  reason: string
  contact_phone: string
  contact_address: string
  status: number
  status_label?: string
  from_session_label?: string
  to_session_label?: string
  unit_label?: string
  /** `0` = chưa gửi duyệt hoặc môi trường chưa khai luồng nhiều bước. */
  approval_instance_id: number
  /** Giấy GNP sinh ra sau khi duyệt. `0` = chưa sinh. */
  document_id: number
  /** Thời điểm LẬP đơn — mốc đầu tiên của dòng thời gian phê duyệt. */
  created_at?: string | null
  submitted_at?: string | null
  decided_at?: string | null
  decision_note: string
  /**
   * Tên người CHỐT tờ đơn (duyệt · từ chối · trả về · hủy). Chỉ có ở đường lấy
   * MỘT đơn — danh sách không trả, vì tra tên cho từng dòng là N+1.
   */
  decided_by_name?: string
  /** Tên người LẬP đơn (hành chính lập hộ thì khác người nghỉ). Chỉ có ở đường lấy MỘT đơn. */
  created_by_name?: string
  handovers?: LeaveHandover[]
}

/** Dữ liệu của ô «số phép còn lại» trên form — ràng buộc §6.1 của kế hoạch. */
export interface LeaveBalanceHint {
  employee_id: number
  year: number
  leave_type_id: number
  counts_balance: boolean
  total_days: number
  used_days: number
  pending_days: number
  remaining_days: number
  /** Hồ sơ chưa nhập ngày vào làm → thâm niên tính bằng 0, con số có thể thiếu. */
  missing_hire_date: boolean
}

// ── Luồng duyệt dạng ngang (CR-260) ────────────────────────────────────────────

/**
 * Trạng thái MỘT CHẶNG khi vẽ dải chấm. Bộ mã CHUỖI do backend cấp
 * (`approval/steps_service.py`), cố ý khác bộ mã số của trạng thái việc: một
 * chặng có thể có nhiều người duyệt, nên trạng thái chặng là kết luận rút ra từ
 * cả nhóm chứ không phải chép lại của một việc.
 */
export const APPROVAL_STEP_STATE = {
  DONE: 'done',
  CURRENT: 'current',
  TODO: 'todo',
  REJECTED: 'rejected',
  RETURNED: 'returned',
  CANCELLED: 'cancelled',
  /**
   * Chặng KHÔNG CHẠY trên một phiếu đã duyệt xong — bước tùy chọn không cần
   * tới, nhánh rẽ không đi vào, hoặc luồng nhảy cóc qua nó. Khác hẳn
   * `CANCELLED`: chỗ kia nói phiếu chết, chỗ này nói phiếu đi đường ngắn hơn
   * và vẫn duyệt xong. Vẽ chung một màu là người xem đọc một phiếu hoàn chỉnh
   * thành phiếu bị rút.
   */
  SKIPPED: 'skipped',
} as const

export type ApprovalStepState =
  (typeof APPROVAL_STEP_STATE)[keyof typeof APPROVAL_STEP_STATE]

export interface ApprovalStepAssignee {
  employee_id: number
  name: string
  status: number
  decided_at?: string | null
}

export interface ApprovalStep {
  seq: number
  name: string
  state: ApprovalStepState
  /** RỖNG khi chặng chưa mở — bộ máy chưa giao việc cho ai. */
  assignees: ApprovalStepAssignee[]
}

export interface ApprovalFlowStrip {
  instance_id: number
  status: number
  status_label: string
  current_seq: number
  started_by_name: string
  /** Câu rút gọn do BACKEND dựng — đừng chép luật đó sang đây. */
  summary: string
  steps: ApprovalStep[]
}

/** Việc duyệt của CHÍNH tôi trên một tờ đơn (tab «Cần tôi duyệt»). */
export interface LeaveApprovalTask {
  id: number
  instance_id: number
  node_seq: number
  node_name: string
  due_at?: string | null
  is_overdue?: boolean
  /** Bấm THAY ai theo ủy quyền — rỗng nghĩa là việc của chính mình. */
  on_behalf_of_name?: string
  /** Chỉ có ở tab «Tôi đã duyệt»: tôi đã làm gì với tờ đơn này. */
  action_label?: string
  decided_at?: string | null
}

/** Một dòng của hộp việc duyệt — tờ đơn kèm việc của tôi và luồng của nó. */
export interface LeaveInboxRow extends LeaveRequest {
  task: LeaveApprovalTask
  /** `null` khi đơn chưa vào bộ máy duyệt. */
  flow?: ApprovalFlowStrip | null
}

/** Một dòng bảng đối chiếu kết sổ cuối năm (duoc-CR-664) — khớp `carryover_review_service`. */
export interface LeaveCloseYearReviewRow {
  employee_id: number
  employee_code: string
  employee_name: string
  source_type_id: number
  source_type_name: string
  dest_type_id: number
  dest_type_name: string
  /** Tỷ lệ quy đổi: `1` = mang sang nguyên loại. */
  ratio: number
  /** Số dư năm cũ TRƯỚC kết sổ = còn lại + đã chuyển đi. */
  before_days: number
  /** Số dư năm cũ SAU kết sổ. */
  after_days: number
  /** `after - before`, âm = phần đã chuyển đi. */
  diff_days: number
  /** Ngày cộng vào năm sau (đã nhân tỷ lệ, theo cấu hình hiện hành). */
  credited_days: number
  /** Phần mang sang đang có thật ở dòng quỹ năm sau của loại nhận. */
  dest_carried_days: number
}

export interface LeaveCloseYearReview {
  year: number
  next_year: number
  items: LeaveCloseYearReviewRow[]
  totals: {
    row_count: number
    before_days: number
    after_days: number
    diff_days: number
    credited_days: number
  }
}
