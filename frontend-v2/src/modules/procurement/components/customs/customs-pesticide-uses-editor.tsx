// Bảng nhập PHẠM VI SỬ DỤNG trong hộp thêm / sửa thuốc BVTV (duoc-CR-490): mỗi dòng một cặp
// cây trồng – dịch hại kèm liều, thời gian cách ly, cách dùng. Lưu là thay TOÀN BỘ phạm vi.
//
// ⚠️ Ô con nằm trong `<form>` của hộp thoại: Enter trong ô một dòng phải bị chặn, không thì gõ dở
// một dòng, nhấn Enter là form LƯU cả thuốc (bẫy thứ hai của duoc-CR-317). Mọi nút `type="button"`.
import { Plus, Trash2 } from 'lucide-react'
import type { KeyboardEvent } from 'react'

import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import { Textarea } from '@/shared/ui/textarea'

import type { CustomsPesticideUseInput } from '../../types/customs-pesticide'
import {
  emptyPesticideUse,
  MAX_PESTICIDE_USES,
  PESTICIDE_USE_LIMITS,
} from '../../utils/customs-pesticide-form'

const SHORT_FIELDS = [
  { key: 'crop', label: 'Cây trồng' },
  { key: 'pest', label: 'Dịch hại' },
  { key: 'dosage', label: 'Liều lượng' },
  { key: 'pre_harvest_interval', label: 'Thời gian cách ly' },
] as const

function blockEnter(event: KeyboardEvent<HTMLInputElement>) {
  if (event.key === 'Enter') event.preventDefault()
}

interface CustomsPesticideUsesEditorProps {
  uses: CustomsPesticideUseInput[]
  onChange: (uses: CustomsPesticideUseInput[]) => void
  disabled?: boolean
}

export function CustomsPesticideUsesEditor({ uses, onChange, disabled }: CustomsPesticideUsesEditorProps) {
  function patch(index: number, changes: Partial<CustomsPesticideUseInput>) {
    onChange(uses.map((use, i) => (i === index ? { ...use, ...changes } : use)))
  }

  return (
    <section className="space-y-2">
      <div className="flex items-center justify-between gap-2">
        <h3 className="text-sm font-semibold">Phạm vi sử dụng ({uses.length})</h3>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={disabled || uses.length >= MAX_PESTICIDE_USES}
          onClick={() => onChange([...uses, emptyPesticideUse()])}
        >
          <Plus className="size-4" />
          Thêm dòng
        </Button>
      </div>
      {uses.length === 0 && (
        <p className="text-sm text-muted-foreground">Chưa có dòng phạm vi sử dụng nào.</p>
      )}
      {uses.map((use, index) => (
        <div key={index} className="space-y-2 rounded-md border p-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-muted-foreground">Dòng {index + 1}</span>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="size-7 text-destructive hover:text-destructive"
              aria-label={`Xóa dòng phạm vi ${index + 1}`}
              disabled={disabled}
              onClick={() => onChange(uses.filter((_, i) => i !== index))}
            >
              <Trash2 className="size-4" />
            </Button>
          </div>
          <div className="grid gap-2 sm:grid-cols-4">
            {SHORT_FIELDS.map((field) => (
              <Input
                key={field.key}
                aria-label={`${field.label} — dòng ${index + 1}`}
                placeholder={field.label}
                value={use[field.key]}
                maxLength={PESTICIDE_USE_LIMITS[field.key]}
                disabled={disabled}
                onKeyDown={blockEnter}
                onChange={(event) => patch(index, { [field.key]: event.target.value })}
              />
            ))}
          </div>
          <Textarea
            aria-label={`Cách dùng — dòng ${index + 1}`}
            placeholder="Cách dùng"
            rows={2}
            value={use.usage}
            maxLength={PESTICIDE_USE_LIMITS.usage}
            disabled={disabled}
            onChange={(event) => patch(index, { usage: event.target.value })}
          />
        </div>
      ))}
    </section>
  )
}
