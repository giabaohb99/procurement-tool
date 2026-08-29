import { cn } from '@/shared/utils/cn'
import { WORK_COLORS, dotClass } from '../utils/work-colors'

interface WorkColorPickerProps {
  value: string
  onChange: (color: string) => void
  className?: string
}

/**
 * Chọn màu cho tag / giá trị nhãn / cột kanban — 12 màu ĐẶT SẴN của
 * `WORK_COLORS`, không có ô nhập hex.
 *
 * Lý do không cho hex tự do nằm ở đầu `work-colors.ts`: hex người dùng gõ không
 * có biến thể cho nền tối, bật nền tối là chữ đen trên nền đen. Mỗi màu ở đây
 * là một cặp class đã kiểm ở cả hai chế độ nền.
 */
export function WorkColorPicker({ value, onChange, className }: WorkColorPickerProps) {
  return (
    <div className={cn('flex flex-wrap gap-1', className)} role="group" aria-label="Chọn màu">
      {WORK_COLORS.map((c) => (
        <button
          key={c.value}
          type="button"
          aria-label={c.label}
          aria-pressed={value === c.value}
          onClick={() => onChange(c.value)}
          className={cn(
            'size-5 rounded-full ring-offset-2 ring-offset-background',
            dotClass(c.value),
            //  Vòng nhấn lấy màu `primary` của bảng màu tài khoản, không gán
            //  cứng: bảng màu đổi thì vòng chọn đổi theo.
            value === c.value && 'ring-2 ring-primary',
          )}
        />
      ))}
    </div>
  )
}
