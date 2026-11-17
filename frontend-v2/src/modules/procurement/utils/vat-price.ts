/**
 * duoc-CR-776 — nhập ĐƠN GIÁ SAU VAT trên dòng YCMH / ĐMH, tự tính ngược đơn giá trước thuế.
 *
 * Máy chủ chỉ lưu `price` (trước thuế, Numeric(18,4)) và VAT dạng PHẦN TRĂM (8 = 8%). Ô sau VAT
 * chỉ là một cách nhập ở giao diện: số người dùng gõ giữ ở bản nháp dòng trong trường
 * `price_after_vat_input`, KHÔNG gửi lên máy chủ, tải lại trang là mất.
 *
 * Công thức (một nơi duy nhất cho cả hai chứng từ):
 * - sau VAT = làm tròn 2 số lẻ của `price × (1 + vat/100)` — khớp cột cũ bao-CR-307;
 * - trước thuế = làm tròn 4 số lẻ của `sau VAT / (1 + vat/100)` — đúng độ chính xác cột `price`.
 */

/** Giá trị ô giá / ô VAT có thể nhận: số, chuỗi người gõ, hoặc rỗng. */
type NumberLike = number | string | null | undefined

/** Đọc một giá trị thành số hữu hạn; rỗng / chữ / vô cực trả `null`. */
function toFiniteNumber(value: NumberLike): number | null {
  if (value === null || value === undefined) return null
  if (typeof value === 'string' && value.trim() === '') return null
  const num = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(num) ? num : null
}

/**
 * Làm tròn `decimals` số lẻ. Số quá lớn (nhân lên vượt trần số nguyên an toàn của JS) thì số
 * thực đã không còn chỗ cho phần lẻ — trả nguyên giá trị, đừng làm tròn ra một số sai bậc.
 */
function roundTo(value: number, decimals: number): number {
  const factor = 10 ** decimals
  const scaled = value * factor
  if (Math.abs(scaled) > Number.MAX_SAFE_INTEGER) return value
  return Math.round(scaled) / factor
}

/** VAT phần trăm dùng để tính: rỗng / âm / không phải số coi như 0. */
export function normalizeVatPercent(vat: NumberLike): number {
  const num = toFiniteNumber(vat)
  return num === null || num < 0 ? 0 : num
}

/** Đơn giá hợp lệ để tính: rỗng / âm / không phải số trả `null` (không tính gì). */
function toUnitPrice(value: NumberLike): number | null {
  const num = toFiniteNumber(value)
  return num === null || num < 0 ? null : num
}

/** Đơn giá sau VAT, làm tròn 2 số lẻ. Giá không hợp lệ trả `null`. */
export function computePriceAfterVat(price: NumberLike, vat: NumberLike): number | null {
  const base = toUnitPrice(price)
  if (base === null) return null
  //  Nhân / chia theo (100 + vat) thay vì (1 + vat/100): 1,08 không biểu diễn đúng ở dạng nhị
  //  phân, đi đường số nguyên đỡ lệch đuôi ở số lớn (1.080 tỷ / 1,08 ra 999.999.999.999,9998).
  const result = roundTo((base * (100 + normalizeVatPercent(vat))) / 100, 2)
  return Number.isFinite(result) ? result : null
}

/** Đơn giá trước thuế tính ngược từ giá sau VAT, làm tròn 4 số lẻ. Giá không hợp lệ trả `null`. */
export function computePriceBeforeVat(priceAfterVat: NumberLike, vat: NumberLike): number | null {
  const gross = toUnitPrice(priceAfterVat)
  if (gross === null) return null
  const result = roundTo((gross * 100) / (100 + normalizeVatPercent(vat)), 4)
  return Number.isFinite(result) ? result : null
}

/**
 * Phần nháp dòng mà cụm hàm này đọc / ghi. `price_after_vat_input` có mặt nghĩa là ô người
 * dùng gõ GẦN NHẤT trên dòng là ô sau VAT; vắng mặt là ô trước thuế (hoặc dòng vừa nạp).
 */
export interface VatPriceLineDraft {
  price: number
  price_after_vat_input?: number
}

/** Phần thay đổi trả về để trang trộn vào dòng (`{ ...line, ...patch }`). */
export interface VatPricePatch {
  price: number
  price_after_vat_input: number | undefined
}

/**
 * Số sau VAT người dùng gõ còn KHỚP với đơn giá đang có không. Chỗ khác đổi `price` mà không
 * xóa số đã gõ (điền từ lịch sử mua hàng, điền giá hàng loạt…) thì số gõ cũ hết giá trị —
 * bỏ qua nó thay vì hiện một con số lệch với đơn giá thật.
 */
function typedPriceAfterVat(line: VatPriceLineDraft, vat: NumberLike): number | null {
  const typed = line.price_after_vat_input
  if (typed === undefined) return null
  const expected = computePriceBeforeVat(typed, vat)
  if (expected === null) return null
  return Math.abs(expected - (Number(line.price) || 0)) < 1e-9 ? typed : null
}

/** Đơn giá sau VAT đang hiện trên dòng: số vừa gõ nếu còn khớp, không thì tính từ đơn giá. */
export function resolveLinePriceAfterVat(line: VatPriceLineDraft, vat: NumberLike): number {
  return typedPriceAfterVat(line, vat) ?? computePriceAfterVat(line.price, vat) ?? 0
}

/** Gõ vào ô ĐƠN GIÁ (trước thuế): ô này thành ô gõ gần nhất, bỏ số sau VAT đã gõ. */
export function applyPriceBeforeVatInput(price: number): VatPricePatch {
  return { price: toUnitPrice(price) ?? 0, price_after_vat_input: undefined }
}

/** Gõ vào ô ĐƠN GIÁ SAU VAT: tính ngược đơn giá trước thuế, giữ số vừa gõ để hiện đúng. */
export function applyPriceAfterVatInput(priceAfterVat: number, vat: NumberLike): VatPricePatch {
  const price = computePriceBeforeVat(priceAfterVat, vat)
  if (price === null) return { price: 0, price_after_vat_input: undefined }
  return { price, price_after_vat_input: priceAfterVat }
}

/**
 * Đổi VAT % của dòng: giữ ô gõ gần nhất. Vừa gõ sau VAT (và số đó còn khớp với VAT cũ) thì giữ
 * sau VAT, tính lại trước thuế theo VAT mới; còn lại giữ nguyên đơn giá trước thuế như trước nay.
 */
export function repriceOnVatChange(
  line: VatPriceLineDraft,
  previousVat: NumberLike,
  nextVat: NumberLike,
): VatPricePatch {
  const typed = typedPriceAfterVat(line, previousVat)
  if (typed === null) {
    return { price: Number(line.price) || 0, price_after_vat_input: undefined }
  }
  return applyPriceAfterVatInput(typed, nextVat)
}

/** Bỏ trường chỉ-ở-giao-diện trước khi gửi dòng lên máy chủ. */
export function stripPriceAfterVatInput<T extends { price_after_vat_input?: number }>(
  line: T,
): Omit<T, 'price_after_vat_input'> {
  const { price_after_vat_input: _dropped, ...rest } = line
  return rest
}
