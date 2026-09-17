import { Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Switch } from '@/shared/ui/switch'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import type { DossierCustomRow } from '../types/dossier-custom-row'
import {
  DOSSIER_FIELD_TYPES,
  DOSSIER_FIELD_TYPE_LABEL,
  slugifyFieldKey,
  type DossierFieldType,
} from '../types/dossier-field'

interface DossierCustomFieldRowProps {
  row: DossierCustomRow
  index: number
  /** Mã trường này có đụng ai không — dựng ở component cha (trùng nhau, hoặc trùng ô của loại). */
  clashWith?: string
  onChange: (next: DossierCustomRow) => void
  onRemove: () => void
  disabled?: boolean
}

/**
 * MỘT hàng của trình khai trường riêng: **tên · kiểu · bắt buộc · giá trị**.
 *
 * ⚠️ Cả bốn thứ đứng CHUNG một hàng vì người dùng nghĩ về chúng như một: *«thêm
 * ô Số quyết định, kiểu chữ, bắt buộc, giá trị 1234/QĐ»*. Tách khai báo sang một
 * khu rồi giá trị sang khu khác — như màn Loại hồ sơ đang làm — chỉ đúng khi
 * khai báo dùng lại cho NHIỀU hồ sơ; ở đây nó chỉ thuộc về đúng tờ này.
 *
 * ⚠️ Mọi `<Button>` khai `type="button"`. Hàng này nằm TRONG `<form>` của khung
 * CRUD, nên thiếu là bấm «Xóa» sẽ LƯU cả hồ sơ trước (bẫy thứ ba của
 * duoc-CR-317).
 */
export function DossierCustomFieldRow({
  row,
  index,
  clashWith,
  onChange,
  onRemove,
  disabled,
}: DossierCustomFieldRowProps) {
  const set = (patch: Partial<DossierCustomRow>) => onChange({ ...row, ...patch })

  //  Gợi ý mã từ tên CHỈ khi người dùng chưa tự sửa mã — ghi đè mã họ đã đặt là
  //  đổi khóa của dữ liệu, giá trị cũ ở lại dưới khóa cũ.
  const handleLabel = (label: string) => {
    const keyWasAuto = !row.key || row.key === slugifyFieldKey(row.label)
    set({ label, key: keyWasAuto ? slugifyFieldKey(label) : row.key })
  }

  //  ⚠️ Đổi KIỂU thì nắn lại giá trị cho khớp. Không nắn thì chuyển ô «Có/Không»
  //  (đang giữ `false`) sang ô Ngày là `DatePicker` nhận một boolean, và chuyển
  //  ngược lại thì công tắc đọc một chuỗi ngày ra `true` — người dùng thấy nút
  //  tự bật lên.
  const handleType = (next: DossierFieldType) => {
    if (next === row.type) return
    set({ type: next, value: next === 'switch' ? false : '', options: row.options })
  }

  return (
    <div
      className={cn(
        'grid gap-2 rounded-lg border bg-card p-2.5 @2xl:grid-cols-[minmax(0,1fr)_130px_92px_minmax(0,1.3fr)_auto] @2xl:items-end',
        clashWith && 'border-destructive/50',
      )}
    >
      <div className="space-y-1">
        <Label htmlFor={`cf-label-${index}`} className="text-xs @2xl:sr-only">
          Tên trường
        </Label>
        <Input
          id={`cf-label-${index}`}
          value={row.label}
          placeholder="VD: Số quyết định"
          disabled={disabled}
          onChange={(e) => handleLabel(e.target.value)}
        />
      </div>

      <div className="space-y-1">
        <Label htmlFor={`cf-type-${index}`} className="text-xs @2xl:sr-only">
          Kiểu
        </Label>
        <Select
          value={row.type}
          disabled={disabled}
          onValueChange={(v) => handleType(v as DossierFieldType)}
        >
          <SelectTrigger id={`cf-type-${index}`} className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {DOSSIER_FIELD_TYPES.filter((t) => t !== 'select').map((t) => (
              <SelectItem key={t} value={t}>
                {DOSSIER_FIELD_TYPE_LABEL[t]}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/*  Công tắc «bắt buộc» — chữ chỉ hiện ở khổ hẹp, khổ rộng đã có tiêu đề cột. */}
      <div className="flex items-center gap-2 @2xl:h-9 @2xl:justify-center">
        <Switch
          id={`cf-req-${index}`}
          checked={row.required}
          disabled={disabled}
          onCheckedChange={(v) => set({ required: v })}
        />
        <Label htmlFor={`cf-req-${index}`} className="cursor-pointer text-xs @2xl:sr-only">
          Bắt buộc
        </Label>
      </div>

      <div className="space-y-1">
        <Label htmlFor={`cf-val-${index}`} className="text-xs @2xl:sr-only">
          Giá trị
        </Label>
        <CustomValueInput row={row} index={index} disabled={disabled} onChange={set} />
      </div>

      <Button
        type="button"
        variant="ghost"
        size="icon"
        className="size-9 shrink-0 justify-self-end text-destructive"
        aria-label={`Xóa trường ${row.label || index + 1}`}
        disabled={disabled}
        onClick={onRemove}
      >
        <Trash2 className="size-4" />
      </Button>

      {clashWith && (
        <p className="text-xs text-destructive @2xl:col-span-5">{clashWith}</p>
      )}
    </div>
  )
}

/** Ô GIÁ TRỊ, hình dạng đổi theo kiểu người dùng vừa chọn ở ngay bên trái. */
function CustomValueInput({
  row,
  index,
  disabled,
  onChange,
}: {
  row: DossierCustomRow
  index: number
  disabled?: boolean
  onChange: (patch: Partial<DossierCustomRow>) => void
}) {
  const id = `cf-val-${index}`

  if (row.type === 'switch') {
    return (
      <div className="flex h-9 items-center">
        <Switch
          id={id}
          checked={Boolean(row.value)}
          disabled={disabled}
          onCheckedChange={(v) => onChange({ value: v })}
        />
      </div>
    )
  }

  if (row.type === 'date') {
    return (
      <DatePicker
        value={String(row.value ?? '')}
        onChange={(v) => onChange({ value: v })}
      />
    )
  }

  if (row.type === 'textarea') {
    return (
      <Textarea
        id={id}
        rows={2}
        value={String(row.value ?? '')}
        disabled={disabled}
        onChange={(e) => onChange({ value: e.target.value })}
      />
    )
  }

  return (
    <Input
      id={id}
      type={row.type === 'number' ? 'number' : 'text'}
      value={String(row.value ?? '')}
      disabled={disabled}
      onChange={(e) => onChange({ value: e.target.value })}
    />
  )
}
