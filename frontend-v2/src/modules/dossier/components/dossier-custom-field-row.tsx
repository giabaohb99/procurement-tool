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
  MAX_DOSSIER_FIELD_OPTIONS,
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
    //  Giữ `options` khi đổi kiểu: người dùng gõ nhầm kiểu rồi đổi lại thì mục
    //  đã khai còn nguyên, khỏi gõ lại.
    set({ type: next, value: next === 'switch' ? false : '', options: row.options })
  }

  //  ⚠️ Sửa danh sách mục mà giá trị đang chọn RỚT khỏi danh sách thì xóa nó đi.
  //  Giữ lại thì Radix không khớp mục nào và rơi về chữ gợi ý — nhìn y hệt ô
  //  chưa chọn, nhưng giá trị cũ vẫn nằm trong form và bấm Lưu là backend trả
  //  422 «nhận một trong các mục: …» cho một thứ không hiện trên màn hình.
  const handleOptions = (raw: string) => {
    const options = raw.split(',').map((o) => o.trim()).filter(Boolean)
    const stillThere = options.includes(String(row.value ?? ''))
    set({ options, value: stillThere ? row.value : '' })
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
            {DOSSIER_FIELD_TYPES.map((t) => (
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

      {/*  DÒNG PHỤ chỉ của ô CHỌN — khai các mục bấm được.
           ⚠️ Nằm dưới cả hàng chứ không chen vào một cột: bốn cột trên đã chật,
           mà danh sách mục thì dài hơn mọi ô còn lại cộng lại. Ẩn hẳn với kiểu
           khác thay vì làm mờ — ô mờ vẫn chiếm chỗ và vẫn bắt người đọc dừng
           lại xem nó là gì. */}
      {row.type === 'select' && (
        <div className="space-y-1 @2xl:col-span-5">
          <Label htmlFor={`cf-opts-${index}`} className="text-xs">
            Các mục chọn
          </Label>
          <Input
            id={`cf-opts-${index}`}
            value={row.options.join(', ')}
            placeholder="Đường biển, Đường hàng không, Đường bộ"
            disabled={disabled}
            onChange={(e) => handleOptions(e.target.value)}
          />
          <p className="text-xs text-muted-foreground">
            Ngăn cách bằng dấu phẩy. Tối đa {MAX_DOSSIER_FIELD_OPTIONS} mục.
          </p>
        </div>
      )}

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

  if (row.type === 'select') {
    //  ⚠️ Chưa khai mục nào thì ô chọn là một danh sách RỖNG — bấm vào mở ra
    //  khoảng trắng, người dùng tưởng hỏng. Nói thẳng việc phải làm trước.
    if (row.options.length === 0) {
      return (
        <div className="flex h-9 items-center text-xs text-muted-foreground">
          Khai «Các mục chọn» bên dưới trước
        </div>
      )
    }
    return (
      <Select
        value={String(row.value ?? '')}
        disabled={disabled}
        onValueChange={(v) => {
          //  ⚠️ BỎ QUA chuỗi rỗng — không phải người dùng chọn. Radix giữ một
          //  `<select>` ẩn và đồng bộ bằng cách gán thẳng `value`; trình duyệt
          //  ép giá trị chưa có `<option>` tương ứng về rỗng rồi bắn `change`,
          //  Radix gọi ngược `onValueChange('')` và xóa trắng giá trị thật.
          //  Cùng bẫy đã ghi ở `CrudSelectField` của khung CRUD.
          if (v === '') return
          onChange({ value: v })
        }}
      >
        <SelectTrigger id={id} className="w-full">
          <SelectValue placeholder="Chọn giá trị" />
        </SelectTrigger>
        <SelectContent>
          {row.options.map((opt) => (
            <SelectItem key={opt} value={opt}>
              {opt}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
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
