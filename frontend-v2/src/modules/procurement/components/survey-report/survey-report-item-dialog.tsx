import { Loader2, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import type { SurveyReportItem } from '../../types/survey-request-report'

interface SurveyReportItemDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** null = thêm nút mới. */
  item: SurveyReportItem | null
  pending: boolean
  onSave: (itemId: number | undefined, name: string) => Promise<unknown>
  onDelete: (itemId: number) => Promise<unknown>
}

/** Thêm / đổi tên / xóa một NÚT dòng hàng của khối báo cáo (case C-01). */
export function SurveyReportItemDialog({
  open,
  onOpenChange,
  item,
  pending,
  onSave,
  onDelete,
}: SurveyReportItemDialogProps) {
  const [name, setName] = useState(item?.name ?? '')
  const once = useSingleFlight()

  //  Reset ngay trong lúc render mỗi lần MỞ (mẫu `useHasChanged`) — không qua
  //  effect để khỏi lóe dữ liệu của lần mở trước.
  const openChanged = useHasChanged(open)
  if (openChanged && open) setName(item?.name ?? '')

  const isDirty = name !== (item?.name ?? '')

  const attemptClose = async () => {
    if (pending) return
    if (
      isDirty &&
      !(await confirm({ message: 'Bạn có thay đổi chưa lưu. Đóng và bỏ các thay đổi này?' }))
    )
      return
    onOpenChange(false)
  }

  const handleSave = () =>
    once(async () => {
      if (!name.trim()) {
        toast.error('Nhập tên nút dòng hàng')
        return
      }
      await onSave(item?.id, name.trim())
      onOpenChange(false)
    })

  const handleDelete = () =>
    once(async () => {
      if (!item) return
      if (
        !(await confirm({
          message: `Xóa nút "${item.name}"? Hồ sơ đang gắn nút này sẽ chuyển về Chung, không bị xóa.`,
        }))
      )
        return
      await onDelete(item.id)
      onOpenChange(false)
    })

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (next) onOpenChange(true)
        else void attemptClose()
      }}
    >
      <DialogContent
        className="sm:max-w-md"
        onEscapeKeyDown={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
        onPointerDownOutside={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>{item ? 'Sửa nút dòng hàng' : 'Thêm nút dòng hàng'}</DialogTitle>
          <DialogDescription>
            Nút dùng để lọc hồ sơ báo cáo theo dòng hàng. Hồ sơ «Chung» hiện ở mọi nút.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-1.5">
          <Label>
            Tên nút
            <RequiredMark />
          </Label>
          <Input
            value={name}
            placeholder="VD: K2SO4, KNO3…"
            onChange={(e) => setName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault()
                void handleSave()
              }
            }}
          />
        </div>

        <DialogFooter className="gap-2 sm:justify-between">
          <div>
            {item && (
              <Button
                type="button"
                variant="outline"
                className="text-destructive hover:text-destructive"
                disabled={pending}
                onClick={handleDelete}
              >
                <Trash2 />
                Xóa
              </Button>
            )}
          </div>
          <div className="flex gap-2">
            <Button type="button" variant="outline" disabled={pending} onClick={attemptClose}>
              Hủy
            </Button>
            <Button type="button" disabled={pending} onClick={handleSave}>
              {pending && <Loader2 className="animate-spin" />}
              Lưu
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
