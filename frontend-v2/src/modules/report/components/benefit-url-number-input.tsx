import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { NumberInput } from '@/shared/ui/number-input'

import { formatAmountParam, parseAmountParam } from '../utils/benefit-amount-param'
import { BENEFIT_INPUT_DEBOUNCE_MS } from '../utils/benefit-occasion-presets'

interface BenefitUrlNumberInputProps {
  /** Tên tham số trên URL (`amount_staff`, `age_min`…). */
  name: string
  id: string
  /** Trần kẹp ngay lúc gõ — khớp trần backend để khỏi ăn 422. */
  max: number
  disabled?: boolean
  placeholder?: string
  className?: string
}

/**
 * Ô số nguyên không âm của bộ lọc H1, nguồn sự thật là URL. Ô hiện dấu ngăn nghìn kiểu VN
 * (`NumberInput` dùng chung), gõ chạy bằng state cục bộ và chỉ ghi URL sau khi ngừng gõ;
 * URL đổi từ nơi khác (bấm dịp có sẵn, "Bỏ hết điều kiện", nút Back) thì ô theo
 * (`useUrlSearchParam`). Số 0 = "chưa nhập" → xóa khỏi URL.
 */
export function BenefitUrlNumberInput({
  name,
  id,
  max,
  disabled,
  placeholder,
  className,
}: BenefitUrlNumberInputProps) {
  const { value, setValue } = useUrlSearchParam(name, BENEFIT_INPUT_DEBOUNCE_MS)
  return (
    <NumberInput
      id={id}
      value={Math.min(parseAmountParam(value), max)}
      onChange={(next) => setValue(formatAmountParam(next))}
      decimals={false}
      max={max}
      disabled={disabled}
      placeholder={placeholder}
      className={className}
    />
  )
}
