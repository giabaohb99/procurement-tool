import { Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import {
  fieldHasOptions,
  WORK_FIELD_TYPE,
  WORK_FIELD_TYPES,
} from '../types/work'
import { cn } from '@/shared/utils/cn'
import {
  useCreateLabelField,
  useCreateLabelOption,
  useCreateTag,
  useDeleteLabelField,
  useDeleteLabelOption,
  useDeleteTag,
  useWorkLabelFields,
  useWorkTags,
} from '../hooks/use-work-config'
import { WORK_COLORS, chipClass, dotClass } from '../utils/work-colors'

interface ListConfigDialogProps {
  open: boolean
  listId: number
  onClose: () => void
}

/**
 * Khai TAG và NHÃN TÙY BIẾN của một danh sách (B-05, B-08).
 *
 * Hai thứ khác nhau, cố ý để chung một hộp thoại hai tab vì cùng là "danh mục
 * riêng của list" và cùng chỉ ADMIN trở lên mới sửa:
 * - **Tag** — một trường ĐA TRỊ có sẵn ở mọi list.
 * - **Nhãn tùy biến** — người dùng tự đặt THÊM TRƯỜNG ("Phiên bản"), mỗi trường
 *   một bộ giá trị và mỗi task chọn ĐÚNG MỘT giá trị.
 */
export function ListConfigDialog({ open, listId, onClose }: ListConfigDialogProps) {
  const { data: tags = [] } = useWorkTags(open ? listId : undefined)
  const { data: fields = [] } = useWorkLabelFields(open ? listId : undefined)

  const createTag = useCreateTag(listId)
  const deleteTag = useDeleteTag(listId)
  const createField = useCreateLabelField(listId)
  const deleteField = useDeleteLabelField(listId)
  const createOption = useCreateLabelOption(listId)
  const deleteOption = useDeleteLabelOption(listId)

  const [tagName, setTagName] = useState('')
  const [tagColor, setTagColor] = useState('sky')
  const [fieldName, setFieldName] = useState('')
  const [fieldType, setFieldType] = useState<number>(WORK_FIELD_TYPE.SINGLE)
  const [optionName, setOptionName] = useState<Record<number, string>>({})
  //  Màu của giá trị SẮP thêm, nhớ theo từng trường. Trước đây khóa cứng
  //  `slate` nên mọi giá trị người dùng tự khai đều xám ngoét, trong khi giá trị
  //  do seed nạp thì có màu — nhìn như tính năng hỏng.
  const [optionColor, setOptionColor] = useState<Record<number, string>>({})

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Thiết lập danh sách</DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="tags">
          <TabsList>
            <TabsTrigger value="tags">Tag</TabsTrigger>
            <TabsTrigger value="labels">Nhãn tùy biến</TabsTrigger>
          </TabsList>

          <TabsContent value="tags" className="space-y-3 pt-3">
            <div className="flex items-center gap-2">
              <Input
                value={tagName}
                placeholder="Tên tag"
                onChange={(e) => setTagName(e.target.value)}
              />
              <ColorPicker value={tagColor} onChange={setTagColor} />
              <Button
                onClick={() => {
                  if (!tagName.trim()) return
                  createTag.mutate(
                    { name: tagName.trim(), color: tagColor },
                    { onSuccess: () => setTagName('') },
                  )
                }}
              >
                <Plus className="size-4" />
                Thêm
              </Button>
            </div>

            <div className="flex flex-wrap gap-2">
              {tags.map((t) => (
                <span
                  key={t.id}
                  className={cn('flex items-center gap-1 rounded px-2 py-1 text-xs', chipClass(t.color))}
                >
                  {t.name}
                  <button
                    type="button"
                    title="Xóa tag"
                    onClick={() => deleteTag.mutate(t.id)}
                    className="opacity-60 hover:opacity-100"
                  >
                    <Trash2 className="size-3" />
                  </button>
                </span>
              ))}
              {tags.length === 0 && (
                <p className="text-sm text-muted-foreground">Chưa khai tag nào.</p>
              )}
            </div>
          </TabsContent>

          <TabsContent value="labels" className="space-y-4 pt-3">
            <div className="flex items-center gap-2">
              <Input
                value={fieldName}
                placeholder='Tên trường, ví dụ "Phiên bản"'
                onChange={(e) => setFieldName(e.target.value)}
              />
              {/*  Chọn KIỂU ngay lúc khai, như hộp «Add custom field» của Lark.
                  Kiểu KHÔNG sửa được sau khi tạo: đổi kiểu thì mọi giá trị đã
                  gán nằm sai cột, nên muốn đổi phải xóa trường rồi khai lại. */}
              <Select
                value={String(fieldType)}
                onValueChange={(v) => setFieldType(Number(v))}
              >
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

            {fields.map((f) => (
              <div key={f.id} className="rounded-lg border p-3">
                <div className="mb-2 flex items-center justify-between">
                  <span className="flex items-center gap-2 text-sm font-medium">
                    {f.name}
                    <span className="rounded bg-muted px-1.5 py-0.5 text-[11px] font-normal text-muted-foreground">
                      {WORK_FIELD_TYPES.find((t) => t.value === f.field_type)?.label ?? 'Chọn một giá trị'}
                    </span>
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    title="Xóa trường nhãn"
                    onClick={() => deleteField.mutate(f.id)}
                  >
                    <Trash2 className="size-4 text-destructive" />
                  </Button>
                </div>

                {/*  Bốn kiểu còn lại (người · số · ngày · chữ) nhập tự do nên
                    KHÔNG có bộ giá trị — hiện ô "Thêm giá trị" ở đó chỉ tổ làm
                    người dùng gõ vào rồi tự hỏi sao không thấy đâu. */}
                {fieldHasOptions(f.field_type) ? (
                <>
                <div className="mb-2 flex flex-wrap gap-2">
                  {f.options.map((o) => (
                    <span
                      key={o.id}
                      className={cn('flex items-center gap-1 rounded px-2 py-1 text-xs', chipClass(o.color))}
                    >
                      {o.name}
                      <button
                        type="button"
                        title="Xóa giá trị"
                        onClick={() => deleteOption.mutate(o.id)}
                        className="opacity-60 hover:opacity-100"
                      >
                        <Trash2 className="size-3" />
                      </button>
                    </span>
                  ))}
                  {f.options.length === 0 && (
                    <span className="text-xs text-muted-foreground">Chưa có giá trị nào.</span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <Input
                    value={optionName[f.id] ?? ''}
                    placeholder="Giá trị mới"
                    onChange={(e) => setOptionName({ ...optionName, [f.id]: e.target.value })}
                  />
                  <ColorPicker
                    value={optionColor[f.id] ?? 'sky'}
                    onChange={(color) => setOptionColor({ ...optionColor, [f.id]: color })}
                  />
                  <Button
                    variant="outline"
                    onClick={() => {
                      const name = (optionName[f.id] ?? '').trim()
                      if (!name) return
                      createOption.mutate(
                        { fieldId: f.id, values: { name, color: optionColor[f.id] ?? 'sky' } },
                        { onSuccess: () => setOptionName({ ...optionName, [f.id]: '' }) },
                      )
                    }}
                  >
                    Thêm giá trị
                  </Button>
                </div>
                </>
                ) : null}
              </div>
            ))}
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  )
}

function ColorPicker({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex flex-wrap gap-1">
      {WORK_COLORS.map((c) => (
        <button
          key={c.value}
          type="button"
          title={c.label}
          onClick={() => onChange(c.value)}
          className={cn(
            'size-5 rounded-full ring-offset-2 ring-offset-background',
            dotClass(c.value),
            value === c.value && 'ring-2 ring-primary',
          )}
        />
      ))}
    </div>
  )
}
