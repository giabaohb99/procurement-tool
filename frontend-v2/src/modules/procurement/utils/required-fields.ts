/**
 * Trường BẮT BUỘC của ba loại chứng từ mua hàng (YCMH · YCBG · ĐMH).
 *
 * Một nguồn duy nhất cho hai thứ vốn hay lệch nhau: dấu sao đỏ vẽ trên màn và
 * câu chặn lúc bấm Gửi duyệt. Đổi luật thì đổi ở ĐÂY, đừng rải `if` vào trang.
 *
 * Ba luật nền:
 *
 * 1. **Chặn ở GỬI DUYỆT, không chặn ở LƯU.** Phiếu nháp cho phép cất dở — bắt đủ
 *    ngay từ nút Lưu thì người lập không ghi tạm được nửa chừng. Riêng vài ô đầu
 *    phiếu (công ty, người yêu cầu…) vẫn chặn ngay khi Lưu vì thiếu chúng thì
 *    backend không dựng nổi bản ghi.
 * 2. **Nêu đích danh dòng nào thiếu ô nào.** Báo "còn thiếu thông tin" thì người
 *    lập phải mở lần lượt từng dòng để dò.
 * 3. **ĐMH bám sát backend.** Danh sách dưới đây là bản sao của
 *    `TRUONG_BAT_BUOC_DONG` trong `backend/app/modules/purchase_order/service.py`
 *    (CR-095). Kiểm ở đây chỉ để báo lỗi sớm và tử tế hơn — backend vẫn là chốt
 *    thật. Sửa một bên thì phải sửa bên kia, kẻo màn cho bấm rồi API mới chặn.
 *    VAT CỐ Ý không nằm trong danh sách: 0 vừa nghĩa "chưa nhập" vừa nghĩa
 *    "hàng không chịu thuế", bắt buộc là chặn oan hàng 0%.
 */

import type {
  PurchaseOrderDetail,
  PurchaseOrderItem,
} from '../types/purchase-order-detail'
import type {
  PurchaseRequestDetail,
  PurchaseRequestItem,
} from '../types/purchase-request-detail'
import type {
  SurveyRequestDetail,
  SurveyRequestLine,
} from '../types/survey-request-detail'

/** Một ô bắt buộc trên DÒNG chứng từ. `label` chính là nhãn người dùng thấy. */
interface RequiredLineField<T> {
  label: string
  filled: (line: T) => boolean
}

const hasText = (value: string | undefined | null) => !!String(value ?? '').trim()
const isPositive = (value: number | undefined | null) => (Number(value) || 0) > 0

function missingFields<T>(line: T, fields: RequiredLineField<T>[]): string[] {
  return fields.filter((field) => !field.filled(line)).map((field) => field.label)
}

/* ------------------------------------------------------------------ YCMH -- */

/**
 * Dòng sản phẩm của YCMH. Backend KHÔNG chặn gì ở `submit_pr`, nên luật thật sự
 * nằm ở đây — giữ đúng bộ bốn ô của bản `frontend` đang chạy.
 */
export const PURCHASE_REQUEST_LINE_REQUIRED: RequiredLineField<PurchaseRequestItem>[] = [
  { label: 'Mã hàng', filled: (line) => hasText(line.product_code) },
  { label: 'Số lượng mua', filled: (line) => isPositive(line.qty) },
  { label: 'Kho nhận', filled: (line) => hasText(line.warehouse) },
  { label: 'Ngày cần hàng', filled: (line) => hasText(line.required_date) },
]

export function missingPurchaseRequestLineFields(line: PurchaseRequestItem): string[] {
  return missingFields(line, PURCHASE_REQUEST_LINE_REQUIRED)
}

/** Dòng có tên sản phẩm mới được tính — dòng trống là dòng người dùng bỏ dở. */
function purchaseRequestLines(data: PurchaseRequestDetail): PurchaseRequestItem[] {
  return data.items.filter((item) => hasText(item.product_name))
}

/**
 * Trả về câu báo lỗi đầu tiên, chuỗi rỗng nếu hợp lệ.
 * `forSubmit` = đang gửi duyệt, khi đó kiểm thêm từng dòng.
 */
export function validatePurchaseRequest(
  data: PurchaseRequestDetail,
  forSubmit = false,
): string {
  if (!data.company_id) return 'Vui lòng chọn Công ty'
  if (!data.requester) return 'Vui lòng chọn Nhân sự yêu cầu'

  const lines = purchaseRequestLines(data)
  if (!lines.length) return 'Cần ít nhất một sản phẩm'

  // Trùng mã kiểm CẢ LÚC LƯU: dòng YCMH nối sang ĐMH bằng mã hàng, để lọt hai
  // dòng cùng mã là tiến độ số lượng của cả hai phiếu sai. Backend cũng chặn,
  // nhưng ở đây nói rõ được mã nào.
  const duplicated = duplicateCodes(lines.map((line) => line.product_code))
  if (duplicated.length) {
    return `Mã hàng bị trùng: ${duplicated.join(', ')}. Mỗi mã chỉ được một dòng — gộp số lượng vào một dòng hoặc đổi mã.`
  }

  if (!forSubmit) return ''

  for (const line of lines) {
    const missing = missingPurchaseRequestLineFields(line)
    if (missing.length) {
      return `Sản phẩm "${line.product_name}" còn thiếu: ${missing.join(', ')}.`
    }
  }
  return ''
}

/* ------------------------------------------------------------------ YCBG -- */

/**
 * Dòng cần khảo sát. Trước đây màn v2 nhận "Phân loại HOẶC Chi tiết thông số",
 * nhưng bản đang chạy đánh sao đỏ ở Phân loại — khách chốt lấy luật CHẶT: thiếu
 * Phân loại là không gửi duyệt được, vì phân loại quyết định thời gian chuẩn để
 * tính ngày trả kết quả.
 */
export const SURVEY_REQUEST_LINE_REQUIRED: RequiredLineField<SurveyRequestLine>[] = [
  { label: 'Phân loại', filled: (line) => hasText(line.item_group) },
]

export function missingSurveyRequestLineFields(line: SurveyRequestLine): string[] {
  return missingFields(line, SURVEY_REQUEST_LINE_REQUIRED)
}

export function validateSurveyRequest(
  data: SurveyRequestDetail,
  forSubmit = false,
): string {
  if (!data.company_id) return 'Vui lòng chọn Công ty'
  if (!data.requester) return 'Vui lòng nhập Người yêu cầu'
  if (!hasText(data.purpose)) return 'Vui lòng nhập Mục đích khảo sát'
  if (!data.lines.length) return 'Cần ít nhất 1 dòng sản phẩm cần khảo sát'

  if (!forSubmit) return ''

  for (const [index, line] of data.lines.entries()) {
    const missing = missingSurveyRequestLineFields(line)
    if (missing.length) return `Dòng ${index + 1} còn thiếu: ${missing.join(', ')}.`
  }
  return ''
}

/**
 * Tập khóa các ô đang thiếu — để trang KHOANH ĐỎ đúng chỗ thay vì chỉ toast
 * (QA 29/08). Cùng luật với `validateSurveyRequest`, sửa một bên phải sửa bên
 * kia. Khóa đầu phiếu là tên trường; khóa dòng là `line-${index}-${field}`.
 */
export function invalidSurveyRequestKeys(
  data: SurveyRequestDetail,
  forSubmit = false,
): Set<string> {
  const invalid = new Set<string>()
  if (!data.company_id) invalid.add('company_id')
  if (!data.requester) invalid.add('requester')
  if (!hasText(data.purpose)) invalid.add('purpose')

  if (!forSubmit) return invalid

  for (const [index, line] of data.lines.entries()) {
    if (missingSurveyRequestLineFields(line).length) invalid.add(`line-${index}-item_group`)
  }
  return invalid
}

/* ------------------------------------------------------------------- ĐMH -- */

/**
 * Bản sao `TRUONG_BAT_BUOC_DONG` của backend, GIỮ NGUYÊN thứ tự và nhãn để câu
 * báo lỗi của hai bên đọc giống nhau.
 */
export const PURCHASE_ORDER_LINE_REQUIRED: RequiredLineField<PurchaseOrderItem>[] = [
  { label: 'Mã hàng', filled: (line) => hasText(line.product_code) },
  { label: 'Phân loại', filled: (line) => hasText(line.item_group) },
  { label: 'Tên hàng', filled: (line) => hasText(line.product_name) },
  { label: 'Tên trên hóa đơn', filled: (line) => hasText(line.invoice_name) },
  { label: 'Ngày yêu cầu có hàng', filled: (line) => hasText(line.required_date) },
  { label: 'Ngày dự kiến có hàng', filled: (line) => hasText(line.expected_date) },
  { label: 'ĐVT', filled: (line) => hasText(line.unit) },
  { label: 'Kho nhận mặc định', filled: (line) => hasText(line.warehouse_code) },
  { label: 'SL yêu cầu', filled: (line) => isPositive(line.qty_request) },
  { label: 'SL đặt NCC', filled: (line) => isPositive(line.qty_order) },
  { label: 'Đơn giá', filled: (line) => isPositive(line.price) },
]

export function missingPurchaseOrderLineFields(line: PurchaseOrderItem): string[] {
  return missingFields(line, PURCHASE_ORDER_LINE_REQUIRED)
}

/** Dòng thật sự được gửi lên — khớp bộ lọc của `toPurchaseOrderPayload`. */
function purchaseOrderLines(data: PurchaseOrderDetail): PurchaseOrderItem[] {
  return data.items.filter((item) => hasText(item.product_name) || hasText(item.product_code))
}

export function validatePurchaseOrder(data: PurchaseOrderDetail, forSubmit = false): string {
  if (!data.company_id) return 'Vui lòng chọn Công ty nhận hóa đơn'
  if (!data.supplier_code) return 'Vui lòng chọn Nhà cung cấp bán hàng'

  const lines = purchaseOrderLines(data)
  if (!lines.length) return 'Cần ít nhất một dòng hàng'

  // Mỗi mã hàng CHỈ một dòng: dòng ĐMH nối về dòng YCMH bằng mã, trùng mã là
  // tiến độ số lượng của cả hai phiếu sai.
  const duplicated = duplicateCodes(lines.map((line) => line.product_code))
  if (duplicated.length) {
    return `Mã hàng bị trùng: ${duplicated.join(', ')}. Mỗi mã chỉ được một dòng.`
  }

  if (!forSubmit) return ''

  // Gộp mọi dòng thiếu vào MỘT câu, giống hệt `submit_po` của backend: sửa xong
  // dòng 1 lại bị chặn ở dòng 2 thì người lập tưởng màn hình hỏng.
  const problems = lines
    .map((line, index) => ({ index, line, missing: missingPurchaseOrderLineFields(line) }))
    .filter((entry) => entry.missing.length)
    .map(
      ({ index, line, missing }) =>
        `dòng ${index + 1} (${line.product_code.trim() || 'chưa có mã hàng'}): ${missing.join(', ')}`,
    )
  if (problems.length) return `Chưa gửi duyệt được — còn thiếu ${problems.join('; ')}.`
  return ''
}

/* ----------------------------------------------------------------- chung -- */

/** Các mã xuất hiện từ hai lần trở lên; bỏ qua dòng chưa có mã. */
function duplicateCodes(codes: string[]): string[] {
  const seen = new Set<string>()
  const duplicated = new Set<string>()
  for (const raw of codes) {
    const code = String(raw ?? '').trim()
    if (!code) continue
    if (seen.has(code)) duplicated.add(code)
    seen.add(code)
  }
  return [...duplicated]
}
