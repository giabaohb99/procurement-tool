/** Nhập ĐƠN GIÁ SAU VAT trên dòng hàng (YCMH, ĐMH) — duoc-CR-776.
 *
 *  Máy chủ KHÔNG đổi: vẫn chỉ nhận / lưu đơn giá TRƯỚC thuế (`price`, Numeric(18,4)) và VAT theo
 *  PHẦN TRĂM (8 = 8%). Ô "Đơn giá sau VAT" chỉ là cách nhập ở giao diện: gõ ô nào thì ô kia tự tính.
 *
 *  Công thức (một chỗ duy nhất, cả hai trang dùng chung):
 *   - sau VAT   = làm tròn 2 số lẻ của  trước thuế × (1 + VAT/100)   (khớp bao-CR-307 / delivery_service)
 *   - trước thuế = làm tròn 4 số lẻ của sau VAT / (1 + VAT/100)      (đúng độ chính xác cột `price`)
 *
 *  Giữ ô vừa gõ khi đổi VAT %: dòng mang hai trường CHỈ Ở GIAO DIỆN (không bao giờ gửi lên API,
 *  phải bóc bằng `stripVatPriceClientFields` trước khi dựng payload):
 *   - `_lastPriceField` = 'post' khi vừa gõ ô sau VAT, 'pre' khi vừa gõ ô trước thuế;
 *   - `_postVat`        = số sau VAT người dùng đã gõ (giữ nguyên chữ số họ gõ, không bị làm tròn ngược).
 *  Dòng mới nạp từ máy chủ không có hai trường này → coi như vừa gõ trước thuế (giữ trước thuế).
 */

export const PRE_VAT_DECIMALS = 4
export const POST_VAT_DECIMALS = 2

export type LastPriceField = 'pre' | 'post'

/** Phần giá của một dòng hàng mà helper đọc. */
export interface VatPriceLine {
  price?: unknown
  _postVat?: unknown
  _lastPriceField?: unknown
}

/** Làm tròn `d` số lẻ (cộng EPSILON để 1.005 không bị làm tròn xuống do sai số nhị phân). */
const roundTo = (n: number, d: number): number => {
  const f = 10 ** d
  return Math.round((n + Number.EPSILON) * f) / f
}

/** VAT rỗng / âm / không phải số → 0. Đơn vị phần trăm (8 = 8%). */
export function normalizeVat(vat: unknown): number {
  const n = Number(vat)
  return Number.isFinite(n) && n >= 0 ? n : 0
}

/** Giá hợp lệ = số hữu hạn không âm; rỗng / âm / chữ → null (để trống, không tính). */
function cleanPrice(value: unknown): number | null {
  if (value === null || value === undefined || value === '' || typeof value === 'boolean') return null
  const n = Number(value)
  return Number.isFinite(n) && n >= 0 ? n : null
}

/** Trước thuế → sau VAT (làm tròn 2 số lẻ). null nếu giá không hợp lệ. */
export function calcPostVatPrice(price: unknown, vat: unknown): number | null {
  const p = cleanPrice(price)
  if (p === null) return null
  // Nhân / chia theo (100 + VAT) chứ không theo 1,08: số rất lớn nhân 1,08 lệch đuôi — cùng cách với
  // frontend-v2 `vat-price.ts` để hai giao diện ra đúng từng số lẻ (duoc-CR-776).
  return roundTo((p * (100 + normalizeVat(vat))) / 100, POST_VAT_DECIMALS)
}

/** Sau VAT → trước thuế (làm tròn 4 số lẻ). null nếu giá không hợp lệ. */
export function calcPreVatPrice(postVatPrice: unknown, vat: unknown): number | null {
  const p = cleanPrice(postVatPrice)
  if (p === null) return null
  return roundTo((p * 100) / (100 + normalizeVat(vat)), PRE_VAT_DECIMALS)
}

/** Dòng đang "neo" theo số sau VAT người dùng gõ: vừa gõ sau VAT, số đó > 0 và còn khớp với
 *  `price` hiện tại. Kiểm khớp để nếu `price` bị chỗ khác ghi đè (điền từ lịch sử mua, đổi loại
 *  đơn…) thì cờ tự mất hiệu lực, không kéo giá cũ quay lại. */
function isPostVatAnchored(line: VatPriceLine, vat: unknown): boolean {
  if (line._lastPriceField !== 'post') return false
  const post = cleanPrice(line._postVat)
  if (post === null || post <= 0) return false
  return calcPreVatPrice(post, vat) === cleanPrice(line.price)
}

/** Số hiển thị ở ô "Đơn giá sau VAT": số người dùng vừa gõ nếu còn neo, ngược lại tính từ
 *  `price`. Trả 0 khi chưa có giá (ô NumberInput hiện trống với 0). */
export function getPostVatDisplay(line: VatPriceLine, vat: unknown): number {
  if (isPostVatAnchored(line, vat)) return Number(line._postVat)
  return calcPostVatPrice(line.price, vat) ?? 0
}

/** Mảnh cập nhật dòng khi người dùng gõ ô ĐƠN GIÁ (trước thuế). Giá trị không đổi (chỉ bấm vào rồi
 *  rời ô — NumberInput gọi onChange cả lúc blur) thì trả {} để không đổi "ô vừa gõ". */
export function patchOnPreVatEdit(
  line: VatPriceLine,
  price: number,
): { price?: number; _lastPriceField?: LastPriceField; _postVat?: undefined } {
  if (price === (cleanPrice(line.price) ?? 0)) return {}
  return { price, _lastPriceField: 'pre', _postVat: undefined }
}

/** Mảnh cập nhật dòng khi người dùng gõ ô ĐƠN GIÁ SAU VAT: tính ngược `price`. Gõ 0 / để trống
 *  thì xóa giá (price = 0) và bỏ neo. Số không đổi so với đang hiện (chỉ bấm vào rồi rời ô) thì
 *  trả {}: nếu không, mỗi lần Tab qua ô này đơn giá trước thuế bị tính lại từ số đã làm tròn 2 lẻ. */
export function patchOnPostVatEdit(
  line: VatPriceLine,
  postVatPrice: number,
  vat: unknown,
): { price?: number; _lastPriceField?: LastPriceField; _postVat?: number | undefined } {
  if (postVatPrice === getPostVatDisplay(line, vat)) return {}
  const pre = calcPreVatPrice(postVatPrice, vat)
  if (pre === null || !(postVatPrice > 0)) return { price: 0, _lastPriceField: 'pre', _postVat: undefined }
  return { price: pre, _lastPriceField: 'post', _postVat: postVatPrice }
}

/** Mảnh cập nhật `price` khi VAT % đổi từ `oldVat` sang `newVat`. Còn neo sau VAT → giữ sau VAT,
 *  tính lại trước thuế; ngược lại → {} (giữ nguyên trước thuế như trước CR-776). */
export function patchOnVatChange(line: VatPriceLine, oldVat: unknown, newVat: unknown): { price?: number } {
  if (!isPostVatAnchored(line, oldVat)) return {}
  const pre = calcPreVatPrice(line._postVat, newVat)
  return pre === null ? {} : { price: pre }
}

/** Bóc hai trường chỉ-ở-giao-diện khỏi dòng trước khi gửi lên API. */
export function stripVatPriceClientFields<T extends Record<string, any>>(line: T): Omit<T, '_postVat' | '_lastPriceField'> {
  const { _postVat, _lastPriceField, ...rest } = line
  void _postVat; void _lastPriceField
  return rest
}
