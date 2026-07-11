import { useState } from 'react'
import type { CSSProperties } from 'react'

/** Ô nhập SỐ theo chuẩn Việt Nam:
 *  - dấu chấm "." = ngăn cách hàng nghìn (bỏ khi tính)
 *  - dấu phẩy "," = dấu thập phân
 *  Chặn số âm. `decimals=false` (mặc định) => số nguyên (tiền/VNĐ).
 *  `decimals=true` => cho số lẻ (số lượng theo kg/mét…), tối đa 3 chữ số thập phân.
 *
 *  Hiển thị: khi KHÔNG focus -> định dạng VN (vd 1.250,5 hoặc 10.500).
 *            khi ĐANG focus  -> giữ đúng chuỗi người dùng đang gõ.
 */

// Định dạng số -> chuỗi kiểu VN
export function formatVN(n: number, decimals = false): string {
  const v = Number(n) || 0
  if (!v) return ''
  return decimals
    ? v.toLocaleString('vi-VN', { maximumFractionDigits: 3 })
    : Math.round(v).toLocaleString('vi-VN')
}

// Parse chuỗi người dùng gõ (kiểu VN) -> number (không âm)
export function parseVN(s: string, decimals = false): number {
  if (!s) return 0
  if (!decimals) {
    const digits = s.replace(/[^\d]/g, '')          // chỉ lấy chữ số -> số nguyên
    return digits ? parseInt(digits, 10) : 0
  }
  // Số lẻ: bỏ dấu chấm (ngăn nghìn), đổi dấu phẩy -> chấm thập phân
  let cleaned = s.replace(/[^\d.,]/g, '').replace(/\./g, '').replace(',', '.')
  const parts = cleaned.split('.')
  if (parts.length > 2) cleaned = parts[0] + '.' + parts.slice(1).join('')   // chỉ 1 dấu thập phân
  const v = parseFloat(cleaned)
  return isNaN(v) || v < 0 ? 0 : v
}

type Props = {
  value: number
  onChange: (n: number) => void
  decimals?: boolean
  disabled?: boolean
  placeholder?: string
  className?: string
  style?: CSSProperties
}

export default function NumberInput({ value, onChange, decimals = false, disabled, placeholder, className, style }: Props) {
  const [focused, setFocused] = useState(false)
  const [raw, setRaw] = useState('')

  const shown = focused ? raw : formatVN(Number(value) || 0, decimals)
  const allow = decimals ? /[^\d.,]/g : /[^\d.]/g

  return (
    <input
      type="text"
      inputMode={decimals ? 'decimal' : 'numeric'}
      disabled={disabled}
      className={className}
      style={style}
      placeholder={placeholder}
      value={shown}
      onFocus={() => { const v = Number(value) || 0; setRaw(v ? formatVN(v, decimals) : ''); setFocused(true) }}
      onBlur={() => { setFocused(false); onChange(parseVN(raw, decimals)) }}
      onChange={(e) => { const cleaned = e.target.value.replace(allow, ''); setRaw(cleaned); onChange(parseVN(cleaned, decimals)) }}
    />
  )
}
