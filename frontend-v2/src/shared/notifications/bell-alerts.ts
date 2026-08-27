import type { SystemAlert } from './notification-types'

/**
 * Số cảnh báo hệ thống được vẽ trong CHUÔNG.
 *
 * ⚠️ `/api/alerts` trả về TOÀN BỘ, không phân trang, không giới hạn: nó quét cả
 * bảng giao hàng chưa nhận, công nợ chưa trả và hợp đồng chưa thanh lý rồi đẩy
 * hết ra một mảng. Trên dữ liệu thật, riêng công nợ quá hạn đã vài chục dòng —
 * trước 27/08/2026 chuông vẽ hết, đẩy phần thông báo lên tít trên và biến cái
 * popup xem nhanh thành một danh sách phải cuộn mãi.
 *
 * Năm cái là đủ cho "liếc một cái xem có gì gấp"; muốn xem đủ thì bấm vào chính
 * cảnh báo để sang màn nghiệp vụ của nó (ĐMH, Công nợ, Hợp đồng) — nơi có bộ
 * lọc và phân trang tử tế.
 */
export const BELL_ALERT_LIMIT = 5

export interface BellAlerts {
  /** Phần được vẽ, đã xếp cảnh báo NGUY HIỂM lên trước. */
  shown: SystemAlert[]
  /** Số cảnh báo bị cắt bớt. `0` = vẽ đủ. */
  hidden: number
}

/**
 * Chọn ra ít cảnh báo nhất để vẽ trong chuông.
 *
 * Xếp `danger` lên trước `warn` rồi mới cắt: backend trả theo THỨ TỰ LOẠI (giao
 * hàng → công nợ → hợp đồng), nên cắt thẳng thì năm cái "sắp tới hạn" của giao
 * hàng có thể che mất một cái "công nợ QUÁ HẠN" nằm sau. Trong cùng một mức thì
 * giữ nguyên thứ tự backend trả về (`sort` của JS ổn định từ ES2019).
 */
export function pickBellAlerts(items: SystemAlert[], limit = BELL_ALERT_LIMIT): BellAlerts {
  const byLevel = [...items].sort((a, b) => Number(b.level === 'danger') - Number(a.level === 'danger'))

  return {
    shown: byLevel.slice(0, limit),
    hidden: Math.max(0, items.length - limit),
  }
}
