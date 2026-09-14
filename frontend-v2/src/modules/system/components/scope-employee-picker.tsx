import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import type { Employee } from '../types/employee'
import { ScopeChip } from './scope-chip'

interface ScopeEmployeePickerProps {
  /** ID nhân sự đang chọn. Rỗng = không giới hạn theo nhân sự. */
  selected: number[]
  onChange: (ids: number[]) => void
  employees: Employee[]
  /** Câu mô tả khi chưa bật giới hạn. */
  idleHint: string
  /** Chữ trên nút bỏ giới hạn. */
  clearLabel: string
  danger?: boolean
}

/**
 * Chọn nhân sự cho một chiều của phạm vi dữ liệu.
 *
 * Danh sách nhân sự cả công ty quá dài để bày hết thành chip, nên mặc định
 * component ở trạng thái "không giới hạn"; bấm Tùy chỉnh mới hiện ô tìm kiếm.
 * Trạng thái bật/tắt suy ra từ chính `selected` — không giữ cờ riêng, tránh
 * cảnh mảng đã rỗng mà giao diện vẫn báo đang giới hạn.
 */
export function ScopeEmployeePicker({
  selected,
  onChange,
  employees,
  idleHint,
  clearLabel,
  danger,
}: ScopeEmployeePickerProps) {
  const [customizing, setCustomizing] = useState(selected.length > 0)
  const [keyword, setKeyword] = useState('')

  const labelOf = (id: number) => {
    const employee = employees.find((item) => item.id === id)
    return employee ? `${employee.code} — ${employee.full_name}` : String(id)
  }

  const matches = keyword
    ? employees
        .filter((employee) =>
          `${employee.code} ${employee.full_name}`
            .toLowerCase()
            .includes(keyword.toLowerCase()),
        )
        .slice(0, 40)
    : []

  const toggle = (id: number) =>
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id])

  if (!customizing) {
    return (
      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm text-muted-foreground">{idleHint}</span>
        <Button type="button" variant="outline" size="sm" onClick={() => setCustomizing(true)}>
          Tùy chỉnh
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <span className="text-xs text-muted-foreground">
          Gõ mã hoặc tên để tìm và chọn nhân sự.
        </span>
        <button
          type="button"
          className="text-xs text-destructive hover:underline"
          onClick={() => {
            setCustomizing(false)
            setKeyword('')
            onChange([])
          }}
        >
          {clearLabel}
        </button>
      </div>

      {selected.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {selected.map((id) => (
            <ScopeChip
              key={id}
              label={labelOf(id)}
              active
              danger={danger}
              onToggle={() => toggle(id)}
            />
          ))}
        </div>
      )}

      <Input
        placeholder="Gõ mã / tên để tìm nhân sự…"
        value={keyword}
        onChange={(e) => setKeyword(e.target.value)}
      />

      {keyword && (
        <div className="flex max-h-40 flex-wrap gap-1.5 overflow-y-auto">
          {matches.length === 0 ? (
            <span className="text-xs text-muted-foreground">Không tìm thấy nhân sự nào.</span>
          ) : (
            matches.map((employee) => (
              <ScopeChip
                key={employee.id}
                label={`${employee.code} — ${employee.full_name}`}
                active={selected.includes(employee.id)}
                danger={danger}
                onToggle={() => toggle(employee.id)}
              />
            ))
          )}
        </div>
      )}
    </div>
  )
}
