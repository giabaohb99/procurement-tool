import { useState } from 'react'

import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'

/**
 * Hai ô CHỮ của panel chi tiết — tiêu đề và mô tả. Chúng là chỗ duy nhất trong
 * panel giữ bản nháp cục bộ, nên tách riêng để nơi gọi gắn `key={task.id}`:
 * đổi việc là component dựng lại, state khởi tạo lại từ đầu.
 *
 * Cách cũ — `useEffect` gọi `setState` khi task đổi — bị
 * `react-hooks/set-state-in-effect` chặn, mà chặn đúng: nó thêm một vòng render
 * và có một nhịp panel hiện chữ của việc TRƯỚC.
 *
 * Cả hai LƯU KHI RỜI Ô, không có nút Lưu: đây là chỗ sửa nhanh cạnh bảng.
 */

interface TaskTitleFieldProps {
  title: string
  canEdit: boolean
  strike: boolean
  onSave: (title: string) => void
}

export function TaskTitleField({ title, canEdit, strike, onSave }: TaskTitleFieldProps) {
  const [gia, setGia] = useState(title)

  //  Chỉ xem thì hiện CHỮ, không phải `<Input disabled>`: ô disabled không cho
  //  bôi đen/copy và bị làm mờ nên nhìn như chữ gợi ý.
  if (!canEdit) {
    return <p className={cn('flex-1 text-lg font-semibold', strike && 'line-through')}>{title}</p>
  }

  return (
    <Input
      value={gia}
      onChange={(e) => setGia(e.target.value)}
      onBlur={() => gia.trim() && gia !== title && onSave(gia)}
      className={cn(
        'h-auto border-0 px-0 text-lg font-semibold shadow-none',
        strike && 'line-through',
      )}
    />
  )
}

interface TaskDescriptionFieldProps {
  description: string
  canEdit: boolean
  onSave: (description: string) => void
}

export function TaskDescriptionField({
  description,
  canEdit,
  onSave,
}: TaskDescriptionFieldProps) {
  const [gia, setGia] = useState(description)

  return (
    <div className="space-y-1.5">
      <Label className="text-xs text-muted-foreground">Mô tả</Label>
      {canEdit ? (
        <Textarea
          rows={4}
          value={gia}
          onChange={(e) => setGia(e.target.value)}
          onBlur={() => gia !== description && onSave(gia)}
        />
      ) : (
        <ReadOnlyValue multiline>{description}</ReadOnlyValue>
      )}
    </div>
  )
}
