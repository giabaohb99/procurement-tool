/**
 * CR-264 — hợp đồng URL giữa trợ lý AI và form tạo YCTT: nút "Tạo đề nghị thanh toán"
 * mở `?payables=<ids>&offsets=<payableId>:<số tiền>,...` để form điền sẵn cột "Cấn trừ
 * trả trước" theo đề xuất FIFO của tool `draft_payment_request`.
 *
 * Số trên URL chỉ là ĐỀ XUẤT: form kẹp lại không vượt nợ còn lại (khoản nợ có thể đã
 * đổi giữa lúc chat và lúc mở form), backend còn soát chặt lần nữa lúc gửi duyệt/duyệt
 * (CR-260) — nên tin số này ở mức "điền sẵn cho tiện", không phải nguồn sự thật.
 */

/** Đọc `?offsets=` thành map payable_id -> số tiền cấn trừ đề xuất; phần tử hỏng bị bỏ qua. */
export function parseOffsetsParam(raw: string | null): Map<number, number> {
  const map = new Map<number, number>()
  if (!raw) return map
  for (const part of raw.split(',')) {
    const [idPart, amountPart] = part.split(':')
    const id = Number(idPart)
    const amount = Number(amountPart)
    if (Number.isInteger(id) && id > 0 && Number.isFinite(amount) && amount > 0) {
      map.set(id, amount)
    }
  }
  return map
}

/**
 * Chia một khoản nợ thành (chi thật, cấn trừ) theo số đề xuất — cấn trừ kẹp trong
 * [0, nợ còn lại], phần chi thật là số còn lại sau cấn trừ (có thể về 0 khi treo phủ hết).
 */
export function splitLineOffset(
  remaining: number,
  suggested: number,
): { amount: number; offset: number } {
  const rem = Math.max(0, Number(remaining) || 0)
  const offset = Math.round(Math.min(Math.max(0, Number(suggested) || 0), rem) * 100) / 100
  return { amount: Math.round((rem - offset) * 100) / 100, offset }
}
