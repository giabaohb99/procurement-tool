import type { Employee } from '../types/employee'
import type { EmployeeWorkHistory } from '../types/employee-work-history'

/**
 * Câu hỏi áp hồ sơ (Q1/Q2) — hàm THUẦN, không gọi API, không mở hộp thoại nào.
 *
 * Chỉ QUYẾT ĐỊNH có nên hỏi hay không và hỏi CÂU GÌ; hộp thoại (`confirm()`
 * chung hoặc `EmployeeWorkHistoryResignConfirmDialog` riêng) và lời gọi
 * `/apply` nằm ở nơi gọi (`employee-work-history-form-dialog.tsx` — lúc LƯU,
 * `employee-tab-work-history.tsx` — bấm nút ▶ trên dòng có sẵn, H1). BE vẫn là
 * chốt chặn cuối (phase 02 §"Áp vào hồ sơ") — hàm này chỉ tránh hỏi những câu
 * BE sẽ từ chối ngay, và tránh KHÔNG hỏi những câu lẽ ra phải hỏi.
 *
 * ⚠️ Mã số event_type mirror `backend/app/core/hr_work_history_codes.py`
 * (`MAIN_TRACK` ∩ không-Thôi-việc = `POSITION_TRACK`, `CONCURRENT`, `RESIGN`).
 * Không import được từ backend nên khai lại — lệch là lủng, nhưng cả hai phía
 * đều có test canh theo tên hằng số này.
 */
export const POSITION_TRACK = new Set([1, 2, 3, 5]) // Tuyển dụng · Điều chuyển · Bổ nhiệm · Miễn nhiệm
export const CONCURRENT_TYPE = 4 // Kiêm nhiệm
export const RESIGN_TYPE = 6 // Thôi việc
/** Nhóm CHÍNH (khác kiêm nhiệm) — khớp `MAIN_TRACK` của backend, gồm cả Thôi việc. */
export const MAIN_TRACK = new Set([...POSITION_TRACK, RESIGN_TYPE])

/** Khớp `employee/service.py::STATUS_RESIGNED`. */
const RESIGNED_STATUS = 'resigned'

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/

export interface ApplyPromptValues {
  event_type: number
  from_date: string
  to_date: string
  company_id: number
  /** NHÃN mới (để dựng câu "cũ → mới") — bỏ trống thì câu chỉ nói "(chưa gán)". */
  company_label?: string
  department_id: number
  department_label?: string
  position_id: number
  position_label?: string
}

export type ApplyPrompt =
  | null
  | { kind: 'profile'; changes: string[] }
  | { kind: 'resign'; resignDate: string }

function isValidDate(value: string): boolean {
  return DATE_RE.test(value)
}

/** Dòng đã KẾT THÚC trước `today` (chốt `is_current` của backend, lật dấu). */
function isEnded(toDate: string, today: string): boolean {
  return toDate !== '' && isValidDate(toDate) && toDate < today
}

/** `"Pháp nhân: Công ty A → Công ty B"` — rỗng ở bên nào thì nói "(chưa gán)". */
function describeFieldChange(fieldLabel: string, oldLabel: string | null | undefined, newLabel: string | undefined): string {
  const oldText = oldLabel && oldLabel.trim() ? oldLabel : '(chưa gán)'
  const newText = newLabel && newLabel.trim() ? newLabel : '(chưa gán)'
  return `${fieldLabel}: ${oldText} → ${newText}`
}

/** `«Phòng Kế toán»` khi có nhãn, `này` khi không (giữ đúng câu cũ lúc chưa có nhãn). */
function departmentPhrase(label: string | undefined): string {
  return label && label.trim() ? `«${label}»` : 'này'
}

/**
 * Có dòng CHÍNH (MAIN_TRACK — gồm cả Thôi việc) khác, hiệu lực MUỘN HƠN dòng
 * đang xét — tức dòng đang xét là NHẬP BÙ lịch sử cũ, không phải trạng thái
 * mới nhất của hồ sơ. `excludeId` loại dòng đang sửa khỏi chính nó.
 */
function hasLaterMainRow(rows: EmployeeWorkHistory[], excludeId: number, fromDate: string): boolean {
  return rows.some((r) => r.id !== excludeId && MAIN_TRACK.has(r.event_type) && r.from_date > fromDate)
}

export function planApplyPrompt(
  values: ApplyPromptValues,
  employee: Employee,
  extraDeptIds: number[],
  today: string,
  /** Toàn bộ dòng đã có của hồ sơ — để nhận biết NHẬP BÙ lịch sử cũ (M6). */
  existingRows: EmployeeWorkHistory[] = [],
  /** Id dòng đang SỬA (0 = đang tạo mới) — tự loại khỏi `existingRows`. */
  editingId = 0,
): ApplyPrompt {
  //  Ngày rỗng/không hợp lệ, hoặc CHƯA tới ngày hiệu lực (Q1) → không hỏi. BE
  //  cũng từ chối `/apply` với lý do «chưa tới ngày hiệu lực» — hỏi trước là hỏi hụt.
  if (!isValidDate(values.from_date)) return null
  if (values.from_date > today) return null

  if (values.event_type === RESIGN_TYPE) {
    //  CỐ Ý không xét `hasLaterMainRow` ở đây: Thôi việc luôn hỏi, kể cả nhập
    //  bù quá khứ (xem test "quá khứ → kind resign ... nhập bù") — hệ quả khóa
    //  tài khoản nặng hơn một câu hỏi đổi hồ sơ nên không tự suy luận bỏ qua.
    const alreadyResigned =
      employee.status === RESIGNED_STATUS && (employee.resign_date ?? '') === values.from_date
    if (alreadyResigned) return null
    return { kind: 'resign', resignDate: values.from_date }
  }

  if (POSITION_TRACK.has(values.event_type)) {
    //  Loại 1,2,3,5: dòng đã kết thúc thì không còn là "hiện tại" của hồ sơ.
    if (isEnded(values.to_date, today)) return null
    //  Có dòng CHÍNH khác mới hơn → dòng này là nhập bù lịch sử cũ, không hỏi.
    if (hasLaterMainRow(existingRows, editingId, values.from_date)) return null

    const changes: string[] = []
    if (values.company_id > 0 && values.company_id !== employee.company_id) {
      changes.push(describeFieldChange('Pháp nhân', employee.company_name, values.company_label))
    }
    if (values.department_id > 0 && values.department_id !== employee.department_id) {
      changes.push(describeFieldChange('Phòng ban', employee.department_name, values.department_label))
    }
    if (values.position_id > 0 && values.position_id !== (employee.position_id ?? 0)) {
      changes.push(describeFieldChange('Chức vụ', employee.position, values.position_label))
    }
    if (changes.length === 0) return null
    return { kind: 'profile', changes }
  }

  if (values.event_type === CONCURRENT_TYPE) {
    if (values.department_id <= 0) return null
    //  Cùng lý do với POSITION_TRACK — kiêm nhiệm nhập bù quá khứ không hỏi.
    if (hasLaterMainRow(existingRows, editingId, values.from_date)) return null

    const hasDept = extraDeptIds.includes(values.department_id)
    if (isEnded(values.to_date, today)) {
      //  Đã kết thúc mà phòng kiêm nhiệm vẫn còn trong danh sách → hỏi GỠ.
      return hasDept
        ? { kind: 'profile', changes: [`Gỡ kiêm nhiệm phòng ban ${departmentPhrase(values.department_label)}`] }
        : null
    }
    //  Đang hiệu lực mà phòng chưa có trong danh sách kiêm nhiệm → hỏi THÊM.
    return hasDept
      ? null
      : { kind: 'profile', changes: [`Thêm kiêm nhiệm phòng ban ${departmentPhrase(values.department_label)}`] }
  }

  //  Loại "Khác" (9) không nằm trong `APPLICABLE` của backend — không bao giờ hỏi.
  return null
}

/**
 * Chuyển một dòng ĐÃ CÓ (`EmployeeWorkHistory`) thành `ApplyPromptValues` —
 * dùng ở nút ▶ «Áp vào hồ sơ» trên từng dòng (H1, `employee-tab-work-history.tsx`),
 * để dùng LẠI đúng một bộ luật `planApplyPrompt` cho cả hai nơi hỏi (lưu dòng
 * và áp dòng có sẵn), không chép luật ra bản thứ hai. Dòng đã có sẵn tên hiển
 * thị (`company_name`/`department_name`/`position_label`) nên không cần tra
 * danh mục như lúc LƯU (xem `employee-work-history-form-dialog.tsx`).
 */
export function workHistoryRowToApplyValues(row: EmployeeWorkHistory): ApplyPromptValues {
  return {
    event_type: row.event_type,
    from_date: row.from_date,
    to_date: row.to_date ?? '',
    company_id: row.company_id,
    company_label: row.company_name,
    department_id: row.department_id,
    department_label: row.department_name,
    position_id: row.position_id,
    position_label: row.position_label,
  }
}
