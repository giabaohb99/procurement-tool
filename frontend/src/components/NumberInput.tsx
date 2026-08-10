import { useState } from 'react'
import type { CSSProperties } from 'react'

/** Ô nhập SỐ theo chuẩn Việt Nam:
 *  - dấu chấm "." = ngăn cách hàng nghìn (bỏ khi tính)
 *  - dấu phẩy "," = dấu thập phân
 *  Chặn số âm. Mặc định CHO số lẻ (`decimals=true`): áp dụng cho cả tiền lẫn số lượng,
 *  tối đa 3 chữ số thập phân (vd 5.000,5 · 1.250,75). Đặt `decimals={false}` nếu muốn
 *  ép số nguyên (vd số thứ tự, số ngày…).
 *
 *  `maxDecimals`: số chữ số thập phân GIỮ LẠI. Ô ĐƠN GIÁ dùng 4 — giá nhập khẩu/quy đổi
 *  hay lẻ tới phần nghìn đồng (vd 1.668,182 đ/cái), để 3 như mặc định là làm tròn mất tiền
 *  khi nhân với số lượng lớn.
 *
 *  `max`: chặn TRÊN, kẹp giá trị ngay khi gõ (vd ô VAT: tối đa 99,99%). Không đặt = không chặn.
 *
 *  Hiển thị: khi KHÔNG focus -> định dạng VN (vd 1.250,5 hoặc 10.500).
 *            khi ĐANG focus  -> giữ đúng chuỗi người dùng đang gõ.
 */

// Định dạng số -> chuỗi kiểu VN
export function formatVN(n: number, decimals = true, maxDecimals = 3): string {
  const v = Number(n) || 0
  if (!v) return ''
  return decimals
    ? v.toLocaleString('vi-VN', { maximumFractionDigits: maxDecimals })
    : Math.round(v).toLocaleString('vi-VN')
}

// Parse chuỗi người dùng gõ (kiểu VN) -> number (không âm)
export function parseVN(s: string, decimals = true, maxDecimals = 3): number {
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
  if (isNaN(v) || v < 0) return 0
  // Cắt đúng số lẻ cho phép, tránh đẩy lên server con số dài hơn cột DB rồi bị làm tròn ngược
  return Number(v.toFixed(maxDecimals))
}

type Props = {
  value: number
  onChange: (n: number) => void
  decimals?: boolean
  maxDecimals?: number
  max?: number
  disabled?: boolean
  placeholder?: string
  className?: string
  style?: CSSProperties
}

export default function NumberInput({ value, onChange, decimals = true, maxDecimals = 3, max, disabled, placeholder, className, style }: Props) {
  const [focused, setFocused] = useState(false)
  const [raw, setRaw] = useState('')

  const shown = focused ? raw : formatVN(Number(value) || 0, decimals, maxDecimals)
  const allow = decimals ? /[^\d.,]/g : /[^\d.]/g
  // Kẹp NGAY lúc gõ (không đợi blur): người dùng thấy con số bị chặn lại thay vì gõ xong
  // mới bị server trả 422. Kẹp cả chuỗi đang gõ để ô không hiện một đằng, state một nẻo.
  const kep = (n: number) => (max != null && n > max ? max : n)

  return (
    <input
      type="text"
      inputMode={decimals ? 'decimal' : 'numeric'}
      disabled={disabled}
      className={className}
      style={style}
      placeholder={placeholder}
      value={shown}
      onFocus={() => { const v = Number(value) || 0; setRaw(v ? formatVN(v, decimals, maxDecimals) : ''); setFocused(true) }}
      onBlur={() => { setFocused(false); onChange(kep(parseVN(raw, decimals, maxDecimals))) }}
      onChange={(e) => {
        const cleaned = e.target.value.replace(allow, '')
        const n = kep(parseVN(cleaned, decimals, maxDecimals))
        setRaw(max != null && parseVN(cleaned, decimals, maxDecimals) > max ? formatVN(n, decimals, maxDecimals) : cleaned)
        onChange(n)
      }}
    />
  )
}
