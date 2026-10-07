// duoc-CR-611 (07/10/2026) — «Thêm hồ sơ» khi khối Báo cáo thực hiện còn TRỐNG. Trước đây khối
// trống chỉ có «Khởi tạo báo cáo mẫu» (đổ cả bộ mẫu) hoặc «Thêm giai đoạn»; muốn ghi đúng MỘT
// hồ sơ cho MỘT dòng hàng thì phải đổ mẫu rồi xóa bớt. Hộp này chọn dòng hàng + giai đoạn mặc
// định + tên; backend dựng khung (5 giai đoạn + nút theo dòng, không đổ mẫu) rồi thêm hồ sơ đó.
import { Loader2 } from 'lucide-react'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { useReportFirstDocOptions } from '../../hooks/use-survey-request-report'
import type {
  ReportFirstDocPayload,
  ReportOwnerEntity,
} from '../../types/survey-request-report'

/** Giá trị ô chọn dòng hàng của hồ sơ CHUNG — trùng `line_id = 0` gửi lên backend. */
const COMMON_LINE = '0'
/** Trần độ dài tên hồ sơ — khớp `max_length=255` của `ReportFirstDocIn`. */
const TITLE_MAX = 255

interface SurveyReportFirstDocDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  ownerId: number
  entity: ReportOwnerEntity
  /** «phiếu» / «đơn» — chữ của dòng Chung. */
  ownerLabel: string
  pending: boolean
  onSave: (payload: ReportFirstDocPayload) => Promise<unknown>
}

export function SurveyReportFirstDocDialog({
  open,
  onOpenChange,
  ownerId,
  entity,
  ownerLabel,
  pending,
  onSave,
}: SurveyReportFirstDocDialogProps) {
  const options = useReportFirstDocOptions(ownerId, entity, open)
  const [title, setTitle] = useState('')
  const [lineId, setLineId] = useState(COMMON_LINE)
  const [phaseOrder, setPhaseOrder] = useState('0')
  const once = useSingleFlight()

  //  Reset ngay trong lúc render mỗi lần MỞ (mẫu `useHasChanged`) — không lóe dữ liệu lần trước.
  const openChanged = useHasChanged(open)
  if (openChanged && open) {
    setTitle('')
    setLineId(COMMON_LINE)
    setPhaseOrder('0')
  }

  const lines = options.data?.lines ?? []
  const phases = options.data?.phases ?? []
  const isDirty = title !== '' || lineId !== COMMON_LINE || phaseOrder !== '0'

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
      const trimmed = title.trim()
      if (!trimmed) {
        toast.error('Nhập tên hồ sơ')
        return
      }
      await onSave({ title: trimmed, line_id: Number(lineId), phase_order: Number(phaseOrder) })
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
        className="sm:max-w-lg"
        onEscapeKeyDown={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
        onPointerDownOutside={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>Thêm hồ sơ đầu tiên</DialogTitle>
          <DialogDescription>
            Chọn dòng hàng và giai đoạn cho hồ sơ. Hệ thống dựng sẵn 5 giai đoạn mặc định và một
            nút cho mỗi dòng hàng, KHÔNG đổ bộ hồ sơ mẫu — chi tiết (ngày, người làm, tiên quyết…)
            sửa sau ở nút bút chì trên hồ sơ.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="first-doc-line">Dòng hàng</Label>
            <Select value={lineId} onValueChange={setLineId} disabled={options.isLoading}>
              <SelectTrigger id="first-doc-line" className="w-full" aria-label="Dòng hàng">
                <SelectValue placeholder="Đang tải dòng hàng…" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={COMMON_LINE}>Chung (cả {ownerLabel})</SelectItem>
                {lines.map((line) => (
                  <SelectItem key={line.line_id} value={String(line.line_id)}>
                    {line.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {!options.isLoading && lines.length === 0 && (
              <p className="text-xs text-muted-foreground">
                {ownerLabel === 'đơn' ? 'Đơn' : 'Phiếu'} chưa có dòng hàng nào — hồ sơ sẽ vào
                Chung.
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="first-doc-phase">Giai đoạn</Label>
            <Select value={phaseOrder} onValueChange={setPhaseOrder} disabled={options.isLoading}>
              <SelectTrigger id="first-doc-phase" className="w-full" aria-label="Giai đoạn">
                <SelectValue placeholder="Đang tải giai đoạn…" />
              </SelectTrigger>
              <SelectContent>
                {phases.map((phase) => (
                  <SelectItem key={phase.order} value={String(phase.order)}>
                    {phase.order + 1}. {phase.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="first-doc-title">
              Tên hồ sơ
              <RequiredMark />
            </Label>
            <Input
              id="first-doc-title"
              value={title}
              maxLength={TITLE_MAX}
              placeholder="VD: Giấy phép nhập khẩu chuyên ngành"
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => {
                //  Enter = lưu, và chặn mặc định để không submit form cha (bẫy biểu mẫu CR-317).
                if (e.key === 'Enter') {
                  e.preventDefault()
                  void handleSave()
                }
              }}
            />
          </div>
        </div>

        <DialogFooter className="gap-2">
          <Button type="button" variant="outline" disabled={pending} onClick={attemptClose}>
            Hủy
          </Button>
          <Button
            type="button"
            disabled={pending || options.isLoading || options.isError}
            onClick={handleSave}
          >
            {pending && <Loader2 className="animate-spin" />}
            Thêm hồ sơ
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
