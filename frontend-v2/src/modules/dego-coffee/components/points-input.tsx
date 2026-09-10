import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'

interface PointsInputProps {
  value: number
  onChange: (value: number) => void
  id?: string
  placeholder?: string
  disabled?: boolean
  className?: string
}

/**
 * Ô nhập ĐIỂM — số nguyên không âm, **tự chèn dấu ngăn nghìn NGAY LÚC GÕ**
 * (gõ `200000` thấy `200.000`), theo yêu cầu 08/09/2026.
 *
 * Khác `shared/ui/number-input.tsx` (cố ý hiện số thô khi đang gõ, khớp bản v1
 * đang chạy thật) — điểm cà phê là phân hệ mới không vướng khuôn cũ, và ô này
 * chỉ nhận SỐ NGUYÊN nên format-lúc-gõ không phải xử caret quanh dấu thập phân.
 * Con trỏ đặt cuối ô sau mỗi lần gõ — nhập tiền kiểu bấm nối đuôi thì đúng ý.
 */
export function PointsInput({ value, onChange, id, placeholder, disabled, className }: PointsInputProps) {
  const shown = value ? value.toLocaleString('vi-VN') : ''

  function handleChange(text: string) {
    const digits = text.replace(/[^\d]/g, '')
    onChange(digits ? Math.min(parseInt(digits, 10), 1_000_000_000) : 0)
  }

  return (
    <Input
      id={id}
      type="text"
      inputMode="numeric"
      disabled={disabled}
      placeholder={placeholder}
      className={cn('tabular-nums', className)}
      value={shown}
      onChange={(e) => handleChange(e.target.value)}
    />
  )
}
