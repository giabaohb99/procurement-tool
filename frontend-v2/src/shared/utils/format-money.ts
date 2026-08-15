import { appConfig } from '@/core/config/app-config'

/**
 * ⚠️ KHÔNG gọi thẳng `toLocaleString('vi-VN')` lên số tiền: mặc định nó hiện 3 chữ số
 * thập phân, làm lẻ đồng rò ra cột danh sách (`4.760.000,08 đ`). Luôn dùng hai hàm dưới.
 * Đây chỉ là định dạng HIỂN THỊ — giá trị lưu trong DB vẫn giữ nguyên độ chính xác.
 */

const { locale } = appConfig

/** TIỀN (thành tiền, tổng cộng) — làm tròn tới đồng. */
export function formatMoney(value: number | string | null | undefined): string {
  const num = toNumber(value)
  if (num === null) return ''
  return num.toLocaleString(locale, { maximumFractionDigits: 0 })
}

/** ĐƠN GIÁ — giữ tối đa 4 chữ số thập phân, không ép đủ 4 nếu là số tròn. */
export function formatUnitPrice(value: number | string | null | undefined): string {
  const num = toNumber(value)
  if (num === null) return ''
  return num.toLocaleString(locale, { maximumFractionDigits: 4 })
}

/** Số lượng — tối đa 3 chữ số thập phân. */
export function formatQuantity(value: number | string | null | undefined): string {
  const num = toNumber(value)
  if (num === null) return ''
  return num.toLocaleString(locale, { maximumFractionDigits: 3 })
}

function toNumber(value: number | string | null | undefined): number | null {
  if (value === null || value === undefined || value === '') return null
  const num = typeof value === 'number' ? value : Number(value)
  return Number.isFinite(num) ? num : null
}
