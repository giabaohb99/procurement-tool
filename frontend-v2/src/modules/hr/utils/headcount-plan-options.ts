import type { CrudOption } from '@/shared/crud'

import { WHOLE_COMPANY_DEPARTMENT_ID, WHOLE_COMPANY_LABEL } from '../types/headcount-plan'

/** Backend chặn năm ngoài 2000–2100 (`schema.Year`) — dải chọn không được vượt ra ngoài đó. */
const MIN_PLAN_YEAR = 2000
const MAX_PLAN_YEAR = 2100

/**
 * Năm để chọn ở ô lọc và ô nhập: năm sau → ba năm trước, mới nhất lên đầu. Kế hoạch thường
 * lập cho năm SAU từ quý 4, nên năm sau phải có sẵn; ba năm trước để còn so lại kế hoạch cũ.
 */
export function buildHeadcountPlanYearOptions(currentYear: number): CrudOption[] {
  const years: CrudOption[] = []
  for (let y = currentYear + 1; y >= currentYear - 3; y -= 1) {
    if (y < MIN_PLAN_YEAR || y > MAX_PLAN_YEAR) continue
    years.push({ value: String(y), label: String(y) })
  }
  return years
}

interface DepartmentLike {
  id: number
  name: string
}

/**
 * Ô chọn phòng của kế hoạch nhân sự (dùng cho cả ô lọc lẫn ô nhập ở trang kế hoạch): «Toàn pháp nhân» (`0`) đứng đầu, rồi MỌI phòng đang dùng,
 * xếp theo tên tiếng Việt, mỗi phòng một lần.
 *
 * ⚠️ Không lọc theo pháp nhân: phòng ban DÙNG CHUNG cho mọi pháp nhân (dev + local không có ánh xạ
 * phòng ↔ pháp nhân, `Department.company_id = 0`), và backend chỉ bắt phòng có thật (chốt
 * 28/10/2026). ⚠️ `0` là giá trị THẬT (dòng của cả pháp nhân), không phải «chưa chọn» — nên nó
 * phải là một MỤC chọn được, không được để rơi về chữ gợi ý.
 */
export function buildHeadcountPlanDepartmentOptions(departments: readonly DepartmentLike[]): CrudOption[] {
  const seen = new Map<number, string>()
  for (const d of departments) if (d.id > 0 && !seen.has(d.id)) seen.set(d.id, d.name)
  const rows = [...seen]
    .sort((a, b) => a[1].localeCompare(b[1], 'vi'))
    .map(([id, name]) => ({ value: String(id), label: name }))
  return [{ value: String(WHOLE_COMPANY_DEPARTMENT_ID), label: WHOLE_COMPANY_LABEL }, ...rows]
}

/** Đuôi backend gắn khi có hơn 20 lỗi: « (và 7 lỗi khác)». */
const MORE_ERRORS_TAIL = /\s*\((và \d+ lỗi khác)\)$/

/**
 * Tách câu lỗi nhập CSV thành từng dòng. Backend (`csv_service.import_rows`) gộp mọi lỗi vào MỘT
 * câu: «Tệp CSV có lỗi, chưa ghi dòng nào: Dòng 2: … | Dòng 5: … (và 7 lỗi khác)». Bỏ phần mở
 * đầu (hộp thoại đã nói «không dòng nào được ghi»), tách theo « | », đuôi «và N lỗi khác» thành
 * dòng riêng. Câu không có «Dòng n» (vd «Tệp CSV thiếu cột: year») giữ nguyên một dòng.
 */
export function splitImportErrorMessage(message: string): string[] {
  const text = message.trim()
  if (!text) return []
  const start = text.search(/Dòng \d+:/)
  if (start < 0) return [text]
  const tail = MORE_ERRORS_TAIL.exec(text)
  const body = (tail ? text.slice(0, tail.index) : text).slice(start)
  const lines = body
    .split(' | ')
    .map((line) => line.trim())
    .filter(Boolean)
  return tail ? [...lines, `…${tail[1]}`] : lines
}
