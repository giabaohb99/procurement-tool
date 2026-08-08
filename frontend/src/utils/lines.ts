/** Quy tắc dòng hàng dùng chung cho Yêu cầu mua hàng và Đơn mua hàng. */

const count = (codes: string[]) => {
  const m = new Map<string, number>()
  for (const raw of codes) {
    const c = (raw || '').trim()
    if (c) m.set(c, (m.get(c) || 0) + 1)
  }
  return m
}

/**
 * Mã hàng bị trùng MỚI so với bản đã lưu trên server.
 *
 * Mã phải duy nhất trên mỗi phiếu: dòng ĐMH nối ngược về dòng YCMH bằng chuỗi mã hàng, trùng
 * mã làm SL đặt/nhận bị cộng dồn rồi ghi vào mọi dòng trùng → tiến độ sai.
 *
 * Chỉ tính TRÙNG MỚI (số lần xuất hiện tăng so với `saved`) — phiếu cũ đã lỡ trùng vẫn phải
 * lưu lại được, vì dòng đã Hoàn thành/Hủy đơn không có nút xóa. Giống hệt luật ở backend
 * (`app/core/utils.assert_unique_product_codes`).
 */
export function newDupCodes(current: string[], saved: string[] = []): string[] {
  const before = count(saved)
  const after = count(current)
  const bad: string[] = []
  after.forEach((n, c) => { if (n > 1 && n > (before.get(c) || 0)) bad.push(c) })
  return bad.sort()
}
