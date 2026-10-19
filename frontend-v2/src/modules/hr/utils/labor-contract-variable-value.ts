import { VARIABLE_TYPE_DATE, VARIABLE_TYPE_MONEY, VARIABLE_TYPE_NUMBER } from '../types/labor-contract-variable'

/** Trần tiền của backend (`variable_rules.MONEY_MAX`). */
export const MAX_VARIABLE_MONEY = 10 ** 12

/** Số lẻ tối đa của kiểu «Số» (backend: 2). */
export const NUMBER_MAX_DECIMALS = 2

/**
 * Giá trị trong ô → chuỗi GỬI backend. Kiểu «Số» cho gõ `,` hoặc `.` làm dấu thập phân nên đổi
 * `,` → `.` và bỏ dấu thập phân treo cuối («1,» → «1»); kiểu khác giữ nguyên. Backend vẫn là chuẩn
 * (chuẩn hóa + kiểm lại); đây chỉ để khỏi gửi chuỗi chắc chắn bị từ chối.
 */
export function toWireValue(valueType: number, raw: string): string {
  if (valueType !== VARIABLE_TYPE_NUMBER) return raw
  return raw.trim().replace(',', '.').replace(/\.$/, '')
}

/** Chuỗi chuẩn của backend («1.5») → chữ hiện trong ô số kiểu Việt («1,5»). */
export function numberToDisplay(wire: string): string {
  return wire.replace('.', ',')
}

/** Giữ lại chữ số + đúng một dấu thập phân (`,` hoặc `.`) và tối đa `NUMBER_MAX_DECIMALS` số lẻ. */
export function sanitizeNumberText(text: string): string {
  const cleaned = text.replace(/[^\d.,]/g, '')
  const at = cleaned.search(/[.,]/)
  if (at < 0) return cleaned
  const whole = cleaned.slice(0, at)
  const frac = cleaned.slice(at + 1).replace(/[.,]/g, '').slice(0, NUMBER_MAX_DECIMALS)
  return `${whole}${cleaned[at]}${frac}`
}

/** Giá trị chuẩn → chữ đọc được (hộp Sửa HĐ hiện biến đã ngừng dùng ở chế độ chỉ đọc). */
export function formatVariableValue(valueType: number, wire: string): string {
  if (!wire) return ''
  if (valueType === VARIABLE_TYPE_DATE) {
    const [y, m, d] = wire.split('-')
    return y && m && d ? `${d}/${m}/${y}` : wire
  }
  if (valueType === VARIABLE_TYPE_MONEY) return /^\d+$/.test(wire) ? Number(wire).toLocaleString('vi-VN') : wire
  if (valueType === VARIABLE_TYPE_NUMBER) {
    const [whole, frac] = wire.split('.')
    const grouped = /^\d+$/.test(whole) ? Number(whole).toLocaleString('vi-VN') : whole
    return frac ? `${grouped},${frac}` : grouped
  }
  return wire
}
