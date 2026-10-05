import { useController, type Control } from 'react-hook-form'

import { WORK_SCHEDULE_LEVEL } from '@/shared/constants/statuses'
import type { CrudRecord } from '@/shared/crud'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { SYSTEM_LEVEL_LABEL } from '../types/work-schedule'
import { isChosenId } from '../utils/work-schedule-validation'

interface WorkScheduleLevelFieldProps {
  control: Control<CrudRecord>
  /** Tên ô cấp trong form (`target_level`). */
  name: string
  /** Tên ô đối tượng đi kèm (`target_id`) — bị xóa mỗi khi cấp đổi. */
  idName: string
  disabled?: boolean
}

/**
 * Ô «Cấp áp dụng». Đổi cấp thì **xóa luôn đối tượng đã chọn** (về 0) trong cùng
 * một lần bấm: giữ `target_id` cũ là gán nhầm — nhân sự #12 bỗng thành pháp nhân
 * #12. Cố ý làm trong handler chứ không bằng effect theo dõi cấp, vì effect đó
 * cũng chạy khi form nạp bản ghi có sẵn và sẽ xóa mất đối tượng của chính bản ghi.
 */
export function WorkScheduleLevelField({
  control,
  name,
  idName,
  disabled = false,
}: WorkScheduleLevelFieldProps) {
  const { field: level, fieldState } = useController({
    control,
    name,
    rules: { validate: (value) => isChosenId(value) || 'Chọn cấp áp dụng.' },
  })
  const { field: targetId } = useController({ control, name: idName })
  const current = String(level.value ?? '')
  const selected = WORK_SCHEDULE_LEVEL.find((option) => option.value === current)

  return (
    <div className="space-y-1.5">
      <Label htmlFor={name}>
        Cấp áp dụng
        <RequiredMark />
      </Label>
      {disabled ? (
        <ReadOnlyValue>{selected?.label ?? ''}</ReadOnlyValue>
      ) : (
        <Select
          value={selected ? current : ''}
          onValueChange={(value) => {
            //  Chuỗi rỗng là nhịp đồng bộ của thẻ select ẩn Radix, không phải người chọn.
            if (value === '' || value === current) return
            level.onChange(Number(value))
            targetId.onChange(0)
          }}
        >
          <SelectTrigger id={name} className="w-full">
            <SelectValue placeholder="Chọn cấp áp dụng" />
          </SelectTrigger>
          <SelectContent>
            {WORK_SCHEDULE_LEVEL.map((option) => (
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
      <p className="text-xs text-muted-foreground">
        Hẹp thắng rộng: Nhân sự &gt; Phòng ban &gt; Pháp nhân &gt; {SYSTEM_LEVEL_LABEL}. Chưa gán gì thì
        dùng T2–T7, 08:00–17:00.
      </p>
    </div>
  )
}
