import type {
  ContractReminder,
  MonthlyReminderGroupKey,
  MonthlyReminderGroupPayload,
  MonthlyReminders,
} from '../types/monthly-reminders'

/** Một dòng đã dựng sẵn để vẽ — mọi nhóm chung một dạng. */
export interface MonthlyReminderRow {
  /** Khóa React, duy nhất trong nhóm. */
  id: string
  employeeId: number
  employeeCode: string
  employeeName: string
  department: string
  /** Câu mốc: «Sinh nhật 05/10», «Tròn 5 năm làm việc · 03/10», «Thử việc hết hạn 20/10». */
  detail: string
  /** `true` = việc gấp (HĐ còn ≤ ngưỡng đỏ / đã quá hạn). */
  urgent: boolean
}

export interface MonthlyReminderGroup {
  key: MonthlyReminderGroupKey
  title: string
  rows: MonthlyReminderRow[]
  /** Số thật ở backend — có thể lớn hơn `rows.length` khi chạm trần. */
  total: number
  truncated: boolean
}

const pad2 = (n: number) => String(n).padStart(2, '0')

/** `day` + `month` → `'dd/MM'`; thiếu số thì trả chuỗi rỗng. */
export function formatDayMonth(day: number | null | undefined, month: number | null | undefined): string {
  if (!day || !month) return ''
  return `${pad2(day)}/${pad2(month)}`
}

/** `'YYYY-MM-DD'` → `'dd/MM'`; chuỗi lạ thì trả lại nguyên văn. */
export function formatIsoDayMonth(value: string | null | undefined): string {
  const m = /^\d{4}-(\d{2})-(\d{2})/.exec(value ?? '')
  return m ? `${m[2]}/${m[1]}` : (value ?? '')
}

function isShown<T>(group: MonthlyReminderGroupPayload<T> | undefined): group is MonthlyReminderGroupPayload<T> {
  return !!group && group.allowed !== false && Array.isArray(group.items)
}

function contractRow(c: ContractReminder, probation: boolean): MonthlyReminderRow {
  return {
    id: `${probation ? 'p' : 'c'}-${c.contract_code || c.employee_id}-${c.end_date}`,
    employeeId: c.employee_id,
    employeeCode: c.employee_code,
    employeeName: c.employee_name,
    department: c.department ?? '',
    detail: `${probation ? 'Thử việc' : 'Hợp đồng'} hết hạn ${formatIsoDayMonth(c.end_date)}`,
    urgent: c.level === 'danger',
  }
}

/**
 * Ba nhóm để vẽ, đúng thứ tự cố định (việc vui trước, việc phải làm sau). Nhóm `allowed: false`
 * hoặc vắng (máy chủ cũ) = người xem thiếu quyền → BỎ HẲN, không dựng cột «không có ai» (câu đó
 * là trấn an sai). HĐ và thử việc gộp một nhóm, sắp theo ngày hết hạn; nhóm gộp chỉ hiện khi CẢ
 * HAI nửa đều được phép đọc (cùng một quyền ở backend, nên thực tế hai nửa luôn cùng cờ).
 */
export function buildMonthlyReminderGroups(data: MonthlyReminders | undefined): MonthlyReminderGroup[] {
  if (!data) return []
  const groups: MonthlyReminderGroup[] = []

  if (isShown(data.birthdays)) {
    const g = data.birthdays
    groups.push({
      key: 'birthdays',
      title: 'Sinh nhật',
      rows: g.items.map((b) => ({
        id: `b-${b.employee_id}`,
        employeeId: b.employee_id,
        employeeCode: b.employee_code,
        employeeName: b.employee_name,
        department: b.department ?? '',
        detail: `Sinh nhật ${formatDayMonth(b.day, b.month)}`,
        urgent: false,
      })),
      total: g.total ?? g.items.length,
      truncated: !!g.truncated,
    })
  }

  if (isShown(data.anniversaries)) {
    const g = data.anniversaries
    groups.push({
      key: 'anniversaries',
      title: 'Kỷ niệm năm làm việc',
      rows: g.items.map((a) => ({
        id: `a-${a.employee_id}`,
        employeeId: a.employee_id,
        employeeCode: a.employee_code,
        employeeName: a.employee_name,
        department: a.department ?? '',
        detail: `Tròn ${a.years} năm làm việc · ${formatDayMonth(a.day, a.month)}`,
        urgent: false,
      })),
      total: g.total ?? g.items.length,
      truncated: !!g.truncated,
    })
  }

  if (isShown(data.contracts) && isShown(data.probations)) {
    const c = data.contracts
    const p = data.probations
    const merged = [
      ...c.items.map((x) => ({ end: x.end_date, row: contractRow(x, false) })),
      ...p.items.map((x) => ({ end: x.end_date, row: contractRow(x, true) })),
    ].sort((a, b) => a.end.localeCompare(b.end))
    groups.push({
      key: 'expiring_contracts',
      title: 'HĐ / thử việc hết hạn',
      rows: merged.map((m) => m.row),
      total: (c.total ?? c.items.length) + (p.total ?? p.items.length),
      truncated: !!c.truncated || !!p.truncated,
    })
  }

  return groups
}

/** Tháng của một ngày, dạng `YYYY-MM` theo giờ máy (người dùng ở VN). */
export function toMonthKey(date: Date): string {
  return `${date.getFullYear()}-${pad2(date.getMonth() + 1)}`
}

/** `'YYYY-MM'` → ngày 1 của tháng đó; chuỗi hỏng thì về tháng của `fallback`. */
export function monthKeyToDate(key: string, fallback: Date): Date {
  const m = /^(\d{4})-(\d{2})$/.exec(key)
  const month = m ? Number(m[2]) : 0
  if (!m || month < 1 || month > 12) return new Date(fallback.getFullYear(), fallback.getMonth(), 1)
  return new Date(Number(m[1]), month - 1, 1)
}

/** Lùi / tiến `delta` tháng — tính từ NGÀY 1 nên không tràn khi tháng đích ngắn hơn. */
export function shiftMonthKey(key: string, delta: number, fallback: Date): string {
  const d = monthKeyToDate(key, fallback)
  return toMonthKey(new Date(d.getFullYear(), d.getMonth() + delta, 1))
}

/** Nhãn tháng trên nút chọn: «Tháng 10/2026». */
export function formatMonthKeyLabel(key: string, fallback: Date): string {
  const d = monthKeyToDate(key, fallback)
  return `Tháng ${d.getMonth() + 1}/${d.getFullYear()}`
}

/** Nguồn HĐ hết hạn chỉ nhìn trước tối đa 180 ngày (`expiry_service.MAX_WINDOW_DAYS`). */
export const CONTRACT_LOOKAHEAD_DAYS = 180

/**
 * Tháng đang xem có phần nào nằm QUÁ cửa sổ 180 ngày của nguồn HĐ không — có thì nhóm HĐ của
 * tháng đó có thể thiếu, phải nói ra kẻo «không có ai» thành trấn an sai.
 */
export function isPastContractLookahead(monthKey: string, today: Date): boolean {
  const start = monthKeyToDate(monthKey, today)
  const monthEnd = new Date(start.getFullYear(), start.getMonth() + 1, 0)
  const limit = new Date(today.getFullYear(), today.getMonth(), today.getDate() + CONTRACT_LOOKAHEAD_DAYS)
  return monthEnd > limit
}
