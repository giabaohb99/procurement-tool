import { Loader2, Trash2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { confirm } from '@/shared/ui/confirm-dialog'
import {
  Dialog,
  DialogContent,
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
import { Textarea } from '@/shared/ui/textarea'
import type { ReportDocPayload } from '../../api/survey-request-report-api'
import {
  REPORT_DOC_IDLE,
  REPORT_DOC_STATUS_LABELS,
  type SurveyReportDoc,
  type SurveyRequestReport,
} from '../../types/survey-request-report'

interface SurveyReportDocDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** null = thêm mới. */
  doc: SurveyReportDoc | null
  report: SurveyRequestReport
  /** Giai đoạn/nút đang lọc — điền sẵn cho hồ sơ mới. */
  defaultPhaseId: number
  defaultItemId: number
  pending: boolean
  onSave: (docId: number | undefined, payload: ReportDocPayload) => Promise<unknown>
  onDelete: (docId: number) => Promise<unknown>
}

function buildDraft(
  doc: SurveyReportDoc | null,
  defaultPhaseId: number,
  defaultItemId: number,
): ReportDocPayload {
  return doc
    ? {
        title: doc.title,
        description: doc.description,
        phase_id: doc.phase_id,
        item_id: doc.item_id,
        required: doc.required,
        status: doc.status,
        file_note: doc.file_note,
        depends: [...doc.depends],
      }
    : {
        title: '',
        description: '',
        phase_id: defaultPhaseId,
        item_id: defaultItemId,
        required: true,
        status: REPORT_DOC_IDLE,
        file_note: '',
        depends: [],
      }
}

/**
 * Thêm / sửa một HỒ SƠ của khối báo cáo. Theo case C-01: chỉ đóng bằng Hủy/X,
 * chặn Esc + click ra ngoài, form đang dở thì hỏi xác nhận trước khi đóng.
 * Không dùng `<form>` — Enter trong ô nhập không được submit hộ (duoc-CR-317).
 */
export function SurveyReportDocDialog({
  open,
  onOpenChange,
  doc,
  report,
  defaultPhaseId,
  defaultItemId,
  pending,
  onSave,
  onDelete,
}: SurveyReportDocDialogProps) {
  const [draft, setDraft] = useState<ReportDocPayload>(() =>
    buildDraft(doc, defaultPhaseId, defaultItemId),
  )
  const [initial, setInitial] = useState(draft)
  //  Chặn bấm trùng trong cùng một nhịp — `disabled={pending}` chỉ đúng ở lần
  //  render sau (bẫy duoc-CR-317).
  const once = useSingleFlight()

  //  Nạp lại mỗi lần MỞ: cùng component dùng cho cả Thêm lẫn Sửa, không reset
  //  thì lần mở sau còn nguyên dữ liệu lần trước. Reset ngay trong lúc render
  //  (mẫu `useHasChanged`), không qua effect — đỡ một khung hình dữ liệu cũ.
  const openChanged = useHasChanged(open)
  if (openChanged && open) {
    const next = buildDraft(doc, defaultPhaseId, defaultItemId)
    setDraft(next)
    setInitial(next)
  }

  const isDirty = JSON.stringify(draft) !== JSON.stringify(initial)

  const attemptClose = async () => {
    if (pending) return
    if (
      isDirty &&
      !(await confirm({ message: 'Bạn có thay đổi chưa lưu. Đóng và bỏ các thay đổi này?' }))
    )
      return
    onOpenChange(false)
  }

  const patch = (changes: Partial<ReportDocPayload>) =>
    setDraft((current) => ({ ...current, ...changes }))

  const handleSave = () =>
    once(async () => {
      if (!draft.title.trim()) {
        toast.error('Nhập tiêu đề hồ sơ')
        return
      }
      await onSave(doc?.id, { ...draft, title: draft.title.trim() })
      onOpenChange(false)
    })

  const handleDelete = () =>
    once(async () => {
      if (!doc) return
      if (
        !(await confirm({
          message: `Xóa hồ sơ "${doc.title}"? Hồ sơ khác đang chờ nó sẽ được mở khóa.`,
        }))
      )
        return
      await onDelete(doc.id)
      onOpenChange(false)
    })

  //  Ứng viên tiên quyết: mọi hồ sơ khác cùng phiếu (backend chặn vòng lặp).
  const dependCandidates = report.docs.filter((other) => other.id !== doc?.id)

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (next) onOpenChange(true)
        else void attemptClose()
      }}
    >
      <DialogContent
        className="sm:max-w-xl"
        onEscapeKeyDown={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
        onPointerDownOutside={(e) => e.preventDefault()}
      >
        <DialogHeader>
          <DialogTitle>{doc ? 'Chỉnh sửa hồ sơ' : 'Thêm hồ sơ mới'}</DialogTitle>
        </DialogHeader>

        <div className="max-h-[65dvh] space-y-4 overflow-y-auto pr-1">
          <div className="space-y-1.5">
            <Label>
              Tiêu đề hồ sơ
              <RequiredMark />
            </Label>
            <Input
              value={draft.title}
              placeholder="VD: Giấy phép nhập khẩu tiền chất"
              onChange={(e) => patch({ title: e.target.value })}
            />
          </div>

          <div className="space-y-1.5">
            <Label>Mô tả chi tiết</Label>
            <Textarea
              rows={3}
              value={draft.description}
              placeholder="Cơ quan cấp, căn cứ pháp lý, thời gian xử lý, lưu ý…"
              onChange={(e) => patch({ description: e.target.value })}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Dòng hàng</Label>
              <Select
                value={String(draft.item_id)}
                onValueChange={(value) => patch({ item_id: Number(value) })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="0">Chung (mọi dòng hàng)</SelectItem>
                  {report.items.map((item) => (
                    <SelectItem key={item.id} value={String(item.id)}>
                      {item.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Trạng thái</Label>
              <Select
                value={String(draft.status)}
                onValueChange={(value) => patch({ status: Number(value) })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(REPORT_DOC_STATUS_LABELS).map(([code, label]) => (
                    <SelectItem key={code} value={code}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Giai đoạn</Label>
              <Select
                value={String(draft.phase_id)}
                onValueChange={(value) => patch({ phase_id: Number(value) })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {report.phases.map((phase, index) => (
                    <SelectItem key={phase.id} value={String(phase.id)}>
                      {index + 1}. {phase.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Bắt buộc?</Label>
              <Select
                value={draft.required ? '1' : '0'}
                onValueChange={(value) => patch({ required: value === '1' })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Bắt buộc</SelectItem>
                  <SelectItem value="0">Không bắt buộc</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Tệp đính kèm (tên tệp hoặc link)</Label>
            <Input
              value={draft.file_note}
              placeholder="VD: GP-tienchat.pdf · hoặc dán link Drive"
              onChange={(e) => patch({ file_note: e.target.value })}
            />
          </div>

          <div className="space-y-1.5">
            <Label>Tiên quyết — hồ sơ phải xong trước</Label>
            <div className="max-h-40 space-y-1 overflow-y-auto rounded-md border bg-muted/30 p-2.5">
              {dependCandidates.length === 0 && (
                <p className="text-xs text-muted-foreground">Chưa có hồ sơ khác</p>
              )}
              {dependCandidates.map((other) => (
                <label
                  key={other.id}
                  className="flex cursor-pointer items-center gap-2 text-sm"
                >
                  <Checkbox
                    checked={draft.depends.includes(other.id)}
                    onCheckedChange={(checked) =>
                      patch({
                        depends: checked
                          ? [...draft.depends, other.id]
                          : draft.depends.filter((id) => id !== other.id),
                      })
                    }
                  />
                  <span className="truncate">{other.title}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <DialogFooter className="gap-2 sm:justify-between">
          <div>
            {doc && (
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
