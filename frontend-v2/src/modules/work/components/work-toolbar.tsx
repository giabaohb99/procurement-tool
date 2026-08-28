import { Plus, Search, SlidersHorizontal } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Popover, PopoverContent, PopoverTrigger } from '@/shared/ui/popover'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import {
  CARD_FIELD_LABELS,
  WORK_SCOPES,
  WORK_SORTS,
  type CardFields,
  type WorkScope,
  type WorkSort,
} from '../types/view-options'

interface WorkToolbarProps {
  scope: WorkScope
  onScopeChange: (value: WorkScope) => void
  sort: WorkSort
  onSortChange: (value: WorkSort) => void
  keyword: string
  onKeywordChange: (value: string) => void
  fields: CardFields
  onFieldsChange: (fields: CardFields) => void
  canEdit: boolean
  onNewTask: () => void
}

/**
 * Thanh công cụ khung nhìn (D-07) — clone hàng nút của Lark.
 *
 * Ba thứ ở đây (lát cắt · sắp xếp · trường hiện trên thẻ) đều là **hiển thị**,
 * lọc ngay tại trình duyệt trên payload bảng đã tải: một list vài trăm việc thì
 * đi vòng máy chủ chỉ tốn thêm một nhịp chờ.
 *
 * ⚠️ CHƯA có nút «Lọc» điều kiện (`conditional-filter`) và «Gom nhóm» — hai mục
 * đó của §3.3/§3.5, để đợt sau; đừng tưởng quên.
 */
export function WorkToolbar({
  scope,
  onScopeChange,
  sort,
  onSortChange,
  keyword,
  onKeywordChange,
  fields,
  onFieldsChange,
  canEdit,
  onNewTask,
}: WorkToolbarProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      {canEdit && (
        <Button size="sm" onClick={onNewTask}>
          <Plus className="size-4" />
          Việc mới
        </Button>
      )}

      <Select value={scope} onValueChange={(v) => onScopeChange(v as WorkScope)}>
        <SelectTrigger size="sm" className="w-52">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {WORK_SCOPES.map((s) => (
            <SelectItem key={s.value} value={s.value}>
              {s.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={sort} onValueChange={(v) => onSortChange(v as WorkSort)}>
        <SelectTrigger size="sm" className="w-44">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {WORK_SORTS.map((s) => (
            <SelectItem key={s.value} value={s.value}>
              Sắp xếp: {s.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <div className="relative">
        <Search className="absolute top-1/2 left-2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          value={keyword}
          onChange={(e) => onKeywordChange(e.target.value)}
          placeholder="Tìm trong danh sách"
          className="h-8 w-56 pl-8"
        />
      </div>

      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline" size="sm">
            <SlidersHorizontal className="size-4" />
            Tùy chỉnh
          </Button>
        </PopoverTrigger>
        <PopoverContent align="end" className="w-56">
          <p className="mb-2 text-sm font-medium">Hiện trên thẻ</p>
          <div className="space-y-2">
            {CARD_FIELD_LABELS.map(({ key, label }) => (
              <div key={key} className="flex items-center gap-2">
                <Checkbox
                  id={`field-${key}`}
                  checked={fields[key]}
                  onCheckedChange={(checked) =>
                    onFieldsChange({ ...fields, [key]: checked === true })
                  }
                />
                <Label htmlFor={`field-${key}`} className="text-sm font-normal">
                  {label}
                </Label>
              </div>
            ))}
          </div>
        </PopoverContent>
      </Popover>
    </div>
  )
}
