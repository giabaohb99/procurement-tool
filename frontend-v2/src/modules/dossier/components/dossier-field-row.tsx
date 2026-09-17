import { ChevronDown, ChevronUp, Trash2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
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
import {
  DOSSIER_FIELD_TYPES,
  DOSSIER_FIELD_TYPE_LABEL,
  MAX_DOSSIER_FIELD_OPTIONS,
  slugifyFieldKey,
  type DossierFieldDef,
  type DossierFieldType,
} from '../types/dossier-field'

interface DossierFieldRowProps {
  field: DossierFieldDef
  index: number
  total: number
  /** Mã trường này có trùng mã của ô khác không — dựng ở component cha. */
  duplicateKey: boolean
  onChange: (next: DossierFieldDef) => void
  onMove: (from: number, to: number) => void
  onRemove: () => void
  disabled?: boolean
}

/**
 * MỘT dòng của trình khai bộ trường.
 *
 * ⚠️ Mọi `<Button>` ở đây khai `type="button"`. Component này nằm NGOÀI biểu mẫu
 * CRUD hôm nay, nhưng mặc định của HTML là `submit` — ai dời nó vào trong một
 * `<form>` mà quên thì bấm «Xóa ô» sẽ LƯU bản ghi trước, rồi hộp xác nhận mới
 * mở (bẫy thứ ba của duoc-CR-317, đã trúng ~11 màn chi tiết).
 */
export function DossierFieldRow({
  field,
  index,
  total,
  duplicateKey,
  onChange,
  onMove,
  onRemove,
  disabled,
}: DossierFieldRowProps) {
  const set = (patch: Partial<DossierFieldDef>) => onChange({ ...field, ...patch })

  //  Gợi ý mã từ nhãn CHỈ khi người dùng chưa tự đặt mã. Ghi đè mã họ đã sửa là
  //  đổi khóa của dữ liệu đã lưu — giá trị cũ ở lại dưới khóa cũ và ô mới hiện
  //  trống, im lặng.
  const handleLabel = (label: string) => {
    const suggested = slugifyFieldKey(label)
    const keyWasAuto = !field.key || field.key === slugifyFieldKey(field.label)
    set({ label, key: keyWasAuto ? suggested : field.key })
  }

  return (
    <div className="space-y-3 rounded-lg border bg-card p-3">
      <div className="flex items-start gap-2">
        <div className="grid min-w-0 flex-1 gap-3 @md:grid-cols-2">
          <div className="space-y-1.5">
            <Label htmlFor={`fld-label-${index}`}>Tên ô</Label>
            <Input
              id={`fld-label-${index}`}
              value={field.label}
              placeholder="VD: Số giấy phép"
              disabled={disabled}
              onChange={(e) => handleLabel(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor={`fld-key-${index}`}>Mã trường</Label>
            <Input
              id={`fld-key-${index}`}
              value={field.key}
              placeholder="so_giay_phep"
              disabled={disabled}
              onChange={(e) => set({ key: slugifyFieldKey(e.target.value) })}
            />
            {duplicateKey ? (
              <p className="text-xs text-destructive">
                Trùng mã với một ô khác. Hai ô cùng mã thì chỉ một giá trị sống sót.
              </p>
            ) : (
              <p className="text-xs text-muted-foreground">
                Khóa dữ liệu đã lưu bám vào. Đổi mã ô đang có dữ liệu = tạo ô mới rỗng.
              </p>
            )}
          </div>
        </div>

        <div className="flex shrink-0 flex-col gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-7"
            aria-label="Đưa lên trên"
            disabled={disabled || index === 0}
            onClick={() => onMove(index, index - 1)}
          >
            <ChevronUp className="size-4" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-7"
            aria-label="Đưa xuống dưới"
            disabled={disabled || index === total - 1}
            onClick={() => onMove(index, index + 1)}
          >
            <ChevronDown className="size-4" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-7 text-destructive"
            aria-label={`Xóa ô ${field.label || index + 1}`}
            disabled={disabled}
            onClick={onRemove}
          >
            <Trash2 className="size-4" />
          </Button>
        </div>
      </div>

      <div className="grid gap-3 @md:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor={`fld-type-${index}`}>Kiểu ô</Label>
          <Select
            value={field.type}
            disabled={disabled}
            onValueChange={(v) => set({ type: v as DossierFieldType })}
          >
            <SelectTrigger id={`fld-type-${index}`} className="w-full">
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

        <div className="space-y-1.5">
          <Label htmlFor={`fld-hint-${index}`}>Chú thích (tùy chọn)</Label>
          <Input
            id={`fld-hint-${index}`}
            value={field.hint}
            placeholder="Câu nhắc hiện dưới ô nhập"
            disabled={disabled}
            onChange={(e) => set({ hint: e.target.value })}
          />
        </div>
      </div>

      {/*  Danh sách mục CHỈ hiện với ô chọn — ẩn hẳn thay vì làm mờ: ô mờ vẫn
           chiếm chỗ và vẫn khiến người đọc dừng lại đọc nhãn của nó. Giá trị đã
           gõ KHÔNG bị xóa khi đổi kiểu, nên đổi nhầm rồi đổi lại không mất công
           gõ lại. */}
      {field.type === 'select' && (
        <div className="space-y-1.5">
          <Label htmlFor={`fld-opts-${index}`}>Các mục chọn</Label>
          <Input
            id={`fld-opts-${index}`}
            value={field.options.join(', ')}
            placeholder="Đường biển, Đường hàng không, Đường bộ"
            disabled={disabled}
            onChange={(e) =>
              set({
                options: e.target.value
                  .split(',')
                  .map((o) => o.trim())
                  .filter(Boolean)
                  .slice(0, MAX_DOSSIER_FIELD_OPTIONS),
              })
            }
          />
          <p className="text-xs text-muted-foreground">
            Ngăn cách bằng dấu phẩy. Tối đa {MAX_DOSSIER_FIELD_OPTIONS} mục.
          </p>
        </div>
      )}

      <div className="flex items-center justify-between gap-3 rounded-md border bg-muted/20 px-3 py-2">
        <Label htmlFor={`fld-req-${index}`} className="cursor-pointer">
          Bắt buộc nhập
          <span className="mt-0.5 block text-xs font-normal text-muted-foreground">
            Hồ sơ cũ của loại này cũng bị đòi điền ô đó ở lần sửa kế tiếp.
          </span>
        </Label>
        <Switch
          id={`fld-req-${index}`}
          checked={field.required}
          disabled={disabled}
          onCheckedChange={(v) => set({ required: v })}
        />
      </div>
    </div>
  )
}
