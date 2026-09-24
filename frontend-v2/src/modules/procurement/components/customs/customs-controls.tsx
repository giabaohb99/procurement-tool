// bao-CR-470 — mấy mẩu điều khiển nhỏ dùng chung giữa các thẻ của màn Tra cứu giá hải
// quan: hàng nút chọn một (Kỳ / Giá), hàng chip đơn vị tính, khung báo trạng thái.
import { Filter, Info } from 'lucide-react'
import type { ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'

import type { CustomsUnitCount } from '../../types/customs'
import { CUSTOMS_NEED_FILTER_MESSAGE, formatCustomsUnitChip } from '../../utils/customs'

interface CustomsSegmentedChoiceProps<T extends string> {
  label: string
  value: T
  options: readonly { value: T; label: string }[]
  onChange: (value: T) => void
}

/** Hàng nút chọn MỘT — nhãn trước, các lựa chọn sau, nút đang chọn tô đặc. */
export function CustomsSegmentedChoice<T extends string>({
  label,
  value,
  options,
  onChange,
}: CustomsSegmentedChoiceProps<T>) {
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-sm" role="group" aria-label={label}>
      <span className="mr-0.5 text-muted-foreground">{label}:</span>
      {options.map((option) => (
        <Button
          key={option.value}
          type="button"
          size="sm"
          variant={option.value === value ? 'default' : 'outline'}
          aria-pressed={option.value === value}
          onClick={() => onChange(option.value)}
        >
          {option.label}
        </Button>
      ))}
    </div>
  )
}

interface CustomsUnitChipsProps {
  label?: string
  units: CustomsUnitCount[]
  value: string
  onChange: (unit: string) => void
}

/**
 * Chọn đơn vị để vẽ — kg và lít KHÔNG vẽ chung (luật 1 của biểu đồ). Mặc định backend
 * chọn đơn vị nhiều dòng nhất; chip nào đang vẽ thì tô đặc.
 */
export function CustomsUnitChips({
  label = 'Đơn vị (vẽ từng đơn vị một)',
  units,
  value,
  onChange,
}: CustomsUnitChipsProps) {
  if (!units.length) return null
  return (
    <div className="flex flex-wrap items-center gap-1.5 text-sm" role="group" aria-label={label}>
      <span className="mr-0.5 text-muted-foreground">{label}:</span>
      {units.map((item) => (
        <Button
          key={item.unit}
          type="button"
          size="xs"
          variant={item.unit === value ? 'default' : 'outline'}
          aria-pressed={item.unit === value}
          onClick={() => onChange(item.unit)}
        >
          {formatCustomsUnitChip(item.unit)} · {item.count} dòng
        </Button>
      ))}
    </div>
  )
}

/** Khung chặn thẻ Biểu đồ / Nhà nhập khẩu khi chưa có từ khóa hoặc mã HS. */
export function CustomsNeedFilterState() {
  return (
    <Card className="items-center gap-2 p-8 text-center text-muted-foreground">
      <Filter className="size-7" />
      <p className="text-sm">{CUSTOMS_NEED_FILTER_MESSAGE}</p>
      <p className="text-xs">
        Biểu đồ của toàn bộ dữ liệu là trộn hàng nghìn mặt hàng, kg lẫn lít — con số không có
        nghĩa.
      </p>
    </Card>
  )
}

interface CustomsNoticeProps {
  tone?: 'info' | 'warning' | 'danger'
  icon?: ReactNode
  children: ReactNode
  className?: string
}

/** Dải thông báo nền nhạt (độ phủ dữ liệu, cảnh báo thay dòng cũ, cảnh báo pháp lý). */
export function CustomsNotice({ tone = 'info', icon, children, className }: CustomsNoticeProps) {
  return (
    <div
      className={cn(
        'flex gap-2 rounded-lg border px-3 py-2 text-sm',
        tone === 'info' && 'border-info/30 bg-info/5 text-foreground',
        tone === 'warning' && 'border-warning/40 bg-warning/10 text-foreground',
        tone === 'danger' && 'border-destructive/30 bg-destructive/5 text-foreground',
        className,
      )}
    >
      <span
        className={cn(
          'mt-0.5 shrink-0',
          tone === 'info' && 'text-info',
          tone === 'warning' && 'text-warning',
          tone === 'danger' && 'text-destructive',
        )}
      >
        {icon ?? <Info className="size-4" />}
      </span>
      <div className="min-w-0 flex-1">{children}</div>
    </div>
  )
}
