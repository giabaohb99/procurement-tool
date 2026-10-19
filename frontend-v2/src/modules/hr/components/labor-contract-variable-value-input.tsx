import { useState } from 'react'

import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Textarea } from '@/shared/ui/textarea'
import {
  VARIABLE_TYPE_DATE,
  VARIABLE_TYPE_MONEY,
  VARIABLE_TYPE_MULTILINE,
  VARIABLE_TYPE_NUMBER,
} from '../types/labor-contract-variable'
import {
  MAX_VARIABLE_MONEY,
  formatVariableValue,
  numberToDisplay,
  sanitizeNumberText,
  toWireValue,
} from '../utils/labor-contract-variable-value'

interface ValueInputProps {
  /** Kiểu giá trị (`LaborContractVariableType`). */
  valueType: number
  /**
   * Giá trị ở dạng chuỗi CHUẨN của backend (tiền «15000000», số «1.5», ngày «2026-10-01», chữ nguyên văn);
   * chuỗi rỗng = chưa có giá trị.
   */
  value: string
  onChange: (value: string) => void
  id?: string
  'aria-label'?: string
  placeholder?: string
  disabled?: boolean
}

/**
 * Ô nhập giá trị theo KIỂU của biến — dùng ở hộp mặc định của biến (phase 04) và ô «Thông tin bổ sung»
 * trong hộp Lập / Sửa hợp đồng (phase 05). Giá trị ra/vào là chuỗi chuẩn nên form chỉ cần lưu chuỗi.
 *
 * Số 0 là MỘT GIÁ TRỊ THẬT cho kiểu Số và Tiền («0» thỏa «bắt buộc», in ra «0»); ô để trống mới là
 * «chưa có giá trị». Vì vậy tiền không dùng `NumberInput` (nó hiện ô trống cho 0).
 */
export function LaborContractVariableValueInput({
  valueType,
  value,
  onChange,
  id,
  'aria-label': ariaLabel,
  placeholder,
  disabled,
}: ValueInputProps) {
  if (valueType === VARIABLE_TYPE_MONEY) {
    return (
      <MoneyTextInput
        id={id}
        aria-label={ariaLabel}
        placeholder={placeholder}
        disabled={disabled}
        value={value}
        onChange={onChange}
      />
    )
  }
  if (valueType === VARIABLE_TYPE_DATE) {
    return <DatePicker id={id} value={value} onChange={onChange} disabled={disabled} placeholder={placeholder} />
  }
  if (valueType === VARIABLE_TYPE_MULTILINE) {
    return (
      <Textarea
        id={id}
        aria-label={ariaLabel}
        rows={3}
        maxLength={2000}
        placeholder={placeholder}
        disabled={disabled}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    )
  }
  if (valueType === VARIABLE_TYPE_NUMBER) {
    return (
      <NumberTextInput
        id={id}
        aria-label={ariaLabel}
        placeholder={placeholder}
        disabled={disabled}
        value={value}
        onChange={onChange}
      />
    )
  }
  return (
    <Input
      id={id}
      aria-label={ariaLabel}
      maxLength={255}
      placeholder={placeholder}
      disabled={disabled}
      value={value}
      //  Enter trong ô nằm trong <form> khác (hộp Lập HĐ trong trang hồ sơ) không được submit form cha.
      onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()}
      onChange={(e) => onChange(e.target.value)}
    />
  )
}

/**
 * Ô «Số»: gõ `1,5` hay `1.5` đều được, giữ NGUYÊN chữ đang gõ (không định dạng nghìn kẻo nhảy con trỏ);
 * giá trị ra ngoài là dạng chuẩn «1.5». Chữ đang gõ giữ ở state cục bộ, ngoài đổi (reset form) thì
 * hiện lại theo giá trị ngoài — không cần effect.
 */
function NumberTextInput({
  value,
  onChange,
  ...rest
}: Pick<ValueInputProps, 'value' | 'onChange' | 'id' | 'aria-label' | 'placeholder' | 'disabled'>) {
  const [text, setText] = useState(numberToDisplay(value))
  const shown = toWireValue(VARIABLE_TYPE_NUMBER, text) === value ? text : numberToDisplay(value)
  return (
    <Input
      {...rest}
      inputMode="decimal"
      className="tabular-nums"
      value={shown}
      onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()}
      onChange={(e) => {
        const next = sanitizeNumberText(e.target.value)
        setText(next)
        onChange(toWireValue(VARIABLE_TYPE_NUMBER, next))
      }}
    />
  )
}

/** Ô «Tiền»: chỉ chữ số (không âm, không lẻ), hiện ngăn nghìn kiểu Việt, kẹp ở trần 10^12; trống ≠ 0. */
function MoneyTextInput({
  value,
  onChange,
  ...rest
}: Pick<ValueInputProps, 'value' | 'onChange' | 'id' | 'aria-label' | 'placeholder' | 'disabled'>) {
  return (
    <Input
      {...rest}
      inputMode="numeric"
      className="tabular-nums"
      value={formatVariableValue(VARIABLE_TYPE_MONEY, value)}
      onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()}
      onChange={(e) => {
        const digits = e.target.value.replace(/\D/g, '').replace(/^0+(?=\d)/, '')
        if (!digits) return onChange('')
        onChange(Number(digits) > MAX_VARIABLE_MONEY ? String(MAX_VARIABLE_MONEY) : digits)
      }}
    />
  )
}
