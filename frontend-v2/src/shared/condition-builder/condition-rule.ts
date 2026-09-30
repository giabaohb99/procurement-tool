/**
 * ĐIỀU KIỆN kiểu bộ máy duyệt — đọc/ghi giữa BỘ CHỌN ĐIỀU KIỆN và chuỗi JSON.
 *
 * Backend lưu điều kiện dạng JSON (`approval/condition_service.py`):
 * `[{"field":"secrecy_level","op":"gte","value":3}]`, các dòng nối nhau bằng VÀ.
 * Người khai là người làm nghiệp vụ: bắt họ gõ chuỗi đó là bắt học một cú pháp
 * chỉ dùng vài lần, mà gõ sai một dấu ngoặc thì `parse()` của backend **nuốt
 * lặng** — điều kiện không bao giờ khớp và không có gì báo.
 *
 * Nâng từ `modules/approval/helpers/node-condition.ts` lên `shared/` ở
 * bao-CR-528 vì màn Cấu hình hệ thống cũng cần đúng bộ chọn này (ô «Điều kiện
 * bỏ qua điều phối» của YCMH). Bản nâng thêm ba thứ bộ máy duyệt văn bản chưa
 * dùng: hai phép KHÔNG cần giá trị (`empty` · `not_empty`), ô SỐ nhập tay và ô
 * CÓ/KHÔNG. Bộ ô của văn bản không khai chúng nên màn luồng duyệt vẫn y như cũ.
 */

/**
 * Phép so bộ chọn diễn tả được. Backend còn `contains` (so chuỗi) — cố ý chưa
 * đưa vào vì chưa ô nào cần; điều kiện dùng nó sẽ rơi vào «khai tay».
 */
export type ConditionOp =
  | 'eq'
  | 'ne'
  | 'gt'
  | 'gte'
  | 'lt'
  | 'lte'
  | 'in'
  | 'not_in'
  | 'empty'
  | 'not_empty'

/** Phép nhận NHIỀU giá trị — ô nhập là bộ chọn nhiều, không phải chọn một. */
const MULTI_OPS: ConditionOp[] = ['in', 'not_in']
/** Phép không cần giá trị: dòng chỉ có «trường · phép». */
const VALUE_FREE_OPS: ConditionOp[] = ['empty', 'not_empty']

export function isMultiValueOp(op: ConditionOp): boolean {
  return MULTI_OPS.includes(op)
}

export function isValueFreeOp(op: ConditionOp): boolean {
  return VALUE_FREE_OPS.includes(op)
}

/**
 * Giá trị của ô nhập theo kiểu nào.
 * - `choice` (mặc định): chọn từ danh mục — id hoặc mức trong thang, đều từ 1
 *   trở lên, nên `0` nghĩa là «chưa chọn».
 * - `number`: số nhập tay (số dòng hàng…). `0` là giá trị THẬT, «chưa nhập» là `null`.
 * - `bool`: có / không. Lưu `true`/`false` của JSON — backend so bằng chuỗi,
 *   `str(False)` là `"False"`, nên lưu `0` thì không bao giờ khớp.
 */
export type ConditionValueKind = 'choice' | 'number' | 'bool'

export type ConditionValue = number | number[] | boolean | null

export interface ConditionRow {
  field: string
  op: ConditionOp
  value: ConditionValue
}

/** Một ô đem ra so được. Tầng gọi mở rộng thêm nguồn dữ liệu của riêng nó. */
export interface ConditionField {
  /** Phải khớp KHÓA trong bối cảnh phiếu backend đưa vào điều kiện. */
  name: string
  label: string
  /** Chỉ bày những phép có nghĩa với ô này — bày đủ mọi phép là bày cả phép sai. */
  ops: ConditionOp[]
  kind?: ConditionValueKind
  hint?: string
}

/** Một lựa chọn của ô danh mục. `id` ghim là SỐ: điều kiện lưu mảng id số. */
export interface ConditionChoice {
  id: number
  label: string
  hint?: string
}

export interface ParsedCondition {
  rows: ConditionRow[]
  /**
   * `true` = chuỗi đang lưu **vượt ngoài** thứ bộ chọn diễn tả được (gõ tay từ
   * bản cũ, ô lạ, phép lạ, giá trị sai kiểu…). Khi đó màn hình phải hiện nguyên
   * văn và KHÔNG được lặng lẽ ghi đè — người khai trước có thể đã viết đúng.
   */
  advanced: boolean
}

function kindOf(field: ConditionField | undefined): ConditionValueKind {
  return field?.kind ?? 'choice'
}

/**
 * Chuỗi điều kiện → các dòng của bộ chọn.
 *
 * `fields` là danh mục ô của đúng ngữ cảnh đó: ô lạ, hoặc phép mà ô đó không
 * bày, nghĩa là điều kiện này viết cho thứ bộ chọn không biết — xếp vào «khai tay».
 */
export function parseCondition(raw: string, fields: ConditionField[]): ParsedCondition {
  if (!(raw || '').trim()) return { rows: [], advanced: false }

  let data: unknown
  try {
    data = JSON.parse(raw)
  } catch {
    return { rows: [], advanced: true }
  }
  if (!Array.isArray(data) || data.length === 0) return { rows: [], advanced: true }

  const rows: ConditionRow[] = []
  for (const item of data) {
    const row = readRow(item, fields)
    if (row === null) return { rows: [], advanced: true }
    rows.push(row)
  }
  return { rows, advanced: false }
}

function readRow(item: unknown, fields: ConditionField[]): ConditionRow | null {
  if (typeof item !== 'object' || item === null) return null

  const { field, op, value } = item as { field?: unknown; op?: unknown; value?: unknown }
  const def = fields.find((candidate) => candidate.name === field)
  if (typeof field !== 'string' || !def) return null
  if (typeof op !== 'string' || !def.ops.includes(op as ConditionOp)) return null

  const phep = op as ConditionOp
  if (isValueFreeOp(phep)) return { field, op: phep, value: null }

  if (isMultiValueOp(phep)) {
    if (!Array.isArray(value)) return null
    const ids = value.map(Number).filter((so) => Number.isFinite(so))
    //  Danh sách rỗng là điều kiện KHÔNG BAO GIỜ khớp — giữ nguyên chuỗi cũ
    //  thay vì hiện một dòng trống trông như chưa khai gì.
    if (ids.length !== value.length || ids.length === 0) return null
    return { field, op: phep, value: ids }
  }

  const kind = kindOf(def)
  if (kind === 'bool') return typeof value === 'boolean' ? { field, op: phep, value } : null
  if (kind === 'number') {
    return typeof value === 'number' && Number.isFinite(value) ? { field, op: phep, value } : null
  }

  const so = Number(value)
  if (!Number.isFinite(so)) return null
  return { field, op: phep, value: so }
}

/**
 * Dòng đã chọn đủ giá trị chưa. Dòng chưa đủ vẫn hiện trên màn hình (người
 * dùng đang khai dở) nhưng KHÔNG được gửi xuống backend.
 */
export function fullRow(row: ConditionRow, kind: ConditionValueKind = 'choice'): boolean {
  if (!row.field) return false
  if (isValueFreeOp(row.op)) return true
  if (isMultiValueOp(row.op)) return toArray(row.value).length > 0
  if (kind === 'bool') return typeof row.value === 'boolean'
  if (kind === 'number') return typeof row.value === 'number' && Number.isFinite(row.value)
  //  Id danh mục và mức trong thang đều bắt đầu từ 1. `0` là "chưa chọn", gửi
  //  xuống thành điều kiện không phiếu nào khớp.
  return Number(row.value) > 0
}

/**
 * Các dòng của bộ chọn → chuỗi gửi lên backend. Không dòng nào = chuỗi rỗng.
 *
 * `fields` cho biết kiểu giá trị của từng ô; bỏ trống thì coi mọi ô là danh mục
 * (đúng như bộ ô của luồng duyệt văn bản).
 */
export function buildCondition(rows: ConditionRow[], fields: ConditionField[] = []): string {
  const usable = rows.filter((row) =>
    fullRow(row, kindOf(fields.find((field) => field.name === row.field))),
  )
  if (usable.length === 0) return ''
  return JSON.stringify(
    usable.map((row) =>
      //  Phép không cần giá trị thì không gửi khóa `value` — gửi `null` trông như
      //  một điều kiện "bằng rỗng" khi ai đó đọc tay chuỗi dưới DB.
      isValueFreeOp(row.op)
        ? { field: row.field, op: row.op }
        : { field: row.field, op: row.op, value: row.value },
    ),
  )
}

export function toArray(value: ConditionValue): number[] {
  if (Array.isArray(value)) return value
  return typeof value === 'number' ? [value] : []
}

/** Giá trị khởi đầu của một dòng khi vừa chọn ô hoặc đổi phép. */
export function defaultConditionValue(
  op: ConditionOp,
  kind: ConditionValueKind = 'choice',
): ConditionValue {
  if (isValueFreeOp(op)) return null
  if (isMultiValueOp(op)) return []
  if (kind === 'bool') return true
  if (kind === 'number') return null
  return 0
}

/**
 * Một dòng → câu tiếng Việt đọc trôi.
 *
 * Không ghép kiểu `"<ô> <nhãn phép> <giá trị>"`: "Mức mật từ trở lên Mật" là
 * câu không ai đọc được. Mỗi phép có khuôn riêng.
 */
export function describeRow(op: ConditionOp, fieldLabel: string, valueText: string): string {
  switch (op) {
    case 'eq':
      return `${fieldLabel} là ${valueText}`
    case 'ne':
      return `${fieldLabel} không phải ${valueText}`
    case 'gt':
      return `${fieldLabel} trên ${valueText}`
    case 'gte':
      return `${fieldLabel} từ ${valueText} trở lên`
    case 'lt':
      return `${fieldLabel} dưới ${valueText}`
    case 'lte':
      return `${fieldLabel} từ ${valueText} trở xuống`
    case 'in':
      return `${fieldLabel} thuộc ${valueText}`
    case 'not_in':
      return `${fieldLabel} không thuộc ${valueText}`
    case 'empty':
      return `${fieldLabel} để trống`
    case 'not_empty':
      return `${fieldLabel} có giá trị`
  }
}

/** Nhãn ngắn của phép, dùng cho ô chọn trong bộ chọn. */
export const OP_LABELS: Record<ConditionOp, string> = {
  eq: 'là',
  ne: 'không phải',
  gt: 'trên',
  gte: 'từ ... trở lên',
  lt: 'dưới',
  lte: 'từ ... trở xuống',
  in: 'thuộc',
  not_in: 'không thuộc',
  empty: 'để trống',
  not_empty: 'có giá trị',
}
