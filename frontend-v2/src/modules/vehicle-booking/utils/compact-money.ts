import { formatMoney } from '@/shared/utils/format-money'

/**
 * Tiền GỌN cho thẻ KPI / bảng thống kê Đặt xe.
 * 286.000 -> "286 tr"; 1.675.000.000 -> "1,7 tỷ"; nhỏ hơn triệu -> nguyên đồng.
 */
export function compactMoney(value: number): string {
  if (Math.abs(value) >= 1_000_000_000)
    return `${(value / 1_000_000_000).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} tỷ`
  if (Math.abs(value) >= 1_000_000)
    return `${Math.round(value / 1_000_000).toLocaleString('vi-VN')} tr`
  return formatMoney(value)
}
