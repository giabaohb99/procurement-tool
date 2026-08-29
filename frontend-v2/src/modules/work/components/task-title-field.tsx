import { useState } from 'react'

import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'

/**
 * Ô TIÊU ĐỀ của panel chi tiết. Nó giữ bản nháp cục bộ, nên nơi gọi phải gắn
 * `key={task.id}`: đổi việc là component dựng lại, state khởi tạo lại từ đầu.
 *
 * Cách cũ — `useEffect` gọi `setState` khi task đổi — bị
 * `react-hooks/set-state-in-effect` chặn, mà chặn đúng: nó thêm một vòng render
 * và có một nhịp panel hiện chữ của việc TRƯỚC.
 *
 * LƯU KHI RỜI Ô, không có nút Lưu: đây là chỗ sửa nhanh cạnh bảng. Ô mô tả
 * nằm ở `task-description-field.tsx` — nó là trình soạn thảo rich text nên
 * chốt lưu bằng cú bấm ra ngoài chứ không bằng `blur`.
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
    return (
      <h2 className={cn('text-xl leading-snug font-semibold', strike && 'line-through')}>
        {title}
      </h2>
    )
  }

  return (
    <Input
      value={gia}
      aria-label="Tiêu đề công việc"
      onChange={(e) => setGia(e.target.value)}
      onBlur={() => gia.trim() && gia !== title && onSave(gia)}
      //  Ô nhập trông như CHỮ cho tới khi rê chuột vào: tiêu đề là thứ đọc
      //  nhiều hơn sửa, đóng khung sẵn thì panel mở ra đã thấy một ô biểu mẫu.
      className={cn(
        //  `dark:bg-transparent` vì `Input` gốc có `dark:bg-input/30` — bỏ sót
        //  thì ở nền tối tiêu đề nằm trong một hộp xám.
        'h-auto border-0 bg-transparent px-1.5 py-1 text-xl font-semibold shadow-none dark:bg-transparent',
        'hover:bg-accent/60 focus-visible:bg-background focus-visible:ring-[3px] dark:focus-visible:bg-input/30',
        strike && 'line-through',
      )}
    />
  )
}
