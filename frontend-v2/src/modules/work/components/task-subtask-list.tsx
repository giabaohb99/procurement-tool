import { Plus } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'
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
    <section className="space-y-2">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Việc con</h3>
        <span className="text-xs text-muted-foreground">
          {xong}/{tong}
        </span>
      </div>

      {tong > 0 && (
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div className="h-full bg-primary transition-all" style={{ width: `${phanTram}%` }} />
        </div>
      )}

      <ul className="space-y-1">
        {subtasks.map((s) => {
          const daXong = s.status === WORK_TASK_STATUS.DONE
          return (
            <li key={s.id} className="flex items-center gap-2">
              <Checkbox
                id={`subtask-${s.id}`}
                checked={daXong}
                disabled={!canEdit}
                onCheckedChange={(checked) => onToggle(s.id, checked === true)}
              />
              <label
                htmlFor={`subtask-${s.id}`}
                className={cn('text-sm', daXong && 'text-muted-foreground line-through')}
              >
                {s.title}
              </label>
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
          <Button
            variant="ghost"
            size="sm"
            className="justify-start text-muted-foreground"
            onClick={() => setDangThem(true)}
          >
            <Plus className="size-4" />
            Thêm việc con
          </Button>
        ))}
    </section>
  )
}
