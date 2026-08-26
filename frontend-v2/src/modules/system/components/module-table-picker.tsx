import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'

import { DATA_MODULES } from '../config/data-modules'

export interface DataTableOption {
  /** Giá trị bảng (chuỗi) — import dùng số dạng chuỗi, export dùng mã entity. */
  value: string
  label: string
  /** Phân hệ chứa bảng (khớp `DATA_MODULES.id`). */
  moduleId: string
}

interface ModuleTablePickerProps {
  tables: DataTableOption[]
  value: string
  onChange: (value: string) => void
  disabled?: boolean
  /** Nhãn ô chọn bảng (mặc định "Bảng dữ liệu"). */
  tableLabel?: string
}

/**
 * Chọn dữ liệu theo hai bước: **Phân hệ** (ô bấm có icon + tên ngắn) → **Bảng dữ liệu**
 * (ô chọn xổ, chỉ các bảng thuộc phân hệ đang chọn). Dùng chung cho hộp thoại Nhập
 * và Xuất để hai màn đồng nhất.
 */
export function ModuleTablePicker({
  tables,
  value,
  onChange,
  disabled = false,
  tableLabel = 'Bảng dữ liệu',
}: ModuleTablePickerProps) {
  const presentIds = new Set(tables.map((t) => t.moduleId))
  const modules = DATA_MODULES.filter((m) => presentIds.has(m.id))

  const current = tables.find((t) => t.value === value)
  const activeModule = current?.moduleId ?? modules[0]?.id ?? ''
  const tablesInModule = tables.filter((t) => t.moduleId === activeModule)

  function pickModule(moduleId: string) {
    if (moduleId === activeModule) return
    const first = tables.find((t) => t.moduleId === moduleId)
    if (first) onChange(first.value)
  }

  return (
    <div className="space-y-3">
      <div className="space-y-1.5">
        <label className="text-sm font-semibold text-foreground">Phân hệ</label>
        {/* 4 cột mỗi hàng, các ô rộng bằng nhau; icon + chữ canh trái. */}
        <div className="grid grid-cols-4 gap-2">
          {modules.map((m) => {
            const Icon = m.icon
            const active = m.id === activeModule
            return (
              <button
                key={m.id}
                type="button"
                disabled={disabled}
                onClick={() => pickModule(m.id)}
                className={cn(
                  'flex h-9 w-full items-center justify-start gap-2 rounded-lg px-3 text-sm font-semibold transition-colors disabled:cursor-not-allowed disabled:opacity-60',
                  active
                    ? 'border-2 border-primary bg-primary/10 text-primary'
                    : 'border border-input bg-background text-muted-foreground hover:bg-accent',
                )}
              >
                <Icon className="size-4 shrink-0" />
                <span className="truncate">{m.label}</span>
              </button>
            )
          })}
        </div>
      </div>

      <div className="space-y-1.5">
        <label className="text-sm font-semibold text-foreground">{tableLabel}</label>
        <Select value={value} onValueChange={onChange} disabled={disabled}>
          <SelectTrigger className="h-10 w-full">
            <SelectValue placeholder="Chọn bảng dữ liệu" />
          </SelectTrigger>
          <SelectContent>
            {tablesInModule.map((t) => (
              <SelectItem key={t.value} value={t.value}>
                {t.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
    </div>
  )
}
