/**
 * Quy tắc nghiệp vụ của DÒNG khảo sát, tách hẳn khỏi React để test được và để
 * bảng, popup chi tiết và lúc lưu dùng chung MỘT bản luật.
 *
 * Bản v1 (`frontend/src/pages/SurveyDetail.tsx`) để lẫn những hàm này trong
 * component nên "thành tiền" ở bảng và "thành tiền" lúc gửi lên đã có lúc lệch
 * nhau. Sửa ở đây là sửa cho cả ba chỗ.
 */

import type { SurveyDetail, SurveyLine, SurveyTable } from '../types/survey-detail'
import {
  LINE_APPROVE_DEFAULT,
  MANAGER_KEYS,
  OPTIONAL_KEYS,
  sectionsOf,
} from '../types/survey-detail'

/**
 * Ô chỉ có ở giao diện, KHÔNG gửi lên backend:
 * - `supplier_available` không có cột DB, chỉ đổi kiểu ô NCC.
 * - `supplier_name` ở bảng SẢN PHẨM không có cột DB (xem ghi chú đầu
 *   `types/survey-detail.ts`) — nó được suy từ danh mục NCC.
 */
const UI_ONLY_KEYS: Record<SurveyTable, readonly string[]> = {
  supplier: ['supplier_available'],
  product: ['supplier_available', 'supplier_name'],
}

/**
 * Kiểu ô KHÔNG kiểm tra "còn trống" lúc gửi duyệt.
 *
 * `vat` nằm trong này: VAT 0% là con số hợp lệ và rất phổ biến, bắt buộc nó
 * khác rỗng thì mọi dòng hàng không chịu thuế đều không gửi được.
 */
const SKIP_REQUIRED_TYPES = new Set(['num', 'computed', 'vat', 'check', 'legal'])

function keysOf(table: SurveyTable): string[] {
  return sectionsOf(table).flatMap((section) => section.fields.map((field) => field.key))
}

/** Khóa được phép gửi lên backend, theo đúng schema Pydantic của từng bảng. */
function payloadKeysOf(table: SurveyTable): string[] {
  const uiOnly = UI_ONLY_KEYS[table]
  return keysOf(table).filter((key) => !uiOnly.includes(key))
}

/** Những ô là SỐ — nhận từ form dưới dạng chuỗi, phải ép kiểu trước khi gửi. */
export function numericKeysOf(table: SurveyTable): Set<string> {
  const fromSections = sectionsOf(table)
    .flatMap((section) => section.fields)
    .filter((field) => field.type === 'num' || field.type === 'computed' || field.type === 'vat')
    .map((field) => field.key)
  return new Set(fromSections)
}

/** Dòng trống của một bảng: đủ mọi khóa, đúng kiểu mặc định. */
export function makeEmptyLine(table: SurveyTable): SurveyLine {
  const line: SurveyLine = {}
  for (const section of sectionsOf(table)) {
    for (const field of section.fields) {
      if (field.key === 'line_approve') line[field.key] = LINE_APPROVE_DEFAULT
      else if (field.type === 'check') line[field.key] = false
      else if (field.type === 'num' || field.type === 'computed' || field.type === 'vat')
        line[field.key] = 0
      else line[field.key] = ''
    }
  }
  return line
}

export function toNumber(value: SurveyLine[string]): number {
  return Number(value) || 0
}

/** Thành tiền suy ra từ giá × MOQ × (1 + VAT). */
export function calcAmount(line: SurveyLine): number {
  return (
    toNumber(line.price_by_volume) * toNumber(line.moq) * (1 + toNumber(line.vat) / 100)
  )
}

/**
 * Thành tiền HIỂN THỊ. Ưu tiên số đã lưu: người dùng được phép gõ đè thành tiền
 * (báo giá trọn gói, chiết khấu…), tự tính đè lên là mất số họ nhập.
 */
export function rowAmount(line: SurveyLine): number {
  const saved = toNumber(line.amount)
  return saved > 0 ? saved : calcAmount(line)
}

/** Ô không tính là "người dùng có nhập gì" — dòng chỉ có mấy ô này vẫn là dòng rỗng. */
const CONTENT_IGNORED_KEYS = new Set<string>(['id', ...MANAGER_KEYS])

/**
 * Dòng có nội dung hay không. Dòng rỗng bị BỎ lúc lưu — bấm "Thêm nhiều" 5 dòng
 * rồi chỉ điền 2 thì không đẻ ra 3 dòng rác trong DB.
 */
export function lineHasContent(line: SurveyLine, table: SurveyTable): boolean {
  return keysOf(table).some((key) => {
    if (CONTENT_IGNORED_KEYS.has(key)) return false
    const value = line[key]
    if (typeof value === 'number') return value !== 0
    if (typeof value === 'boolean') return value
    return Boolean(value && String(value).trim())
  })
}

/** Một dòng đã sạch kiểu dữ liệu, sẵn sàng gửi lên backend. */
export function toPayloadLine(line: SurveyLine, table: SurveyTable): SurveyLine {
  const payload: SurveyLine = {}
  const numericKeys = numericKeysOf(table)

  for (const key of payloadKeysOf(table)) {
    payload[key] = numericKeys.has(key) ? toNumber(line[key]) : (line[key] ?? '')
  }
  if (typeof line.id === 'number' && line.id > 0) payload.id = line.id
  // Thành tiền phải chốt lại lúc gửi: người dùng có thể sửa giá/MOQ ở popup rồi
  // đóng luôn, ô tính sẵn ở bảng chưa kịp chạy.
  if (table === 'product') payload.amount = rowAmount(line)

  return payload
}

/** Các dòng có nội dung, đã ép kiểu — dùng cho cả tạo mới lẫn cập nhật. */
export function toPayloadLines(lines: SurveyLine[], table: SurveyTable): SurveyLine[] {
  return lines.filter((line) => lineHasContent(line, table)).map((line) => toPayloadLine(line, table))
}

const AMOUNT_INPUT_KEYS = new Set(['price_by_volume', 'moq', 'vat'])

/**
 * Sửa một ô của dòng. Đổi giá / MOQ / VAT thì tính lại thành tiền ngay, trừ khi
 * chính ô thành tiền đang được gõ đè.
 */
export function applyLineChange(line: SurveyLine, changes: Partial<SurveyLine>): SurveyLine {
  const next: SurveyLine = { ...line, ...changes }
  const touched = Object.keys(changes)
  if (!touched.includes('amount') && touched.some((key) => AMOUNT_INPUT_KEYS.has(key))) {
    next.amount = calcAmount(next)
  }
  return next
}

/**
 * CR-024 — chép sẵn từ đầu phiếu xuống dòng mới. Người khảo sát gõ lại y hệt
 * những gì vừa khai ở đầu phiếu là việc thừa và là nguồn lệch dữ liệu.
 */
export function prefillLineFromHeader(
  table: SurveyTable,
  header: Pick<
    SurveyDetail,
    'received_date' | 'result_due_date' | 'item_group' | 'item_code' | 'item_name' | 'uom'
  >,
): Partial<SurveyLine> {
  const common: Partial<SurveyLine> = {
    contact_date: header.received_date || '',
    result_date: header.result_due_date || '',
  }
  if (table === 'supplier') return { ...common, supply_group: header.item_group || '' }
  return {
    ...common,
    internal_code: header.item_code || '',
    product_name: header.item_name || '',
    quote_unit: header.uom || '',
    internal_unit: header.uom || '',
  }
}

/**
 * Ô NCC của dòng đang ở chế độ CHỌN TỪ DANH MỤC hay GÕ TAY.
 *
 * Cờ này không có trong DB nên phải suy lại mỗi lần mở phiếu: mã đang lưu mà
 * không khớp danh mục nghĩa là NCC chưa được tạo, phải giữ ô gõ tay. Bản v1 mặc
 * định luôn "có sẵn" nên tải lại phiếu là tên NCC gõ tay biến mất khỏi ô.
 *
 * `knownCodes` rỗng = danh mục CHƯA nạp xong, coi như có sẵn để tránh cả bảng
 * nhấp nháy sang chế độ gõ tay trong lúc chờ.
 */
export function isSupplierFromCatalog(line: SurveyLine, knownCodes: Set<string>): boolean {
  if (typeof line.supplier_available === 'boolean') return line.supplier_available
  const code = String(line.supplier_code ?? '').trim()
  if (!code || knownCodes.size === 0) return true
  return knownCodes.has(code)
}

/** Kết quả kiểm tra trước khi gửi duyệt. `invalid` chứa khóa ô để tô đỏ. */
export interface SurveyValidation {
  message: string
  /** Khóa dạng `${table}-${index}-${key}`. */
  invalid: Set<string>
}

const TABLE_SHORT_LABELS: Record<SurveyTable, string> = {
  supplier: 'Dòng NCC',
  product: 'Dòng SP',
}

function isRequiredKey(table: SurveyTable, key: string, line: SurveyLine): boolean {
  if (key === 'note') return false
  if ((MANAGER_KEYS as readonly string[]).includes(key)) return false
  if ((OPTIONAL_KEYS as readonly string[]).includes(key)) return false

  // Khối lấy mẫu chỉ bắt buộc khi dòng có đánh dấu "Mẫu sẵn".
  if (['sample_date', 'sample_qty', 'lab_result'].includes(key)) return line.sample_ready === true

  const field = sectionsOf(table)
    .flatMap((section) => section.fields)
    .find((item) => item.key === key)
  return !SKIP_REQUIRED_TYPES.has(field?.type ?? 'text')
}

function missingKeysOfLine(line: SurveyLine, table: SurveyTable): string[] {
  return keysOf(table).filter((key) => {
    if (!isRequiredKey(table, key, line)) return false
    return !String(line[key] ?? '').trim()
  })
}

/**
 * Kiểm tra trước khi GỬI DUYỆT. Lưu nháp thì không chạy hàm này — người khảo sát
 * phải lưu dở được, thông tin NCC nhiều khi phải đợi vài ngày mới đủ.
 */
export function validateSurveySubmit(
  header: SurveyDetail,
  supplierLines: SurveyLine[],
  productLines: SurveyLine[],
): SurveyValidation {
  const errors: string[] = []
  const invalid = new Set<string>()

  if (!header.item_group.trim()) errors.push('Chưa chọn Nhóm hàng')

  if (header.has_product_code) {
    if (!header.item_code.trim()) errors.push('Chưa chọn Mã hàng')
    if (Number(header.request_qty) <= 0) errors.push('Số lượng yêu cầu phải lớn hơn 0')
    if (!header.uom.trim()) errors.push('Chưa chọn ĐVT')
    if (Number(header.proposed_rate) <= 0) errors.push('Đơn giá đề xuất phải lớn hơn 0')
  } else if (!header.requirement_detail.trim()) {
    errors.push('Chưa nhập Chi tiết yêu cầu')
  }

  const filledSuppliers = supplierLines.filter((line) => lineHasContent(line, 'supplier'))
  const filledProducts = productLines.filter((line) => lineHasContent(line, 'product'))
  const hasSupplier = filledSuppliers.some((line) => String(line.supplier_code ?? '').trim())
  const hasProduct = filledProducts.some((line) => String(line.product_name ?? '').trim())

  if (!hasSupplier && !hasProduct) {
    errors.push('Phiếu phải có ít nhất một dòng NCC hoặc một dòng sản phẩm')
  }

  const incompleteLines: string[] = []
  for (const [table, lines] of [
    ['supplier', supplierLines],
    ['product', productLines],
  ] as [SurveyTable, SurveyLine[]][]) {
    lines.forEach((line, index) => {
      if (!lineHasContent(line, table)) return
      const missing = missingKeysOfLine(line, table)
      if (!missing.length) return
      incompleteLines.push(`${TABLE_SHORT_LABELS[table]} #${index + 1}`)
      missing.forEach((key) => invalid.add(`${table}-${index}-${key}`))
    })
  }

  if (incompleteLines.length) {
    errors.push(
      `${incompleteLines.join('; ')} còn thiếu thông tin bắt buộc — mở chi tiết dòng để điền các ô đang tô đỏ`,
    )
  }

  return { message: errors.join('. '), invalid }
}
