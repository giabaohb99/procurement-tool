/**
 * Quy đổi GIÃN DÒNG kiểu Word sang `line-height` của CSS.
 *
 * Hai bên đếm khác nhau, đây là chỗ nhiều người tưởng nhầm:
 *
 * - CSS `line-height: 1.5` = 1,5 × CỠ CHỮ.
 * - Word "1.5 lines" = 1,5 × CHIỀU CAO MỘT DÒNG ĐƠN, mà dòng đơn lấy theo số đo
 *   của chính bộ phông (ascent + descent + lineGap), luôn CAO HƠN cỡ chữ.
 *
 * Times New Roman: (1825 + 443 + 87) / 2048 = 1,15 lần cỡ chữ. Nên cùng ghi
 * "giãn dòng 1,5" mà trang web lại chật hơn Word đúng 15% — nhìn ra ngay khi
 * đặt hai bản cạnh nhau, và đó là lý do có tệp này.
 *
 * Con số 1,15 gắn với Times New Roman — phông quy định của văn bản hành chính
 * (Nghị định 30/2020) và cũng là phông mặc định của `.doc-page`. Đoạn nào người
 * dùng đổi sang phông khác thì tỷ lệ thật hơi lệch (Calibri ~1,22), chấp nhận
 * xấp xỉ chứ không đo phông theo từng đoạn.
 */

/** Chiều cao một dòng đơn của Times New Roman, tính theo cỡ chữ. */
export const SINGLE_LINE_RATIO = 1.15

/** Giãn dòng mặc định của trang giấy — 1 dòng, khai ở `.doc-page` trong `index.css`. */
export const DEFAULT_LINE_SPACING = 1

/** Đổi số giãn dòng ghi trong Word (1 · 1,15 · 1,5 · 2) thành `line-height` CSS. */
export function wordLineSpacingToCss(lines: number): string {
  // Làm tròn 4 chữ số cho hết đuôi 1.7249999999999999 của số thực dấu phẩy động.
  return String(Number((lines * SINGLE_LINE_RATIO).toFixed(4)))
}

/**
 * Đọc ngược `line-height` của đoạn đang đứng ra số dòng kiểu Word.
 *
 * `null` khi đoạn không đặt giãn dòng riêng, hoặc khi giá trị là chiều cao tuyệt
 * đối (`18px` — Word gọi là "Exactly", tệp .docx nhập vào có thể mang theo):
 * không quy ra "mấy dòng" được nên thanh công cụ không tick nấc nào cả.
 */
export function cssToWordLineSpacing(value: string | null | undefined): number | null {
  if (!value) return null
  const parsed = Number(value)
  if (!Number.isFinite(parsed) || parsed <= 0) return null
  return Number((parsed / SINGLE_LINE_RATIO).toFixed(2))
}

/**
 * Đọc số người dùng gõ ở ô "Tùy chỉnh".
 *
 * Nhận cả dấu phẩy thập phân ("1,3") vì đó là cách gõ số của tiếng Việt.
 * `null` = gõ sai hoặc ngoài khoảng cho phép.
 */
export function parseLineSpacingInput(raw: string): number | null {
  const value = Number(raw.trim().replace(',', '.'))
  if (!Number.isFinite(value)) return null
  if (value < MIN_LINE_SPACING || value > MAX_LINE_SPACING) return null
  return value
}

/** Khoảng cho phép của ô tùy chỉnh — bằng Word: hẹp nhất 0,5 dòng, rộng nhất 10. */
export const MIN_LINE_SPACING = 0.5
export const MAX_LINE_SPACING = 10
