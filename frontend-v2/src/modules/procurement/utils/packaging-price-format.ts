/**
 * duoc-CR-784 — định dạng số của cụm Giá bao bì, chép đúng luật hiển thị của bản mẫu (`nf`, `fmtS`, `fmtP`).
 *
 * Giá bao bì lẻ tới phần đồng (nhãn 85,5 đ/cái) nên số dưới 100.000 giữ tối đa 2 chữ số lẻ, số lớn hơn
 * làm tròn tới đồng — cùng một cột mà chỗ "1.234,57" chỗ "1.234.567,891" thì đọc lướt rất dễ nhầm bậc.
 * `null` = chưa có giá → chuỗi rỗng; nơi vẽ ô tự đặt gạch `<span>—</span>` (DataTable nuốt chuỗi gạch trần).
 */

type Num = number | null | undefined

function isNumber(value: Num): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

/** Giá / chi phí một đơn vị. */
export function formatPackagingPrice(value: Num): string {
  if (!isNumber(value)) return ''
  return Math.abs(value) < 100000
    ? value.toLocaleString('vi-VN', { maximumFractionDigits: 2 })
    : Math.round(value).toLocaleString('vi-VN')
}

/** Chênh lệch có dấu: "+1.250", "-85,5", "0". */
export function formatPackagingDiff(value: Num): string {
  if (!isNumber(value)) return ''
  const text = formatPackagingPrice(value)
  return value > 0 ? `+${text}` : text
}

/**
 * Phần trăm có dấu, một chữ số lẻ: 0.125 → "+12,5%". Vào là TỶ SỐ (chênh / giá cũ) đúng như máy chủ trả
 * (`pct = diff / old`, 6 số lẻ) — KHÁC nếp `formatPercent` của các báo cáo (vốn nhận số đã nhân 100).
 */
export function formatPackagingPercent(ratio: Num): string {
  if (!isNumber(ratio)) return ''
  const percent = ratio * 100
  const text = percent.toLocaleString('vi-VN', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })
  return percent > 0 ? `+${text}%` : `${text}%`
}

/**
 * Màu theo chiều chênh: TĂNG đỏ (giá lên là xấu), GIẢM xanh, ~0 không tô — người chủ chốt 27/11/2026, đảo lại quyết định
 * 20/11/2026 (tăng xanh), giống bản mẫu HTML. Áp chung mọi màn cụm Giá bao bì để một màu chỉ mang một nghĩa.
 */
export function packagingDiffTone(value: Num): string | undefined {
  if (!isNumber(value) || Math.abs(value) < 1e-6) return undefined
  return value > 0 ? 'text-destructive' : 'text-emerald-600 dark:text-emerald-400'
}
