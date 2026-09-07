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
 * Hai màn dùng KHÁC nhau (bao-CR-308):
 * - YCMH: CHẶN CỨNG — dòng ĐMH nối ngược về dòng YCMH bằng chuỗi mã hàng, YCMH trùng mã làm
 *   SL đặt/nhận cộng dồn bị ghi vào mọi dòng trùng → tiến độ nhân đôi. Backend chặn cùng luật
 *   (`app/core/utils.assert_unique_product_codes`).
 * - ĐMH: chỉ HỎI XÁC NHẬN khi lưu — nghiệp vụ cần trùng mã để tách dòng theo bộ chứng từ
 *   (cùng mã, khác lô / khác Tên trên hóa đơn); đồng bộ về YCMH cộng gộp theo mã nên vẫn đúng.
 *   Backend ĐMH không còn chặn.
 *
 * Chỉ tính TRÙNG MỚI (số lần xuất hiện tăng so với `saved`) — phiếu cũ đã lỡ trùng vẫn phải
 * lưu lại được, vì dòng đã Hoàn thành/Hủy đơn không có nút xóa.
 */
export function newDupCodes(current: string[], saved: string[] = []): string[] {
  const before = count(saved)
  const after = count(current)
  const bad: string[] = []
  after.forEach((n, c) => { if (n > 1 && n > (before.get(c) || 0)) bad.push(c) })
  return bad.sort()
}
