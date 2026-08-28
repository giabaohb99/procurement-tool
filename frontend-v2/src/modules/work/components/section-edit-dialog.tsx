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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import {
  useCreateSection,
  useDeleteSection,
  useUpdateSection,
} from '../hooks/use-work-config'
import type { WorkSection } from '../types/work'
import { WORK_COLORS, dotClass } from '../utils/work-colors'

export type SectionDialogMode = 'create' | 'edit' | 'delete'

interface SectionEditDialogProps {
  mode: SectionDialogMode | null
  listId: number
  /** Cột đang thao tác (bỏ trống khi tạo mới). */
  section: WorkSection | null
  /** Mọi cột của list — cần cho ô "dồn việc sang cột nào" lúc xóa. */
  sections: WorkSection[]
  onClose: () => void
}

/**
 * Thêm / sửa / xóa CỘT kanban.
 *
 * Nhánh xóa bắt chọn cột nhận khi cột còn việc: backend chặn cứng, nhưng hỏi
 * ngay ở đây thì người dùng không phải ăn một thông báo lỗi rồi mở lại.
 */
export function SectionEditDialog({
  mode,
  listId,
  section,
  sections,
  onClose,
}: SectionEditDialogProps) {
  return (
    <Dialog open={mode !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        {/*  Thân hộp thoại nằm TRONG `DialogContent` nên nó chỉ tồn tại lúc mở:
            đóng là unmount, mở lại là state khởi tạo lại từ chính cột đang chọn.
            Nhờ vậy không cần `useEffect` đồng bộ state (`set-state-in-effect`). */}
        {mode !== null && (
          <SectionForm
            key={`${mode}-${section?.id ?? 'moi'}`}
            mode={mode}
            listId={listId}
            section={section}
            sections={sections}
            onClose={onClose}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

interface SectionFormProps {
  mode: SectionDialogMode
  listId: number
  section: WorkSection | null
  sections: WorkSection[]
  onClose: () => void
}

function SectionForm({ mode, listId, section, sections, onClose }: SectionFormProps) {
  const [ten, setTen] = useState(section?.name ?? '')
  const [mau, setMau] = useState<string>(section?.color || 'slate')
  const [dichChuyen, setDichChuyen] = useState<string>('')

  const createSection = useCreateSection(listId)
  const updateSection = useUpdateSection(listId)
  const deleteSection = useDeleteSection(listId)

  const conLai = sections.filter((s) => s.id !== section?.id)

  function luu() {
    const value = ten.trim()
    if (!value) return
    if (mode === 'create') {
      createSection.mutate(
        { name: value, color: mau, sort_order: sections.length },
        { onSuccess: onClose },
      )
    } else if (section) {
      updateSection.mutate(
        { id: section.id, values: { name: value, color: mau } },
        { onSuccess: onClose },
      )
    }
  }

  function xoa() {
    if (!section) return
    deleteSection.mutate(
      { id: section.id, moveTo: dichChuyen ? Number(dichChuyen) : undefined },
      { onSuccess: onClose },
    )
  }

  const laXoa = mode === 'delete'

  return (
    <>
        <DialogHeader>
          <DialogTitle>
            {laXoa ? 'Xóa cột' : mode === 'create' ? 'Thêm cột' : 'Sửa cột'}
          </DialogTitle>
        </DialogHeader>

        {laXoa ? (
          <div className="space-y-3">
            <p className="text-sm">
              Xóa cột <span className="font-medium">{section?.name}</span>. Việc đang nằm
              trong cột phải dồn sang cột khác — chọn cột nhận:
            </p>
            <Select value={dichChuyen} onValueChange={setDichChuyen}>
              <SelectTrigger>
                <SelectValue placeholder="Chọn cột nhận (bỏ trống nếu cột đang rỗng)" />
              </SelectTrigger>
              <SelectContent>
                {conLai.map((s) => (
                  <SelectItem key={s.id} value={String(s.id)}>
                    {s.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="section-name">Tên cột</Label>
              <Input
                id="section-name"
                autoFocus
                value={ten}
                onChange={(e) => setTen(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && luu()}
              />
            </div>
            <div className="space-y-2">
              <Label>Màu</Label>
              {/* Bảng màu ĐẶT SẴN, không cho gõ hex: hex tự do không có biến
                  thể tối, bật nền tối là chữ chìm hẳn (§9). */}
              <div className="flex flex-wrap gap-2">
                {WORK_COLORS.map((c) => (
                  <button
                    key={c.value}
                    type="button"
                    title={c.label}
                    onClick={() => setMau(c.value)}
                    className={cn(
                      'size-6 rounded-full ring-offset-2 ring-offset-background',
                      dotClass(c.value),
                      mau === c.value && 'ring-2 ring-primary',
                    )}
                  />
                ))}
              </div>
            </div>
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Hủy
          </Button>
          {laXoa ? (
            <Button variant="destructive" onClick={xoa}>
              Xóa cột
            </Button>
          ) : (
            <Button onClick={luu} disabled={!ten.trim()}>
              Lưu
            </Button>
          )}
        </DialogFooter>
    </>
  )
}
