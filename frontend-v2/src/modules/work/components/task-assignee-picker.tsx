import { Check, Plus, Search, X } from 'lucide-react'
import { useMemo, useState } from 'react'

import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { Input } from '@/shared/ui/input'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import type { WorkAssignee, WorkMember } from '../types/work'
import { WORK_ASSIGNEE_KIND } from '../types/work'
import { initials, personName } from '../utils/people'

interface TaskAssigneePickerProps {
  assignees: WorkAssignee[]
  members: WorkMember[]
  disabled?: boolean
  onChange: (picIds: number[]) => void
}

/**
 * Người phụ trách trong panel chi tiết: chip avatar của những người ĐANG được
 * gán, cộng một nút «+» mở danh sách có ô tìm.
 *
 * Bản cũ bày THẲNG mọi thành viên dự án thành một dải nút bật/tắt. Dự án hai
 * mươi người là hai mươi nút xám phủ kín panel, mà thứ cần đọc — "ai đang làm
 * việc này" — lại chìm trong đó. Kiểu Lark: chỉ hiện người đã chọn, muốn đổi
 * thì mở danh sách.
 */
export function TaskAssigneePicker({
  assignees,
  members,
  disabled,
  onChange,
}: TaskAssigneePickerProps) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')

  const picIds = useMemo(
    () => assignees.filter((a) => a.kind === WORK_ASSIGNEE_KIND.PIC).map((a) => a.employee_id),
    [assignees],
  )
  const picked = useMemo(
    () => assignees.filter((a) => a.kind === WORK_ASSIGNEE_KIND.PIC),
    [assignees],
  )

  const matches = useMemo(() => {
    const needle = keyword.trim().toLowerCase()
    if (!needle) return members
    return members.filter((m) =>
      [m.employee_name, m.employee_code].some((f) => (f ?? '').toLowerCase().includes(needle)),
    )
  }, [members, keyword])

  function toggle(employeeId: number) {
    onChange(
      picIds.includes(employeeId)
        ? picIds.filter((id) => id !== employeeId)
        : [...picIds, employeeId],
    )
  }

  return (
    <>
      {picked.map((a) => (
        <span
          key={a.employee_id}
          className="flex items-center gap-1.5 rounded-full bg-accent py-0.5 pr-1 pl-0.5 text-sm"
        >
          <span className="grid size-6 place-items-center rounded-full bg-background text-[10px] font-medium">
            {initials(a.employee_name)}
          </span>
          <span className="max-w-40 truncate">{personName(a.employee_name, a.employee_id)}</span>
          {!disabled && (
            <IconTooltip label={`Bỏ ${personName(a.employee_name, a.employee_id)}`}>
              <button
                type="button"
                aria-label={`Bỏ ${personName(a.employee_name, a.employee_id)}`}
                onClick={() => toggle(a.employee_id)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="size-3.5" />
              </button>
            </IconTooltip>
          )}
        </span>
      ))}

      {picked.length === 0 && disabled && (
        <span className="text-sm text-muted-foreground">Chưa gán ai</span>
      )}

      {!disabled && (
        <Popover open={open} onOpenChange={setOpen}>
          <IconTooltip label="Gán người phụ trách">
            <PopoverTrigger asChild>
              <button
                type="button"
                aria-label="Gán người phụ trách"
                className={cn(
                  'flex items-center gap-1 rounded-full border border-dashed px-2 py-1 text-sm text-muted-foreground',
                  'hover:border-solid hover:bg-accent hover:text-foreground',
                )}
              >
                <Plus className="size-3.5" />
                {picked.length === 0 && 'Gán người'}
              </button>
            </PopoverTrigger>
          </IconTooltip>
          <PopoverContent align="start" className="w-72 p-0">
            <div className="border-b p-2">
              <div className="relative">
                <Search className="absolute top-2.5 left-2 size-4 text-muted-foreground" />
                <Input
                  autoFocus
                  className="pl-8"
                  placeholder="Tìm theo tên hoặc mã"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                />
              </div>
            </div>
            <div className="max-h-64 overflow-y-auto p-1">
              {matches.length === 0 && (
                <p className="px-2 py-4 text-center text-sm text-muted-foreground">
                  {members.length === 0
                    ? 'Dự án chưa có thành viên nào'
                    : 'Không tìm thấy ai khớp'}
                </p>
              )}
              {matches.map((m) => {
                const chosen = picIds.includes(m.employee_id)
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => toggle(m.employee_id)}
                    className={cn(
                      'flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent',
                      chosen && 'bg-accent/50',
                    )}
                  >
                    <Check className={cn('size-4 shrink-0', !chosen && 'invisible')} />
                    <span className="grid size-6 shrink-0 place-items-center rounded-full bg-muted text-[10px] font-medium">
                      {initials(m.employee_name)}
                    </span>
                    <span className="flex-1 truncate">
                      {personName(m.employee_name, m.employee_id)}
                    </span>
                    {m.employee_code && (
                      <span className="shrink-0 text-xs text-muted-foreground">
                        {m.employee_code}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>
          </PopoverContent>
        </Popover>
      )}
    </>
  )
}
