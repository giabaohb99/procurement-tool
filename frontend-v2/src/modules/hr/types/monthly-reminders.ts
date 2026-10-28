/**
 * Ô «Lịch nhắc trong tháng» của Tổng quan Nhân sự (duoc-CR-689) — khớp
 * `GET /api/employees/monthly-reminders?month=YYYY-MM`
 * (`backend/app/modules/employee/monthly_reminders_service.py`).
 *
 * ⚠️ Nhóm người xem THIẾU QUYỀN trả `allowed: false` + rỗng: sinh nhật cần `employee_sensitive.read`,
 * HĐ / thử việc cần `labor_contract.read`. `allowed: false` ≠ rỗng — không có quyền thì giấu cả
 * nhóm, có quyền mà rỗng thì nói «không có ai». Trần 200 dòng mỗi nhóm (`total` là số thật).
 */
export interface MonthlyReminderPerson {
  employee_id: number
  employee_code: string
  employee_name: string
  /** Tên phòng ban chính. */
  department?: string
}

/** Sinh nhật — CHỈ ngày + tháng, backend không bao giờ trả năm sinh. */
export interface BirthdayReminder extends MonthlyReminderPerson {
  day: number
  month: number
}

/** Kỷ niệm 1 / 3 / 5 / 10 năm vào làm. */
export interface AnniversaryReminder extends MonthlyReminderPerson {
  day: number
  month: number
  years: number
  hire_date: string
}

/** HĐLĐ / HĐ thử việc kết thúc trong tháng (cùng nguồn với thẻ «HĐLĐ sắp hết hạn»). */
export interface ContractReminder extends MonthlyReminderPerson {
  contract_code: string
  contract_no: string
  end_date: string
  days_left: number
  level: 'danger' | 'warn' | string
}

export interface MonthlyReminderGroupPayload<T> {
  allowed: boolean
  items: T[]
  total: number
  truncated: boolean
}

export interface MonthlyReminders {
  month: string
  birthdays?: MonthlyReminderGroupPayload<BirthdayReminder>
  anniversaries?: MonthlyReminderGroupPayload<AnniversaryReminder>
  contracts?: MonthlyReminderGroupPayload<ContractReminder>
  probations?: MonthlyReminderGroupPayload<ContractReminder>
}

/** Ba nhóm BÀY trên màn — `contracts` + `probations` của backend gộp chung một nhóm. */
export type MonthlyReminderGroupKey = 'birthdays' | 'anniversaries' | 'expiring_contracts'
