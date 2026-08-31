import { useState } from 'react'

import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'

interface TaskTitleCellProps {
  title: string
  done: boolean
  canEdit: boolean
  onRename: (title: string) => void
}

/**
 * Tên việc SỬA ĐƯỢC ngay trên dòng danh sách (kiểu Lark).
 *
 * Một cú bấm vào chữ là thành ô nhập tại chỗ; Enter hoặc rời ô thì lưu, Esc thì
 * bỏ. Bấm ra chỗ khác trong dòng vẫn mở panel chi tiết như cũ — nên nút này
 * `stopPropagation`, không thì vừa vào chế độ sửa đã bị panel che mất.
 *
 * Hai luật giữ dữ liệu: tên rỗng thì **giữ nguyên tên cũ** (xóa sạch rồi Enter
 * là lỡ tay, không phải ý muốn đặt tên rỗng), và tên không đổi thì không gọi
 * API — mỗi lần rời ô mà cũng bắn một lượt PATCH thì nhật ký thao tác đầy rác.
 */
export function TaskTitleCell({ title, done, canEdit, onRename }: TaskTitleCellProps) {
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState(title)

  function save() {
    const value = draft.trim()
    if (value && value !== title) onRename(value)
    else setDraft(title)
    setEditing(false)
  }

  if (editing) {
    return (
      <Input
        autoFocus
        value={draft}
        aria-label="Tên công việc"
        /*  Không viền, không vòng sáng — y như dòng soạn việc mới. Ô nhập ở đây
            NẰM ĐÈ lên chỗ chữ vừa bấm, nên một cái hộp viền hiện ra làm cả dòng
            giật một nhịp và trông như vừa mở ra một biểu mẫu khác. Con trỏ nháy
            đã đủ nói "đang sửa". `dark:bg-transparent` vì `Input` gốc có
            `dark:bg-input/30`, để nguyên là nền tối lại hiện đúng cái hộp ấy. */
        className="h-6 min-w-0 flex-1 border-0 bg-transparent px-1 py-0 text-sm shadow-none focus-visible:ring-0 dark:bg-transparent"
        onClick={(e) => e.stopPropagation()}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={save}
        onKeyDown={(e) => {
          e.stopPropagation()
          if (e.key === 'Enter') save()
          if (e.key === 'Escape') {
            setDraft(title)
            setEditing(false)
          }
        }}
      />
    )
  }

  return (
    <span
      role={canEdit ? 'button' : undefined}
      tabIndex={canEdit ? 0 : undefined}
      title={title}
      onClick={
        canEdit
          ? (e) => {
              e.stopPropagation()
              setDraft(title)
              setEditing(true)
            }
          : undefined
      }
      onKeyDown={
        canEdit
          ? (e) => {
              if (e.key !== 'Enter') return
              e.stopPropagation()
              setDraft(title)
              setEditing(true)
            }
          : undefined
      }
      /*  KHÔNG `flex-1`: ô tên chỉ rộng bằng chữ của nó, phần trống còn lại của
          dòng để dành cho cú bấm MỞ PANEL chi tiết. Cho nó giãn hết dòng thì
          bấm chỗ nào cũng rơi vào chế độ sửa tên và không còn đường nào mở chi
          tiết ngoài mấy khe hở vài pixel.  */
      className={cn(
        'min-w-0 shrink truncate rounded px-1 py-0.5 text-left text-sm',
        canEdit && 'cursor-text hover:bg-accent/60',
        done && 'text-muted-foreground line-through',
      )}
    >
      {title}
    </span>
  )
}
