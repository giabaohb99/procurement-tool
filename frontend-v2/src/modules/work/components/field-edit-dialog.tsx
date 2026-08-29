import { Info } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import {
  useCreateLabelOption,
  useDeleteLabelField,
  useDeleteLabelOption,
  useUpdateLabelField,
  useUpdateLabelOption,
} from '../hooks/use-work-config'
import {
  fieldHasOptions,
  WORK_FIELD_TYPES,
  type WorkLabelField,
} from '../types/work'
import { saveFieldOptions, type DraftOption } from '../utils/save-field-options'
import { FieldOptionList } from './field-option-list'

interface FieldEditDialogProps {
  listId: number
  /** Trường đang sửa; `null` = đóng hộp thoại. */
  field: WorkLabelField | null
  onClose: () => void
}

/**
 * Hộp thoại «Sửa trường» — MỘT khuôn duy nhất cho mọi trường hiện trên thẻ:
 * tên trường · kiểu trường · bộ giá trị kéo xếp được · xóa trường · nút Lưu.
 *
 * Tag cũng đi đúng cửa này: nó là một trường tùy biến kiểu CHỌN NHIỀU như mọi
 * trường khác kể từ migration `c8a1d4f60b72`, không còn bảng lẫn giao diện
 * riêng.
 *
 * Vì sao là HỘP THOẠI chứ không sửa tại chỗ trong menu «Tùy chỉnh»: menu ấy rộng
 * 320px và đang là một popover — nhồi thêm ô nhập, ô chọn kiểu và một danh sách
 * kéo thả vào đó thì nửa dưới tràn khỏi màn hình, mà mỗi popover lồng nhau (bảng
 * màu) lại đóng nhầm lớp cha.
 *
 * **Sửa theo lô, chốt bằng nút Lưu** — khác các ô khác của phân hệ (lưu khi rời
 * ô). Ở đây một lần lưu có thể là bốn lệnh khác nhau (đổi tên, đổi kiểu,
 * thêm/xóa/sửa giá trị); bắn từng lệnh theo từng phím gõ thì người dùng thấy
 * bảng nhấp nháy và không có đường lui.
 */
export function FieldEditDialog({ listId, field, onClose }: FieldEditDialogProps) {
  if (!field) return null
  return (
    <Dialog open onOpenChange={(mo) => !mo && onClose()}>
      <DialogContent className="sm:max-w-lg">
        {/*  `key` theo trường: bản nháp dựng bằng `useState(...)` một lần lúc gắn
            vào cây. Mở trường khác thì phải là một component KHÁC, không thì ô
            tên vẫn giữ tên của trường mở trước đó (và một `useEffect` đồng bộ
            lại state là đúng thứ React 19 cảnh báo "cascading renders"). */}
        <FieldForm key={field.id} listId={listId} field={field} onClose={onClose} />
      </DialogContent>
    </Dialog>
  )
}

function FieldForm({
  listId,
  field,
  onClose,
}: {
  listId: number
  field: WorkLabelField
  onClose: () => void
}) {
  const updateField = useUpdateLabelField(listId)
  const deleteField = useDeleteLabelField(listId)
  const createOption = useCreateLabelOption(listId)
  const updateOption = useUpdateLabelOption(listId)
  const deleteOption = useDeleteLabelOption(listId)

  const [ten, setTen] = useState(field.name)
  const [kieu, setKieu] = useState(field.field_type)
  const [options, setOptions] = useState<DraftOption[]>(() =>
    field.options.map((o) => ({ id: o.id, name: o.name, color: o.color })),
  )

  //  Hai lý do khóa ô KIỂU, cùng luật với backend (`_assert_can_change_type`).
  const khoaKieu = Boolean(field.system_key) || field.value_count > 0
  const canhBao = field.system_key
    ? 'Trường này do hệ thống nạp sẵn cho MỌI dự án nên không đổi được kiểu. Tên, bộ giá trị và màu thì vẫn sửa thoải mái, và chỉ đổi trong dự án này.'
    : field.value_count > 0
      ? `${field.value_count} việc đang gán giá trị của trường này, nên không đổi được kiểu — đổi kiểu là mọi giá trị đã gán nằm sai chỗ.`
      : ''

  async function luu() {
    const tenSach = ten.trim()
    if (!tenSach) return
    if (tenSach !== field.name || kieu !== field.field_type)
      await updateField.mutateAsync({
        fieldId: field.id,
        values: {
          name: tenSach,
          //  Chỉ gửi kiểu khi thật sự đổi: gửi kèm mà trường đang bị khóa thì
          //  backend từ chối cả lệnh, mất luôn phần đổi tên.
          ...(kieu === field.field_type ? {} : { field_type: kieu }),
        },
      })

    await saveFieldOptions(field.options, options, {
      create: (values) => createOption.mutateAsync({ fieldId: field.id, values }),
      update: (optionId, values) => updateOption.mutateAsync({ optionId, values }),
      remove: (optionId) => deleteOption.mutateAsync(optionId),
    })
  }

  return (
    <FieldFormBody
      note={canhBao}
      name={ten}
      onNameChange={setTen}
      fieldType={kieu}
      onTypeChange={khoaKieu ? undefined : setKieu}
      options={options}
      onOptionsChange={setOptions}
      onDelete={() => {
        deleteField.mutate(field.id)
        onClose()
      }}
      onSave={luu}
      onClose={onClose}
    />
  )
}

interface FieldFormBodyProps {
  /** Câu giải thích vì sao vài ô bị khóa; rỗng = không hiện. */
  note?: string
  name: string
  onNameChange: (value: string) => void
  fieldType: number
  /** Vắng = kiểu bị khóa (trường hệ, hoặc đã có việc gán giá trị). */
  onTypeChange?: (value: number) => void
  options: DraftOption[]
  onOptionsChange: (next: DraftOption[]) => void
  onDelete: () => void
  onSave: () => Promise<void> | void
  onClose: () => void
}

/** Phần thân dùng chung của hộp thoại — thuần hiển thị, không biết trường loại gì. */
function FieldFormBody({
  note,
  name,
  onNameChange,
  fieldType,
  onTypeChange,
  options,
  onOptionsChange,
  onDelete,
  onSave,
  onClose,
}: FieldFormBodyProps) {
  const [dangLuu, setDangLuu] = useState(false)
  const kieuLabel =
    WORK_FIELD_TYPES.find((t) => t.value === fieldType)?.label ?? 'Chọn một giá trị'

  async function luu() {
    setDangLuu(true)
    try {
      await onSave()
      onClose()
    } finally {
      setDangLuu(false)
    }
  }

  return (
    <>
      <DialogHeader>
        <DialogTitle>Sửa trường</DialogTitle>
      </DialogHeader>

      {note && (
        <p className="flex gap-2 rounded-md bg-amber-500/10 p-3 text-sm text-amber-700 dark:text-amber-300">
          <Info className="mt-0.5 size-4 shrink-0" />
          {note}
        </p>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <Label htmlFor="field-name">Tên trường</Label>
          <Input
            id="field-name"
            value={name}
            onChange={(su) => onNameChange(su.target.value)}
            placeholder='Ví dụ "Phiên bản"'
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="field-type">Kiểu trường</Label>
          {/*  Khóa thì hiện dạng CHỮ chứ không phải ô chọn mờ đi: `disabled` gỡ
              luôn khả năng bôi đen, mà giá trị thật lại nhìn như chữ gợi ý. */}
          {onTypeChange ? (
            <Select value={String(fieldType)} onValueChange={(v) => onTypeChange(Number(v))}>
              <SelectTrigger id="field-type" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {WORK_FIELD_TYPES.map((t) => (
                  <SelectItem key={t.value} value={String(t.value)}>
                    {t.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>{kieuLabel}</ReadOnlyValue>
          )}
        </div>
      </div>

      {/*  Bốn kiểu còn lại (người · số · ngày · chữ) nhập tự do nên KHÔNG có bộ
          giá trị. */}
      {fieldHasOptions(fieldType) && (
        <div className="space-y-1.5">
          <Label>Bộ giá trị</Label>
          <FieldOptionList options={options} onChange={onOptionsChange} />
        </div>
      )}

      <DialogFooter className="sm:justify-between">
        <Button
          variant="ghost"
          className="text-destructive hover:bg-destructive/10 hover:text-destructive"
          onClick={onDelete}
        >
          Xóa trường khỏi dự án
        </Button>
        <Button onClick={luu} disabled={dangLuu || !name.trim()}>
          Lưu
        </Button>
      </DialogFooter>
    </>
  )
}
