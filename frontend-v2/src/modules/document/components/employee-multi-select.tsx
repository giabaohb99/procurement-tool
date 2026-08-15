import { Check, Search, X } from 'lucide-react'
import { useMemo, useState } from 'react'

import type { Employee } from '@/modules/hr/types/employee'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/shared/ui/popover'
import { cn } from '@/shared/utils/cn'

interface EmployeeMultiSelectProps {
  /** ID nhân sự đang chọn. */
  value: number[]
  onChange: (ids: number[]) => void
  employees: Employee[]
  placeholder: string
  disabled?: boolean
}

/** Số dòng tối đa trong danh sách thả xuống — dài hơn thì bắt gõ tìm. */
const MAX_VISIBLE = 50

/**
 * Chọn NHIỀU nhân sự — dùng cho người quản lý sổ và người xem sổ.
 *
 * Không dùng `ScopeEmployeePicker` của phân hệ Nhân sự: component đó mang thêm
 * ngữ nghĩa "không giới hạn / tùy chỉnh" của phạm vi dữ liệu, ở đây danh sách
 * rỗng chỉ đơn giản là chưa cử ai chứ không có nghĩa "mọi người".
 */
export function EmployeeMultiSelect({
  value,
  onChange,
  employees,
  placeholder,
  disabled,
}: EmployeeMultiSelectProps) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')

  const selected = useMemo(
    () => value.map((id) => employees.find((e) => e.id === id)).filter(Boolean) as Employee[],
    [value, employees],
  )

  const matches = useMemo(() => {
    const needle = keyword.trim().toLowerCase()
    const rows = needle
      ? employees.filter((e) =>
          [e.full_name, e.code, e.position].some((field) =>
            (field ?? '').toLowerCase().includes(needle),
          ),
        )
      : employees
    return rows.slice(0, MAX_VISIBLE)
  }, [employees, keyword])

  function toggle(id: number) {
    onChange(value.includes(id) ? value.filter((item) => item !== id) : [...value, id])
  }

  return (
    <div className="space-y-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            type="button"
            variant="outline"
            disabled={disabled}
            className="w-full justify-start font-normal text-muted-foreground"
          >
            <Search className="size-4" />
            {placeholder}
          </Button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-80 p-0">
          <div className="border-b p-2">
            <Input
              autoFocus
              placeholder="Tìm theo tên, mã hoặc chức danh…"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
            />
          </div>
          <div className="max-h-72 overflow-y-auto p-1">
            {matches.length === 0 && (
              <p className="px-2 py-4 text-center text-sm text-muted-foreground">
                Không tìm thấy nhân sự nào.
              </p>
            )}
            {matches.map((employee) => {
              const checked = value.includes(employee.id)
              return (
                <button
                  key={employee.id}
                  type="button"
                  onClick={() => toggle(employee.id)}
                  className={cn(
                    'flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-left text-sm hover:bg-accent',
                    checked && 'bg-accent/50',
                  )}
                >
                  <Check
                    className={cn('size-4 shrink-0', !checked && 'invisible')}
                  />
                  <span className="flex-1 truncate">{employee.full_name}</span>
                  <span className="shrink-0 text-xs text-muted-foreground">
                    {employee.code}
                  </span>
                </button>
              )
            })}
          </div>
        </PopoverContent>
      </Popover>

      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {selected.map((employee) => (
            <Badge key={employee.id} variant="secondary" className="gap-1 font-normal">
              {employee.full_name}
              <button
                type="button"
                aria-label={`Bỏ ${employee.full_name}`}
                onClick={() => toggle(employee.id)}
                className="text-muted-foreground hover:text-foreground"
              >
                <X className="size-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}
