import { Plus, UserPlus, X } from 'lucide-react'
import { useMemo, useState } from 'react'

import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'
import type { WorkAssignee, WorkMember } from '../types/work'
import { WORK_ASSIGNEE_KIND } from '../types/work'
import { initials, personName } from '../utils/people'
import { AssigneePickerList } from './assignee-picker-list'

interface TaskAssigneePickerProps {
  assignees: WorkAssignee[]
  members: WorkMember[]
  disabled?: boolean
  /**
   * `true` = dáng MỘT DÒNG cho ô bảng ở khung nhìn Danh sách: avatar chồng nhau
   * + tên người đầu, cả cụm là nút mở danh sách. Dáng mặc định (dải chip có nút
   * ✕ riêng từng người + nút «+») cao gấp đôi và xuống dòng trong ô hẹp.
   */
  compact?: boolean
  onChange: (picIds: number[]) => void
}

/**
 * Người phụ trách: chip avatar của những người ĐANG được gán, cộng một nút mở
 * danh sách có ô tìm.
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
  compact = false,
  onChange,
}: TaskAssigneePickerProps) {
  const [open, setOpen] = useState(false)

  const picked = useMemo(
    () => assignees.filter((a) => a.kind === WORK_ASSIGNEE_KIND.PIC),
    [assignees],
  )
  const picIds = useMemo(() => picked.map((a) => a.employee_id), [picked])

  function toggle(employeeId: number) {
    onChange(
      picIds.includes(employeeId)
        ? picIds.filter((id) => id !== employeeId)
        : [...picIds, employeeId],
    )
  }

  const list = <AssigneePickerList members={members} picIds={picIds} onToggle={toggle} />

  if (compact) {
    if (disabled) {
      return picked.length ? (
        <CompactFaces picked={picked} />
      ) : (
        <span className="text-xs text-muted-foreground">—</span>
      )
    }
    return (
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            aria-label="Gán người phụ trách"
            className="flex h-6 w-full items-center gap-1 rounded px-1 text-left hover:bg-accent"
          >
            {picked.length ? (
              <CompactFaces picked={picked} />
            ) : (
              <UserPlus className="size-3.5 text-muted-foreground opacity-0 transition-opacity group-hover/row:opacity-60" />
            )}
          </button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-72 p-0">
          {list}
        </PopoverContent>
      </Popover>
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
            {list}
          </PopoverContent>
        </Popover>
      )}
    </>
  )
}

/** Số avatar vẽ ra trước khi dồn phần còn lại vào một vòng «+N». */
const MAX_FACES = 3

/**
 * Cụm avatar chồng nhau — CHỈ avatar, không kèm tên.
 *
 * Ô bảng rộng 180px mà tên tiếng Việt đầy đủ thì một cái đã chiếm gần hết, hai
 * cái là cắt cụt cả hai thành vô nghĩa. Avatar đọc nhanh hơn hẳn khi lướt dọc
 * cả cột, và tên đầy đủ vẫn có ở `title` khi rê chuột lẫn trong popover.
 *
 * Quá {@link MAX_FACES} người thì phần dư dồn vào một vòng «+N» thay vì kéo dài
 * mãi — đúng lối avatar-group của shadcn.
 */
function CompactFaces({ picked }: { picked: WorkAssignee[] }) {
  const shown = picked.slice(0, MAX_FACES)
  const extra = picked.length - shown.length
  return (
    <span className="flex shrink-0 -space-x-1.5">
      {shown.map((a) => (
        <span
          key={a.employee_id}
          title={personName(a.employee_name, a.employee_id)}
          className="grid size-5 place-items-center rounded-full bg-muted text-[9px] font-medium ring-1 ring-background"
        >
          {initials(a.employee_name)}
        </span>
      ))}
      {extra > 0 && (
        <span
          title={picked
            .slice(MAX_FACES)
            .map((a) => personName(a.employee_name, a.employee_id))
            .join(', ')}
          className="grid size-5 place-items-center rounded-full bg-muted text-[9px] font-medium text-muted-foreground ring-1 ring-background"
        >
          +{extra}
        </span>
      )}
    </span>
  )
}
