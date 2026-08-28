import { Plus, Trash2 } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
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

  const [tenTag, setTenTag] = useState('')
  const [mauTag, setMauTag] = useState('sky')
  const [tenTruong, setTenTruong] = useState('')
  const [tenGiaTri, setTenGiaTri] = useState<Record<number, string>>({})

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
                value={tenTag}
                placeholder="Tên tag"
                onChange={(e) => setTenTag(e.target.value)}
              />
              <ColorPicker value={mauTag} onChange={setMauTag} />
              <Button
                onClick={() => {
                  if (!tenTag.trim()) return
                  createTag.mutate(
                    { name: tenTag.trim(), color: mauTag },
                    { onSuccess: () => setTenTag('') },
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
                value={tenTruong}
                placeholder='Tên trường, ví dụ "Phiên bản"'
                onChange={(e) => setTenTruong(e.target.value)}
              />
              <Button
                onClick={() => {
                  if (!tenTruong.trim()) return
                  createField.mutate(
                    { name: tenTruong.trim() },
                    { onSuccess: () => setTenTruong('') },
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
                  <span className="text-sm font-medium">{f.name}</span>
                  <Button
                    variant="ghost"
                    size="icon"
                    title="Xóa trường nhãn"
                    onClick={() => deleteField.mutate(f.id)}
                  >
                    <Trash2 className="size-4 text-destructive" />
                  </Button>
                </div>

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
                    value={tenGiaTri[f.id] ?? ''}
                    placeholder="Giá trị mới"
                    onChange={(e) => setTenGiaTri({ ...tenGiaTri, [f.id]: e.target.value })}
                  />
                  <Button
                    variant="outline"
                    onClick={() => {
                      const name = (tenGiaTri[f.id] ?? '').trim()
                      if (!name) return
                      createOption.mutate(
                        { fieldId: f.id, values: { name, color: 'slate' } },
                        { onSuccess: () => setTenGiaTri({ ...tenGiaTri, [f.id]: '' }) },
                      )
                    }}
                  >
                    Thêm giá trị
                  </Button>
                </div>
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
