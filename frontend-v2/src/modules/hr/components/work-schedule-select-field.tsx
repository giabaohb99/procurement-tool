import { useController, type Control } from 'react-hook-form'

import { useCrudList, type CrudRecord } from '@/shared/crud'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import type { WorkSchedule } from '../types/work-schedule'
import { isChosenId } from '../utils/work-schedule-validation'

interface WorkScheduleSelectFieldProps {
  control: Control<CrudRecord>
  /** Tên ô trong form (`schedule_id`). */
  name: string
  disabled?: boolean
}

/**
 * Ô «Mẫu lịch» của màn Gán lịch — chỉ liệt kê mẫu đang dùng.
 *
 * Cố ý KHÔNG dùng `source` của ô `select` chung: nó cache 5 phút dưới khóa riêng
 * nên mẫu vừa tạo ở màn bên cạnh không hiện ra trong ô chọn, HR đi gán thì thấy
 * thiếu. `useCrudList` nằm dưới gốc `['crud', '/api/work-schedules']` nên lưu/xóa
 * mẫu là danh sách này tự nạp lại.
 */
export function WorkScheduleSelectField({
  control,
  name,
  disabled = false,
}: WorkScheduleSelectFieldProps) {
  const { field, fieldState } = useController({
    control,
    name,
    rules: { validate: (value) => isChosenId(value) || 'Chọn mẫu lịch.' },
  })
  const { data, isLoading, isError } = useCrudList<WorkSchedule>('/api/work-schedules', {
    is_active: 'true',
    page_size: 1000,
  })

  const value = Number(field.value) > 0 ? String(field.value) : ''
  const options = (data?.items ?? []).map((item) => ({ value: String(item.id), label: item.name }))
  //  Dòng gán cũ có thể trỏ vào mẫu đã tắt (không còn trong danh sách) — vẫn phải
  //  hiện ra, không thì ô trống và người sửa tưởng chưa chọn.
  const withCurrent =
    value && !options.some((o) => o.value === value)
      ? [{ value, label: `Mẫu #${value}` }, ...options]
      : options

  return (
    <div className="space-y-1.5">
      <Label htmlFor={name}>
        Mẫu lịch
        <RequiredMark />
      </Label>
      {disabled ? (
        <ReadOnlyValue>{withCurrent.find((o) => o.value === value)?.label ?? ''}</ReadOnlyValue>
      ) : (
        <Select
          value={value}
          disabled={isLoading}
          onValueChange={(next) => {
            //  Chuỗi rỗng là nhịp đồng bộ của thẻ select ẩn Radix, không phải người chọn.
            if (next === '') return
            field.onChange(Number(next))
          }}
        >
          <SelectTrigger id={name} className="w-full">
            <SelectValue placeholder="Chọn mẫu lịch" />
          </SelectTrigger>
          <SelectContent>
            {withCurrent.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
      {fieldState.error?.message && (
        <p role="alert" className="text-xs text-destructive">
          {fieldState.error.message}
        </p>
      )}
      {isError && (
        <p className="text-xs text-destructive">Không tải được danh sách mẫu lịch.</p>
      )}
      {!isLoading && !isError && options.length === 0 && (
        <p className="text-xs text-muted-foreground">
          Chưa có mẫu lịch đang dùng — tạo ở mục «Mẫu lịch tuần» trước.
        </p>
      )}
    </div>
  )
}
