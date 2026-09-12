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
import type { SurveyReportPhase } from '../../types/survey-request-report'

interface SurveyReportPhaseDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** null = thêm giai đoạn mới. */
  phase: SurveyReportPhase | null
  /** Giai đoạn còn hồ sơ thì backend chặn xóa — cờ này để câu chặn nói trước. */
  docCount: number
  pending: boolean
  onSave: (phaseId: number | undefined, name: string, location: string) => Promise<unknown>
  onDelete: (phaseId: number) => Promise<unknown>
}

/** Thêm / sửa / xóa một GIAI ĐOẠN của khối báo cáo (case C-01). */
export function SurveyReportPhaseDialog({
  open,
  onOpenChange,
  phase,
  docCount,
  pending,
  onSave,
  onDelete,
}: SurveyReportPhaseDialogProps) {
  const [name, setName] = useState(phase?.name ?? '')
  const [location, setLocation] = useState(phase?.location ?? '')
  const once = useSingleFlight()

  //  Reset ngay trong lúc render mỗi lần MỞ (mẫu `useHasChanged`) — không qua
  //  effect để khỏi lóe dữ liệu của lần mở trước.
  const openChanged = useHasChanged(open)
  if (openChanged && open) {
    setName(phase?.name ?? '')
    setLocation(phase?.location ?? '')
  }

  const isDirty = name !== (phase?.name ?? '') || location !== (phase?.location ?? '')

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
        toast.error('Nhập tên giai đoạn')
        return
      }
      await onSave(phase?.id, name.trim(), location.trim())
      onOpenChange(false)
    })

  const handleDelete = () =>
    once(async () => {
      if (!phase) return
      if (docCount > 0) {
        toast.error(
          `Giai đoạn còn ${docCount} hồ sơ — chuyển hồ sơ sang giai đoạn khác trước khi xóa`,
        )
        return
      }
      if (!(await confirm({ message: `Xóa giai đoạn "${phase.name}"?` }))) return
      await onDelete(phase.id)
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
          <DialogTitle>{phase ? 'Sửa giai đoạn' : 'Thêm giai đoạn'}</DialogTitle>
          <DialogDescription>Hồ sơ báo cáo xếp theo giai đoạn, từ trên xuống.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>
              Tên giai đoạn
              <RequiredMark />
            </Label>
            <Input
              value={name}
              placeholder="VD: Pháp lý & Giấy phép"
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div className="space-y-1.5">
            <Label>Diễn giải / nơi thực hiện</Label>
            <Input
              value={location}
              placeholder="VD: Việt Nam — trước khi đặt hàng"
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>
        </div>

        <DialogFooter className="gap-2 sm:justify-between">
          <div>
            {phase && (
              <Button
                type="button"
                variant="outline"
                className="text-destructive hover:text-destructive"
                disabled={pending}
                title={docCount > 0 ? 'Giai đoạn còn hồ sơ, chưa xóa được' : ''}
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
