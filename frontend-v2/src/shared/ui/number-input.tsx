import { useState } from 'react'

import { cn } from '@/shared/utils/cn'
import { Input } from '@/shared/ui/input'

/**
 * Ô nhập SỐ theo chuẩn Việt Nam — bản v2 của `frontend/src/components/NumberInput.tsx`.
 *
 * `<Input type="number">` của trình duyệt luôn hiện số TRẦN (`3500000`), không có
 * dấu ngăn nghìn, nên đọc lướt qua rất dễ nhầm bậc — ba triệu rưỡi trông y hệt ba
 * trăm năm mươi nghìn. Ô này hiện `3.500.000` lúc không gõ và trả lại chuỗi thô
 * lúc đang gõ, đúng như bản đang chạy thật.
 *
 * Quy ước: dấu chấm `.` ngăn hàng nghìn, dấu phẩy `,` là dấu thập phân. Số âm bị
 * chặn — mọi ô số của chứng từ (số lượng, đơn giá, thành tiền, số ngày) đều không
 * có nghĩa khi âm.
 */

/** Số chữ số thập phân giữ lại cho SỐ LƯỢNG và các ô số thường. */
export const DEFAULT_MAX_DECIMALS = 3

/**
 * Riêng ĐƠN GIÁ giữ 4 chữ số: giá nhập khẩu/quy đổi hay lẻ tới phần nghìn đồng
 * (1.668,182 đ/cái), cắt còn 3 là mất tiền khi nhân với số lượng lớn (CR-058).
 */
export const PRICE_MAX_DECIMALS = 4

/** Số -> chuỗi kiểu VN. Trả chuỗi rỗng cho số 0 để ô trống thay vì hiện "0". */
export function formatNumberVn(
  value: number,
  decimals = true,
  maxDecimals = DEFAULT_MAX_DECIMALS,
): string {
  const num = Number(value) || 0
  if (!num) return ''
  return decimals
    ? num.toLocaleString('vi-VN', { maximumFractionDigits: maxDecimals })
    : Math.round(num).toLocaleString('vi-VN')
}

/** Chuỗi người dùng gõ (kiểu VN) -> số không âm. */
export function parseNumberVn(
  text: string,
  decimals = true,
  maxDecimals = DEFAULT_MAX_DECIMALS,
): number {
  if (!text) return 0
  if (!decimals) {
    const digits = text.replace(/[^\d]/g, '')
    return digits ? parseInt(digits, 10) : 0
  }
  //  Bỏ dấu chấm (ngăn nghìn), đổi dấu phẩy thành dấu thập phân.
  let cleaned = text.replace(/[^\d.,]/g, '').replace(/\./g, '').replace(/,/g, '.')
  const parts = cleaned.split('.')
  //  Gõ nhầm hai dấu phẩy thì gộp lại làm một, đừng để `parseFloat` cắt cụt phần sau.
  if (parts.length > 2) cleaned = `${parts[0]}.${parts.slice(1).join('')}`
  const num = parseFloat(cleaned)
  if (isNaN(num) || num < 0) return 0
  //  Cắt đúng số lẻ cho phép, tránh đẩy lên server con số dài hơn cột DB rồi bị
  //  làm tròn ngược — màn hình một đằng, sổ sách một nẻo.
  return Number(num.toFixed(maxDecimals))
}

interface NumberInputProps {
  value: number
  onChange: (value: number) => void
  /** `false` = ép số nguyên (số thứ tự, số ngày). Mặc định cho nhập số lẻ. */
  decimals?: boolean
  maxDecimals?: number
  /** Chặn TRÊN, kẹp ngay lúc gõ (ô VAT tối đa 99,99). Bỏ trống = không chặn. */
  max?: number
  disabled?: boolean
  placeholder?: string
  className?: string
  title?: string
}

export function NumberInput({
  value,
  onChange,
  decimals = true,
  maxDecimals = DEFAULT_MAX_DECIMALS,
  max,
  disabled,
  placeholder,
  className,
  title,
}: NumberInputProps) {
  const [focused, setFocused] = useState(false)
  const [raw, setRaw] = useState('')

  const shown = focused ? raw : formatNumberVn(Number(value) || 0, decimals, maxDecimals)
  const allowed = decimals ? /[^\d.,]/g : /[^\d.]/g
  //  Kẹp NGAY lúc gõ chứ không đợi rời ô: người dùng thấy con số bị chặn lại, thay
  //  vì gõ xong mới ăn lỗi 422 từ server.
  const clamp = (num: number) => (max != null && num > max ? max : num)

  return (
    <Input
      type="text"
      inputMode={decimals ? 'decimal' : 'numeric'}
      disabled={disabled}
      title={title}
      placeholder={placeholder}
      className={cn('tabular-nums', className)}
      value={shown}
      onFocus={() => {
        const num = Number(value) || 0
        setRaw(num ? formatNumberVn(num, decimals, maxDecimals) : '')
        setFocused(true)
      }}
      onBlur={() => {
        setFocused(false)
        onChange(clamp(parseNumberVn(raw, decimals, maxDecimals)))
      }}
      onChange={(event) => {
        const cleaned = event.target.value.replace(allowed, '')
        const parsed = parseNumberVn(cleaned, decimals, maxDecimals)
        const next = clamp(parsed)
        //  Vượt trần thì hiện luôn con số đã kẹp, đừng để ô hiện một đằng state một nẻo.
        setRaw(max != null && parsed > max ? formatNumberVn(next, decimals, maxDecimals) : cleaned)
        onChange(next)
      }}
    />
  )
}
