import { useState } from 'react'

import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'
import { dueTone, dueToneClass, formatDueLabel } from '../utils/due-date'
import type { WorkTask } from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'

interface TaskSubtaskListProps {
  subtasks: WorkTask[]
  canEdit: boolean
  onToggle: (subtaskId: number, done: boolean) => void
  onAdd: (title: string) => void
}

/**
 * Khối việc con trong panel chi tiết (C-01, C-02).
 *
 * Việc con chỉ sống ở đây — không thành thẻ trên kanban, không thành dòng ở
 * khung nhìn danh sách (C-05/Q10). Thanh tiến độ dùng chính `n/m` đếm được từ
 * danh sách này, không hỏi thêm máy chủ.
 *
 * Bố cục theo Lark: `n/m` và thanh tiến độ nằm CÙNG MỘT HÀNG ở đầu khối (bản cũ
 * để tiêu đề «Việc con» một hàng, số một góc, thanh một hàng nữa — ba hàng cho
 * một con số), mỗi việc con hiện kèm hạn riêng của nó.
 */
export function TaskSubtaskList({ subtasks, canEdit, onToggle, onAdd }: TaskSubtaskListProps) {
  const [dangThem, setDangThem] = useState(false)
  const [tieuDe, setTieuDe] = useState('')

  const xong = subtasks.filter((s) => s.status === WORK_TASK_STATUS.DONE).length
  const tong = subtasks.length
  const phanTram = tong ? Math.round((xong / tong) * 100) : 0

  function luu() {
    const value = tieuDe.trim()
    if (!value) {
      setDangThem(false)
      return
    }
    onAdd(value)
    setTieuDe('')
  }

  return (
    <div className="w-full space-y-1.5">
      {/*  Chưa có việc con nào thì KHÔNG vẽ «0 / 0» với một vạch xám rỗng: nó
           không nói thêm điều gì mà lại chiếm đúng chỗ dễ thấy nhất của khối. */}
      {tong > 0 && (
        <div className="flex h-7 items-center gap-2">
          <span className="text-sm text-muted-foreground tabular-nums">
            {xong} / {tong}
          </span>
          <span className="h-1.5 w-28 overflow-hidden rounded-full bg-muted">
            <span
              className={cn(
                'block h-full transition-all',
                phanTram === 100 ? 'bg-emerald-500' : 'bg-primary',
              )}
              style={{ width: `${phanTram}%` }}
            />
          </span>
        </div>
      )}

      <ul className="space-y-0.5">
        {subtasks.map((s) => {
          const daXong = s.status === WORK_TASK_STATUS.DONE
          return (
            <li key={s.id} className="flex items-center gap-2 rounded-md py-1 hover:bg-accent/50">
              <Checkbox
                id={`subtask-${s.id}`}
                className="rounded-full"
                checked={daXong}
                disabled={!canEdit}
                onCheckedChange={(checked) => onToggle(s.id, checked === true)}
              />
              <label
                htmlFor={`subtask-${s.id}`}
                className={cn(
                  'flex-1 truncate text-sm',
                  canEdit && 'cursor-pointer',
                  daXong && 'text-muted-foreground line-through',
                )}
              >
                {s.title}
              </label>
              {s.due_date && (
                <span className={cn('shrink-0 text-xs', dueToneClass(dueTone(s.due_date, daXong)))}>
                  {formatDueLabel(s.due_date)}
                </span>
              )}
            </li>
          )
        })}
      </ul>

      {canEdit &&
        (dangThem ? (
          <Input
            autoFocus
            value={tieuDe}
            placeholder="Tên việc con rồi Enter"
            onChange={(e) => setTieuDe(e.target.value)}
            onBlur={luu}
            onKeyDown={(e) => {
              if (e.key === 'Enter') luu()
              if (e.key === 'Escape') setDangThem(false)
            }}
          />
        ) : (
          //  Không có dấu `+` ở đây: máng trái của hàng đã mang biểu tượng
          //  «việc con» rồi, và dòng này phải bắt đầu ĐÚNG cùng mốc với «Thêm
          //  đính kèm» ngay dưới — thêm một ký tự là hai dòng so le (khách đối
          //  chiếu Lark 03/09/2026).
          <button
            type="button"
            onClick={() => setDangThem(true)}
            className="flex items-center rounded-md px-1 py-1 text-sm text-muted-foreground hover:text-foreground"
          >
            Thêm việc con
          </button>
        ))}
    </div>
  )
}
