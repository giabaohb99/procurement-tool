import { Check, Search } from 'lucide-react'
import { useMemo, useState } from 'react'

import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'
import type { WorkMember } from '../types/work'
import { initials, personName } from '../utils/people'

interface AssigneePickerListProps {
  members: WorkMember[]
  picIds: number[]
  onToggle: (employeeId: number) => void
}

/**
 * Ruột popover chọn người phụ trách: ô tìm + danh sách thành viên có dấu tick.
 *
 * Tách khỏi `TaskAssigneePicker` vì component đó nay có HAI dáng nút bấm (dải
 * chip cho panel chi tiết, một dòng gọn cho ô bảng danh sách) mà cùng dùng đúng
 * một danh sách này — để chung một tệp thì nó vượt ngưỡng 200 dòng và phần khó
 * đọc nhất bị kẹp giữa hai nhánh dựng hình.
 */
export function AssigneePickerList({ members, picIds, onToggle }: AssigneePickerListProps) {
  const [keyword, setKeyword] = useState('')

  const matches = useMemo(() => {
    const needle = keyword.trim().toLowerCase()
    if (!needle) return members
    return members.filter((m) =>
      [m.employee_name, m.employee_code].some((f) => (f ?? '').toLowerCase().includes(needle)),
    )
  }, [members, keyword])

  return (
    <>
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
            {members.length === 0 ? 'Dự án chưa có thành viên nào' : 'Không tìm thấy ai khớp'}
          </p>
        )}
        {matches.map((m) => {
          const chosen = picIds.includes(m.employee_id)
          return (
            <button
              key={m.id}
              type="button"
              onClick={() => onToggle(m.employee_id)}
              className={cn(
                'flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent',
                chosen && 'bg-accent/50',
              )}
            >
              <Check className={cn('size-4 shrink-0', !chosen && 'invisible')} />
              <span className="grid size-6 shrink-0 place-items-center rounded-full bg-muted text-[10px] font-medium">
                {initials(m.employee_name)}
              </span>
              <span className="flex-1 truncate">{personName(m.employee_name, m.employee_id)}</span>
              {m.employee_code && (
                <span className="shrink-0 text-xs text-muted-foreground">{m.employee_code}</span>
              )}
            </button>
          )
        })}
      </div>
    </>
  )
}
