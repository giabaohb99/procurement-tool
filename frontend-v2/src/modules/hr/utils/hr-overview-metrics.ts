import { CHART_COLORS, CHART_NEUTRAL, type ChartDatum } from '@/shared/ui/chart'
import type { DonutSlice } from '@/shared/ui/donut-chart'
import { parseLocalDate } from '@/shared/utils/format-date'
import { EMPLOYEE_STATUS_OPTIONS, type Employee } from '../types/employee'

/**
 * Phép đếm THUẦN của trang Tổng quan Nhân sự.
 *
 * Tách khỏi `use-hr-overview.ts` để kiểm được không cần dựng React: mọi quy tắc
 * "thế nào là hồ sơ thiếu thông tin" nằm ở đây, và đó là thứ dễ lệch nhất khi
 * backend thêm cột mới.
 */

/** Số hạng mục tối đa vẽ trên một biểu đồ; phần đuôi gom vào "Khác". */
const MAX_BARS = 12

const OTHER = 'Khác'

/**
 * Đếm theo khóa rồi xếp giảm dần; phần đuôi quá dài gom vào một dòng "Khác".
 *
 * Dòng gom LUÔN ghi rõ nó nuốt bao nhiêu mục (`Khác (5 mục)`) — cắt bớt mà
 * không nói thì biểu đồ đọc ra như đã liệt kê hết.
 */
export function groupCount(
  employees: Employee[],
  keyOf: (employee: Employee) => string,
  maxBars: number = MAX_BARS,
): ChartDatum[] {
  const counter = new Map<string, number>()
  for (const employee of employees) {
    const key = keyOf(employee)
    counter.set(key, (counter.get(key) ?? 0) + 1)
  }

  const rows = [...counter.entries()]
    .map(([label, value]) => ({ label, value }))
    .sort((a, b) => b.value - a.value || a.label.localeCompare(b.label, 'vi'))

  if (rows.length <= maxBars) return rows

  const head = rows.slice(0, maxBars - 1)
  const tail = rows.slice(maxBars - 1)
  return [...head, { label: `${OTHER} (${tail.length} mục)`, value: sumOf(tail) }]
}

/**
 * Lát bánh theo trạng thái nhân sự. Màu bám THỨ TỰ CỐ ĐỊNH của
 * `EMPLOYEE_STATUS_OPTIONS`, không bám thứ hạng số lượng — có vậy "Chính thức" mới
 * luôn là một màu dù dữ liệu đổi. Trạng thái lạ (dữ liệu cũ, để trống) gom vào
 * "Khác" màu xám.
 *
 * B-03: đếm theo MÃ, chỉ đổi sang nhãn lúc dựng lát. Đếm theo nhãn thì sửa một chữ
 * trong nhãn là mọi nhân sự rơi hết vào "Khác".
 */
export function buildStatusSlices(employees: Employee[]): DonutSlice[] {
  const counter = new Map<string, number>()
  const known = new Set(EMPLOYEE_STATUS_OPTIONS.map((option) => option.value))
  for (const employee of employees) {
    const status = employee.status?.trim() || ''
    const key = known.has(status) ? status : OTHER
    counter.set(key, (counter.get(key) ?? 0) + 1)
  }

  const slices: DonutSlice[] = EMPLOYEE_STATUS_OPTIONS.map(({ value, label }, index) => ({
    label,
    value: counter.get(value) ?? 0,
    color: CHART_COLORS[index],
  }))

  const other = counter.get(OTHER) ?? 0
  if (other > 0) slices.push({ label: OTHER, value: other, color: CHART_NEUTRAL })

  // Bỏ lát rỗng để chú giải không liệt kê một loạt số 0.
  return slices.filter((slice) => slice.value > 0)
}

/** Bốn ô của hồ sơ mà bỏ trống thì có hậu quả ở nơi khác — xem `ProfileGapsCard`. */
export interface ProfileGaps {
  noDepartment: number
  noManager: number
  noHireDate: number
  noPosition: number
  /**
   * Số HỒ SƠ thiếu ít nhất một ô, KHÔNG phải tổng bốn số trên: một người bỏ
   * trống cả bốn ô vẫn là một hồ sơ cần bổ sung, cộng dồn thì thẻ số liệu báo 4.
   */
  total: number
}

/**
 * Đếm hồ sơ thiếu thông tin. Chỉ tính người ĐANG LÀM VIỆC — người đã nghỉ mà
 * chưa khai quản lý trực tiếp thì không ai phải đi nhập bù nữa.
 */
export function countProfileGaps(employees: Employee[]): ProfileGaps {
  const gaps: ProfileGaps = {
    noDepartment: 0,
    noManager: 0,
    noHireDate: 0,
    noPosition: 0,
    total: 0,
  }

  for (const employee of employees) {
    if (!employee.is_active) continue

    const missing = [
      !employee.department_id,
      !hasManager(employee),
      !employee.hire_date,
      !hasPosition(employee),
    ]

    if (missing[0]) gaps.noDepartment += 1
    if (missing[1]) gaps.noManager += 1
    if (missing[2]) gaps.noHireDate += 1
    if (missing[3]) gaps.noPosition += 1
    if (missing.some(Boolean)) gaps.total += 1
  }

  return gaps
}

/**
 * Số người vào làm trong `days` ngày gần nhất.
 *
 * Ngày vào làm ở TƯƠNG LAI không tính: hợp đồng đã ký nhưng người chưa tới, đưa
 * vào ô "mới vào" thì con số nói sai về đội hình đang có.
 */
export function countRecentHires(employees: Employee[], today: Date, days: number): number {
  const floor = new Date(today.getFullYear(), today.getMonth(), today.getDate() - days)
  const ceiling = new Date(today.getFullYear(), today.getMonth(), today.getDate())

  return employees.filter((employee) => {
    if (!employee.is_active) return false
    const hired = parseLocalDate(employee.hire_date)
    return hired !== undefined && hired >= floor && hired <= ceiling
  }).length
}

/**
 * Có người quản lý trực tiếp chưa.
 *
 * Đọc `manager_id` khi có, nếu không thì lùi về tên: câu trả lời của các đường
 * API dựng TRƯỚC cột `manager_id` (duoc-CR-314) không mang khóa đó, và
 * `undefined` mà hiểu thành 0 thì cả công ty bị đếm là "chưa gán".
 */
function hasManager(employee: Employee): boolean {
  if (typeof employee.manager_id === 'number') return employee.manager_id > 0
  return Boolean(employee.direct_manager_name?.trim())
}

/** Chức vụ tính là ĐÃ GÁN khi có khóa danh mục HOẶC còn nhãn chữ của dữ liệu cũ. */
function hasPosition(employee: Employee): boolean {
  if (typeof employee.position_id === 'number' && employee.position_id > 0) return true
  return Boolean(employee.position?.trim())
}

function sumOf(rows: ChartDatum[]): number {
  return rows.reduce((total, row) => total + row.value, 0)
}
