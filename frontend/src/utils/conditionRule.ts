/**
 * ĐIỀU KIỆN kiểu bộ máy duyệt — đọc/ghi giữa bộ chọn điều kiện và chuỗi JSON (bao-CR-528).
 *
 * Bản v1 của `frontend-v2/src/shared/condition-builder/condition-rule.ts` — HAI BẢN PHẢI KHỚP
 * NHAU: cùng phép so, cùng cách đọc «khai tay», cùng chuỗi JSON gửi lên. Backend
 * (`approval/condition_service.py`) nối các dòng bằng VÀ; cửa lưu của màn Cấu hình chặn
 * trường lạ / phép lạ bằng câu tiếng Việt.
 */

export type ConditionOp =
  | 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'not_in' | 'empty' | 'not_empty'

/** `choice` = chọn từ danh mục (id từ 1) · `number` = số nhập tay (0 là thật) · `bool` = có/không. */
export type ConditionValueKind = 'choice' | 'number' | 'bool'

export type ConditionValue = number | number[] | boolean | null

export type ConditionRow = { field: string; op: ConditionOp; value: ConditionValue }

export type ConditionField = {
  name: string
  label: string
  ops: ConditionOp[]
  kind?: ConditionValueKind
  /** Nguồn lựa chọn của ô danh mục. */
  source?: 'handler_department' | 'department' | 'company' | 'employee'
}

export type ConditionChoice = { id: number; label: string }

const MULTI_OPS: ConditionOp[] = ['in', 'not_in']
const VALUE_FREE_OPS: ConditionOp[] = ['empty', 'not_empty']

export const isMultiValueOp = (op: ConditionOp) => MULTI_OPS.includes(op)
export const isValueFreeOp = (op: ConditionOp) => VALUE_FREE_OPS.includes(op)

export const OP_LABELS: Record<ConditionOp, string> = {
  eq: 'là', ne: 'không phải', gt: 'trên', gte: 'từ ... trở lên', lt: 'dưới',
  lte: 'từ ... trở xuống', in: 'thuộc', not_in: 'không thuộc',
  empty: 'để trống', not_empty: 'có giá trị',
}

/**
 * Ô của phiếu YCMH cho «điều kiện bỏ qua bước thu mua duyệt lần 2». Đúng bằng khóa
 * `purchase_request/service.dispatch_context()` đưa vào (bảng `DISPATCH_CONTEXT_FIELDS`).
 * «Phòng xử lý»: phòng thu mua mặc định đi vào dưới dạng 0 = «để trống», nên bị gỡ khỏi danh
 * sách chọn — điều kiện hay dùng là «Phòng xử lý có giá trị» = phiếu nhờ phòng khác xử lý.
 */
export const PR_DISPATCH_CONDITION_FIELDS: ConditionField[] = [
  { name: 'handler_dept_id', label: 'Phòng xử lý', source: 'handler_department',
    ops: ['not_empty', 'empty', 'in', 'not_in'] },
  { name: 'department_id', label: 'Phòng lập phiếu', source: 'department', ops: ['in', 'not_in'] },
  { name: 'company_id', label: 'Công ty', source: 'company', ops: ['in', 'not_in'] },
  { name: 'requester_id', label: 'Người yêu cầu', source: 'employee', ops: ['in', 'not_in'] },
  { name: 'is_urgent', label: 'Đơn gấp', kind: 'bool', ops: ['eq'] },
  { name: 'line_count', label: 'Số dòng hàng', kind: 'number', ops: ['lte', 'gte', 'eq', 'lt', 'gt'] },
]

/**
 * Chuỗi → các dòng. `advanced: true` = chuỗi vượt ngoài thứ bộ chọn diễn tả được (JSON hỏng,
 * ô lạ, phép lạ, giá trị sai kiểu) — phải hiện nguyên văn, KHÔNG được lặng lẽ ghi đè.
 */
export function parseCondition(raw: string, fields: ConditionField[]): { rows: ConditionRow[]; advanced: boolean } {
  if (!(raw || '').trim()) return { rows: [], advanced: false }
  let data: unknown
  try { data = JSON.parse(raw) } catch { return { rows: [], advanced: true } }
  if (!Array.isArray(data) || data.length === 0) return { rows: [], advanced: true }
  const rows: ConditionRow[] = []
  for (const item of data) {
    const row = readRow(item, fields)
    if (!row) return { rows: [], advanced: true }
    rows.push(row)
  }
  return { rows, advanced: false }
}

function readRow(item: unknown, fields: ConditionField[]): ConditionRow | null {
  if (typeof item !== 'object' || item === null) return null
  const { field, op, value } = item as { field?: unknown; op?: unknown; value?: unknown }
  const def = fields.find((f) => f.name === field)
  if (typeof field !== 'string' || !def) return null
  if (typeof op !== 'string' || !def.ops.includes(op as ConditionOp)) return null
  const o = op as ConditionOp
  if (isValueFreeOp(o)) return { field, op: o, value: null }
  if (isMultiValueOp(o)) {
    if (!Array.isArray(value)) return null
    const ids = value.map(Number).filter((n) => Number.isFinite(n))
    if (ids.length !== value.length || ids.length === 0) return null
    return { field, op: o, value: ids }
  }
  if (def.kind === 'bool') return typeof value === 'boolean' ? { field, op: o, value } : null
  if (def.kind === 'number') return typeof value === 'number' && Number.isFinite(value) ? { field, op: o, value } : null
  const n = Number(value)
  return Number.isFinite(n) ? { field, op: o, value: n } : null
}

/** Dòng đã đủ giá trị chưa — dòng khai dở vẫn hiện nhưng không gửi lên. */
export function fullRow(row: ConditionRow, kind: ConditionValueKind = 'choice'): boolean {
  if (!row.field) return false
  if (isValueFreeOp(row.op)) return true
  if (isMultiValueOp(row.op)) return Array.isArray(row.value) && row.value.length > 0
  if (kind === 'bool') return typeof row.value === 'boolean'
  if (kind === 'number') return typeof row.value === 'number' && Number.isFinite(row.value)
  return Number(row.value) > 0
}

const kindOf = (fields: ConditionField[], name: string) => fields.find((f) => f.name === name)?.kind ?? 'choice'

/** Các dòng → chuỗi gửi backend. Không dòng nào đủ = chuỗi rỗng (không điều kiện). */
export function buildCondition(rows: ConditionRow[], fields: ConditionField[]): string {
  const usable = rows.filter((r) => fullRow(r, kindOf(fields, r.field)))
  if (usable.length === 0) return ''
  return JSON.stringify(usable.map((r) =>
    isValueFreeOp(r.op) ? { field: r.field, op: r.op } : { field: r.field, op: r.op, value: r.value }))
}

export function defaultConditionValue(op: ConditionOp, kind: ConditionValueKind = 'choice'): ConditionValue {
  if (isValueFreeOp(op)) return null
  if (isMultiValueOp(op)) return []
  if (kind === 'bool') return true
  if (kind === 'number') return null
  return 0
}

function describeRow(op: ConditionOp, label: string, v: string): string {
  switch (op) {
    case 'eq': return `${label} là ${v}`
    case 'ne': return `${label} không phải ${v}`
    case 'gt': return `${label} trên ${v}`
    case 'gte': return `${label} từ ${v} trở lên`
    case 'lt': return `${label} dưới ${v}`
    case 'lte': return `${label} từ ${v} trở xuống`
    case 'in': return `${label} thuộc ${v}`
    case 'not_in': return `${label} không thuộc ${v}`
    case 'empty': return `${label} để trống`
    case 'not_empty': return `${label} có giá trị`
  }
}

/** Câu tiếng Việt của cả điều kiện, nối bằng «và» — đúng cách backend đọc. */
export function conditionText(
  rows: ConditionRow[], fields: ConditionField[], getOptions: (f: ConditionField) => ConditionChoice[],
): string {
  return rows.map((row) => {
    const f = fields.find((x) => x.name === row.field)
    if (!f) return ''
    let v = ''
    if (isValueFreeOp(row.op)) v = ''
    else if (f.kind === 'bool') v = typeof row.value === 'boolean' ? (row.value ? 'Có' : 'Không') : ''
    else if (f.kind === 'number') v = typeof row.value === 'number' ? String(row.value) : ''
    else {
      const opts = getOptions(f)
      const ids = Array.isArray(row.value) ? row.value : typeof row.value === 'number' ? [row.value] : []
      v = ids.filter((id) => id > 0).map((id) => opts.find((o) => o.id === id)?.label ?? String(id)).join(', ')
    }
    return describeRow(row.op, f.label, v || '…')
  }).filter(Boolean).join(' và ')
}
