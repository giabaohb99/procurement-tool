/**
 * ĐIỀU KIỆN RẼ NHÁNH của một bước — đọc/ghi giữa BỘ DỰNG và chuỗi JSON.
 *
 * Backend lưu điều kiện dạng JSON (`condition_service.py`) vì bộ máy duyệt phải
 * nhận được mọi loại chứng từ, kể cả loại chưa tồn tại lúc viết. Nhưng người
 * khai luồng là người làm nghiệp vụ: bắt họ gõ
 * `[{"field":"secrecy_level","op":"gte","value":3}]` là bắt học một cú pháp chỉ
 * dùng vài lần, mà gõ sai một dấu ngoặc thì `parse()` của backend **nuốt lặng**
 * — nhánh không bao giờ khớp và không có gì báo.
 *
 * Cùng lối với `flow-scope.ts` (điều kiện ở tầng luồng), chỉ khác là ở tầng
 * bước cần nhiều dòng: các dòng nối nhau bằng VÀ, giống backend.
 */

export type ConditionOp = 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'in' | 'not_in'

export const CONDITION_OPS: ConditionOp[] = [
  'eq',
  'ne',
  'gt',
  'gte',
  'lt',
  'lte',
  'in',
  'not_in',
]

/** Phép nhận NHIỀU giá trị — ô nhập là bộ chọn nhiều, không phải chọn một. */
const MULTI_OPS: ConditionOp[] = ['in', 'not_in']

export function laPhepNhieuGiaTri(op: ConditionOp): boolean {
  return MULTI_OPS.includes(op)
}

export interface ConditionRow {
  field: string
  op: ConditionOp
  /** Một số (eq/gte/…) hoặc danh sách số (in/not_in). */
  value: number | number[]
}

export interface ParsedCondition {
  rows: ConditionRow[]
  /**
   * `true` = chuỗi đang lưu **vượt ngoài** thứ bộ dựng diễn tả được (gõ tay từ
   * bản cũ, ô lạ, giá trị chuỗi…). Khi đó màn hình phải hiện nguyên văn và
   * KHÔNG được lặng lẽ ghi đè — người khai trước có thể đã viết đúng.
   */
  advanced: boolean
}

/**
 * Chuỗi điều kiện → các dòng của bộ dựng.
 *
 * `laOHopLe` do tầng gọi cấp (danh mục ô của loại chứng từ đó): ô lạ nghĩa là
 * điều kiện này viết cho thứ bộ dựng không biết, phải xếp vào «khai tay».
 */
export function parseCondition(
  raw: string,
  laOHopLe: (field: string) => boolean,
): ParsedCondition {
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
    const row = docMotDong(item, laOHopLe)
    if (row === null) return { rows: [], advanced: true }
    rows.push(row)
  }
  return { rows, advanced: false }
}

function docMotDong(item: unknown, laOHopLe: (field: string) => boolean): ConditionRow | null {
  if (typeof item !== 'object' || item === null) return null

  const { field, op, value } = item as { field?: unknown; op?: unknown; value?: unknown }
  if (typeof field !== 'string' || !laOHopLe(field)) return null
  if (typeof op !== 'string' || !CONDITION_OPS.includes(op as ConditionOp)) return null

  const phep = op as ConditionOp
  if (laPhepNhieuGiaTri(phep)) {
    if (!Array.isArray(value)) return null
    const ids = value.map(Number).filter((so) => Number.isFinite(so))
    //  Danh sách rỗng là điều kiện KHÔNG BAO GIỜ khớp — giữ nguyên chuỗi cũ
    //  thay vì hiện một dòng trống trông như chưa khai gì.
    if (ids.length !== value.length || ids.length === 0) return null
    return { field, op: phep, value: ids }
  }

  const so = Number(value)
  if (!Number.isFinite(so)) return null
  return { field, op: phep, value: so }
}

/**
 * Dòng đã chọn đủ giá trị chưa. Dòng chưa đủ vẫn hiện trên màn hình (người
 * dùng đang khai dở) nhưng KHÔNG được gửi xuống backend.
 */
export function dongDayDu(row: ConditionRow): boolean {
  if (!row.field) return false
  //  Mọi giá trị ở đây là id danh mục hoặc mức trong thang — đều bắt đầu từ 1.
  //  `0` là "chưa chọn", gửi xuống thành điều kiện không phiếu nào khớp.
  return laPhepNhieuGiaTri(row.op) ? toArray(row.value).length > 0 : Number(row.value) > 0
}

/** Các dòng của bộ dựng → chuỗi gửi lên backend. Không dòng nào = luôn chạy. */
export function buildCondition(rows: ConditionRow[]): string {
  const dungDuoc = rows.filter(dongDayDu)
  if (dungDuoc.length === 0) return ''
  return JSON.stringify(dungDuoc)
}

export function toArray(value: number | number[]): number[] {
  return Array.isArray(value) ? value : [value]
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
  }
}

/** Nhãn ngắn của phép, dùng cho ô chọn trong bộ dựng. */
export const OP_LABELS: Record<ConditionOp, string> = {
  eq: 'là',
  ne: 'không phải',
  gt: 'trên',
  gte: 'từ ... trở lên',
  lt: 'dưới',
  lte: 'từ ... trở xuống',
  in: 'thuộc',
  not_in: 'không thuộc',
}
