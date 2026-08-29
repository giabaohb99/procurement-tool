import { Pencil, Plus } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { useCreateLabelField, useWorkLabelFields } from '../hooks/use-work-config'
import {
  fieldHasOptions,
  WORK_FIELD_TYPE,
  WORK_FIELD_TYPES,
  type WorkLabelField,
} from '../types/work'
import { FieldEditDialog } from './field-edit-dialog'

interface ListConfigDialogProps {
  open: boolean
  listId: number
  onClose: () => void
}

/**
 * Khai TRƯỜNG của một danh sách (B-08, B-13) — MỘT bảng cho tất cả, Tag và Độ ưu
 * tiên nằm chung với các trường do người dùng tự khai vì chúng đúng là cùng một
 * thứ (migration `c8a1d4f60b72`).
 *
 * Sửa thì mở đúng hộp thoại «Sửa trường» của menu «Tùy chỉnh» — một khuôn duy
 * nhất, hai lối vào. Chỉ ADMIN trở lên mới tới được màn này (04 §3).
 */
export function ListConfigDialog({ open, listId, onClose }: ListConfigDialogProps) {
  const { data: fields = [] } = useWorkLabelFields(open ? listId : undefined)
  const createField = useCreateLabelField(listId)

  const [fieldName, setFieldName] = useState('')
  const [fieldType, setFieldType] = useState<number>(WORK_FIELD_TYPE.SINGLE)
  const [dangSua, setDangSua] = useState<WorkLabelField | null>(null)

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Trường của dự án</DialogTitle>
        </DialogHeader>

        <div className="flex items-center gap-2">
          <Input
            value={fieldName}
            placeholder='Tên trường, ví dụ "Phiên bản"'
            onChange={(e) => setFieldName(e.target.value)}
          />
          {/*  Chọn KIỂU ngay lúc khai, như hộp «Add custom field» của Lark.
              Kiểu chỉ đổi được khi trường chưa có việc nào gán giá trị — luật
              nằm ở backend, hộp «Sửa trường» chỉ phản ánh lại. */}
          <Select value={String(fieldType)} onValueChange={(v) => setFieldType(Number(v))}>
            <SelectTrigger className="w-48 shrink-0">
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
          <Button
            className="shrink-0"
            onClick={() => {
              if (!fieldName.trim()) return
              createField.mutate(
                { name: fieldName.trim(), field_type: fieldType },
                { onSuccess: () => setFieldName('') },
              )
            }}
          >
            <Plus className="size-4" />
            Thêm trường
          </Button>
        </div>

        <div className="space-y-1">
          {fields.map((f) => (
            <FieldRow
              key={f.id}
              name={f.name}
              typeLabel={
                WORK_FIELD_TYPES.find((t) => t.value === f.field_type)?.label ??
                'Chọn một giá trị'
              }
              valueCount={fieldHasOptions(f.field_type) ? f.options.length : undefined}
              onEdit={() => setDangSua(f)}
            />
          ))}
        </div>

        {/*  Hộp thoại LỒNG trong hộp thoại này: Radix cho mỗi hộp một lớp phủ
            riêng nên lớp trong vẫn nhận phím và bấm bình thường. */}
        <FieldEditDialog listId={listId} field={dangSua} onClose={() => setDangSua(null)} />
      </DialogContent>
    </Dialog>
  )
}

function FieldRow({
  name,
  typeLabel,
  valueCount,
  onEdit,
}: {
  name: string
  typeLabel: string
  /** Số giá trị trong bộ; `undefined` với kiểu nhập tự do (người · số · ngày · chữ). */
  valueCount?: number
  onEdit: () => void
}) {
  return (
    <div className="flex items-center gap-2 rounded-lg border px-3 py-2">
      <span className="flex-1 truncate text-sm font-medium">{name}</span>
      <span className="text-xs text-muted-foreground">
        {typeLabel}
        {valueCount !== undefined && ` · ${valueCount} giá trị`}
      </span>
      <IconTooltip label={`Sửa trường ${name}`}>
        <Button
          variant="ghost"
          size="icon"
          className="size-7"
          aria-label={`Sửa trường ${name}`}
          onClick={onEdit}
        >
          <Pencil className="size-3.5" />
        </Button>
      </IconTooltip>
    </div>
  )
}
