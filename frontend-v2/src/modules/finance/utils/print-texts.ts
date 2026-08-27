/**
 * CR-149 (main, ticket #14): câu tự động trên bản in YCTT — dùng để ĐIỀN SẴN
 * vào 3 ô "Nội dung bản in" ở màn chi tiết và làm câu rơi về khi người dùng
 * xóa trống. Phải khớp câu trang in tự dựng (CR-146) kẻo điền sẵn một đằng,
 * in một nẻo.
 */

interface AutoPrintTextInput {
  /** CR-146: 0 = thanh toán công nợ (mặc định) · 1 = thanh toán trước. */
  prepay?: number
  supplier_name?: string
  supplier_code?: string
  /** `yyyy-mm-dd` — lấy kỳ `mm/yyyy` từ 7 ký tự đầu. */
  request_date?: string
}

export function autoPrintText(req: AutoPrintTextInput): string {
  const supplier = req.supplier_name || req.supplier_code || ''
  const period = (req.request_date || '').slice(0, 7).split('-').reverse().join('/')
  const base = req.prepay
    ? `Thanh toán trước cho nhà cung cấp ${supplier}`
    : `Thanh toán công nợ ${supplier}`
  return period ? `${base} ${period}` : base
}
