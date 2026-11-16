/**
 * Kiểu dữ liệu của màn "Xem lịch" (ai làm, ai nghỉ) — khớp hợp đồng API
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

/**
 * Ca xếp theo ngày của MỘT ô (duoc-CR-761). `segments` là nhãn "HH:MM–HH:MM", `ranges` là cặp giờ tròn
 * `[đầu, cuối)` cho hộp xếp ca; không khung nào = nghỉ cả ngày do xếp ca.
 */
export interface WorkRosterShift {
  segments: string[]
  ranges: number[][]
  hours: number
  note: string
  is_day_off: boolean
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
  /**
   * Ngày này có ca xếp riêng (thắng mẫu tuần), `schedule_name` = "Xếp ca theo ngày". Vắng (backend trước
   * duoc-CR-761) = coi như không.
   */
  is_shift?: boolean
  shift?: WorkRosterShift | null
  /**
   * Ngày đó đang có đơn nghỉ chờ duyệt / đã duyệt GIỮ NGÀY (kể cả ngày lễ, ngày nghỉ, theo giờ, và đơn người xem không
   * đọc được) → không xếp / đổi ca được, backend 409. Vắng = `false`.
   */
  leave_hold?: boolean
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

/**
 * Thao tác trên lưới khi người xem XẾP CA được (duoc-CR-761). Cả hai vắng = lưới chỉ xem như trước.
 */
export interface WorkRosterInteraction {
  /** Bấm ô (người × ngày) → mở hộp xếp ca. */
  onEditCell?: (item: WorkRosterItem, date: string) => void
  /** Ô chọn dòng cho Chép tuần trước. */
  selection?: {
    selectedIds: ReadonlySet<number>
    /** Dòng được phép chọn (Trưởng phòng không chọn được chính mình). */
    canSelect: (employeeId: number) => boolean
    onToggle: (employeeId: number) => void
  }
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
