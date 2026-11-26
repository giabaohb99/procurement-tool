/**
 * duoc-CR-784 — ô GIÁ GIẢ ĐỊNH của một mã ở màn Tác động giá (nền vàng như bản mẫu). Dùng chung cho ô bảng "Mã đã chọn" và
 * thẻ điện thoại của cùng bảng, để hai chế độ gõ ra đúng một luật: ô xóa trắng trả 0 = BỎ giả định (giá bao bì 0 đồng
 * không có nghĩa mô phỏng), quay về giá mới.
 */
import { NumberInput, PRICE_MAX_DECIMALS } from '@/shared/ui/number-input'
import { cn } from '@/shared/utils/cn'

interface PackagingAssumedPriceInputProps {
  code: string
  value: number | undefined
  /** `null` = bỏ giả định, quay về giá bảng giá. */
  onChange: (code: string, price: number | null) => void
  className?: string
}

export function PackagingAssumedPriceInput({
  code,
  value,
  onChange,
  className,
}: PackagingAssumedPriceInputProps) {
  return (
    <NumberInput
      aria-label={`Giá giả định ${code}`}
      placeholder="Nhập giá"
      title="Nhập giá giả định để mô phỏng trước khi NCC chốt giá; xóa trắng để quay về giá mới"
      maxDecimals={PRICE_MAX_DECIMALS}
      className={cn('h-8 bg-amber-50 text-right dark:bg-amber-950', className)}
      value={value ?? 0}
      onChange={(price) => onChange(code, price > 0 ? price : null)}
    />
  )
}
