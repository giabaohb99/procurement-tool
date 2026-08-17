import type { ReactNode } from 'react'

import { Checkbox } from '@/shared/ui/checkbox'
import { Label } from '@/shared/ui/label'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'

/**
 * Khối "áp dụng cho" của quy tắc đánh số — dùng chung cho cả loại văn bản và sổ.
 *
 * Cố ý để **thuần trình bày**: nhận giá trị và trả thay đổi qua props, không
 * đụng vào react-hook-form. Nhờ vậy form chính giữ được toàn bộ phần khai báo
 * trường ở một chỗ, và khối này đem dùng lại được ở chỗ khác nếu cần.
 */

/** Đủ dùng cho cả `DocumentType` lẫn `DocumentBook` — hai bên đều có ba trường này. */
export interface ScopeItem {
  id: number
  code: string
  name: string
}

export function ScopeModeCard({
  title,
  name,
  options,
  mode,
  onModeChange,
  children,
}: {
  title: string
  /** Tiền tố id của radio — phải khác nhau giữa các khối trên cùng trang. */
  name: string
  options: Array<{ value: number; label: string }>
  mode: number
  onModeChange: (mode: number) => void
  children?: ReactNode
}) {
  return (
    <div className="space-y-3 rounded-lg border p-4">
      <h4 className="font-medium">{title}</h4>
      <RadioGroup value={String(mode)} onValueChange={(value) => onModeChange(Number(value))}>
        {options.map((option) => (
          <Label
            key={option.value}
            htmlFor={`${name}-${option.value}`}
            className="font-normal"
          >
            <RadioGroupItem id={`${name}-${option.value}`} value={String(option.value)} />
            {option.label}
          </Label>
        ))}
      </RadioGroup>
      {children}
    </div>
  )
}

export function ScopeChecklist({
  name,
  items,
  selected,
  onChange,
  emptyLabel = 'Không có dữ liệu để chọn.',
}: {
  name: string
  items: ScopeItem[]
  selected: number[]
  onChange: (ids: number[]) => void
  emptyLabel?: string
}) {
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">{emptyLabel}</p>
  }

  return (
    <div className="max-h-44 space-y-1 overflow-y-auto rounded-md border p-2">
      {items.map((item) => (
        <Label
          key={item.id}
          // Khóa theo `name` + id: hai khối trên cùng trang có thể trùng id
          // (loại văn bản 3 và sổ 3), dùng chung htmlFor thì bấm ô này tick ô kia.
          htmlFor={`${name}-item-${item.id}`}
          className="rounded px-2 py-2 font-normal hover:bg-muted"
        >
          <Checkbox
            id={`${name}-item-${item.id}`}
            checked={selected.includes(item.id)}
            onCheckedChange={(value) =>
              onChange(
                value === true
                  ? [...selected, item.id]
                  : selected.filter((id) => id !== item.id),
              )
            }
          />
          <span className="truncate">
            {item.code} · {item.name}
          </span>
        </Label>
      ))}
    </div>
  )
}
