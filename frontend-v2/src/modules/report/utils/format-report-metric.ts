import { formatMoney, formatPercent } from '@/shared/utils/format-money'

import type { ReportMetricKind } from '../types/report-analytics'

/** Ranh giới đổi đơn vị của chỉ số `hours`: dưới 1 ngày hiện theo giờ. */
const HOURS_PER_DAY = 24

function round1(value: number): string {
  return value.toLocaleString('vi-VN', { maximumFractionDigits: 1 })
}

/**
 * Tiền rút gọn cho thẻ KPI / trục / cột ngang: "1,2 tỷ", "537,2 tr", "45 k".
 * Không dùng `shortMoney` của Thu mua vì nó in dấu CHẤM thập phân ("537.2 tr")
 * — đặt cạnh "74,5%" trên cùng một hàng thẻ là hai quy ước lệch nhau.
 */
function compactMoney(value: number): string {
  const abs = Math.abs(value)
  if (abs >= 1e9) return `${round1(value / 1e9)} tỷ`
  if (abs >= 1e6) return `${round1(value / 1e6)} tr`
  if (abs >= 1e3) return `${Math.round(value / 1e3).toLocaleString('vi-VN')} k`
  return round1(value)
}

/** `kind: 'hours'` → "x giờ" khi dưới một ngày, "y ngày" khi từ một ngày trở lên. */
function formatReportHours(hours: number): string {
  if (hours < HOURS_PER_DAY) return `${round1(hours)} giờ`
  return `${round1(hours / HOURS_PER_DAY)} ngày`
}

/**
 * Định dạng MỘT giá trị chỉ số theo `kind` do backend khai trong `meta.metrics`
 * — frontend không tự đoán đơn vị, chỉ đọc `kind` rồi chọn hàm hiển thị đúng.
 *
 * `variant`:
 *  - `'compact'` — cho thẻ KPI và trục/tooltip biểu đồ, tiền rút gọn
 *    ("1,2 tỷ", dấu phẩy thập phân như mọi số khác).
 *  - `'full'` (mặc định) — cho ô bảng, tiền đủ số (`formatMoney`, "1.234.000 đ").
 *
 * `null`/`undefined`/`NaN` → "—" (mốc/nhóm không có chỉ số đó — KHÁC số 0).
 */
export function formatReportMetricValue(
  value: number | null | undefined,
  kind: ReportMetricKind,
  variant: 'compact' | 'full' = 'full',
): string {
  if (value === null || value === undefined || !Number.isFinite(value)) return '—'

  switch (kind) {
    case 'int':
      return formatMoney(value)
    case 'money':
      return variant === 'compact' ? `${compactMoney(value)} đ` : `${formatMoney(value)} đ`
    case 'days':
      return `${round1(value)} ngày`
    case 'hours':
      return formatReportHours(value)
    case 'percent':
      return formatPercent(value)
    default:
      //  `ReportMetricKind` đã liệt kê đủ 5 nhánh — đây chỉ là lưới an toàn nếu
      //  backend gửi một `kind` mới chưa khai ở tầng frontend: hiện nguyên số
      //  thay vì vỡ trang.
      return formatMoney(value)
  }
}
