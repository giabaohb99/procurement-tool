import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { useFilterContext } from '../provider/filter-context'
import type { FilterFieldDefinition } from '../types'

export interface FieldSelectProps {
  rowId: string
  selectedField: FilterFieldDefinition | null
}

/**
 * Ô chọn cột để lọc.
 *
 * Bản FilterCN gốc dùng `cmdk` (combobox có ô tìm). Ở đây đổi sang `Select`:
 * mỗi bảng chỉ khai báo dăm bảy trường lọc được, thêm hẳn một thư viện chỉ để
 * tìm trong danh sách 8 dòng là không đáng.
 */
export function FieldSelect({ rowId, selectedField }: FieldSelectProps) {
  const { config, updateField } = useFilterContext()

  return (
    <Select
      value={selectedField?.name ?? ''}
      onValueChange={(name) => {
        const field = config.fields.find((item) => item.name === name)
        if (field) updateField(rowId, field)
      }}
    >
      <SelectTrigger className="w-44 shrink-0">
        <SelectValue placeholder="Chọn trường…" />
      </SelectTrigger>
      <SelectContent>
        {config.fields.map((field) => (
          <SelectItem key={field.name} value={field.name}>
            {field.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
