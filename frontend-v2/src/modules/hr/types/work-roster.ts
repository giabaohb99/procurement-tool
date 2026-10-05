/**
 * Kiểu dữ liệu của màn «Xem lịch» (ai làm, ai nghỉ) — khớp hợp đồng API
 * `GET /api/work-schedules/tools/roster` ở
 * `plans/261005-0925-hr-lich-lam-viec/phase-07-*.md`.
 */

/** Đơn nghỉ phủ lên một ô. Chỉ có khi người xem đọc được đơn đó. */
export interface WorkRosterLeave {
  request_id: number
  code: string
  leave_type_name: string
  status: number
  status_label: string
  /** `true` = đã duyệt (tô đặc); `false` = chờ duyệt (viền nét đứt). */
  is_approved: boolean
  /** Nửa buổi nào CỦA NGÀY ĐÓ bị nghỉ. */
  morning: boolean
  afternoon: boolean
}

export interface WorkRosterCell {
  /** `YYYY-MM-DD`. */
  date: string
  /** `WorkDayKind`: 1 Nghỉ · 2 Cả ngày · 3 Buổi sáng · 4 Buổi chiều. */
  work_kind: number
  /** "HH:MM" hoặc rỗng. */
  start_time: string | null
  end_time: string | null
  schedule_name: string
  is_holiday: boolean
  /** Tên ngày lễ áp cho pháp nhân CỦA NGƯỜI NÀY (chung hoặc riêng); rỗng khi không lễ. */
  holiday_name: string
  leave: WorkRosterLeave | null
}

export interface WorkRosterDay {
  date: string
  /** 0 = Thứ Hai … 6 = Chủ nhật. */
  weekday: number
  /** CHỈ ngày lễ chung (mọi pháp nhân). Lễ riêng của pháp nhân nằm ở `WorkRosterCell.holiday_name`. */
  holiday_name: string
}

export interface WorkRosterItem {
  employee_id: number
  code: string
  full_name: string
  department_id: number
  department_name: string
  cells: WorkRosterCell[]
}

export interface WorkRoster {
  from_date: string
  to_date: string
  days: WorkRosterDay[]
  total: number
  items: WorkRosterItem[]
}

/** Tham số hỏi lưới. `0` ở `company_id` / `department_id` = mọi. */
export interface WorkRosterParams {
  from_date: string
  to_date: string
  company_id?: number
  department_id?: number
  q?: string
  page?: number
  page_size?: number
}
