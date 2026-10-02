import { useState } from 'react'

import { useAccessSubjectOptions } from '@/modules/hr/hooks/use-access-subject-options'
import { AccessSubjectPicker } from '@/shared/access-subject/access-subject-picker'
import { EFFECT } from '@/shared/access-subject/subject-kind'
import type { MixedSubject } from '@/shared/access-subject/subject-kind'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { Textarea } from '@/shared/ui/textarea'
import { useGrantReportAccess } from '../hooks/use-report-access'
import type { ReportAccessItem } from '../types/report-access'
import { ReportAccessGrantList } from './report-access-grant-list'

const REASON_MAX = 500

interface ReportAccessDialogProps {
  /** Báo cáo đang sửa — `null` = đóng hộp. */
  report: ReportAccessItem | null
  onOpenChange: (open: boolean) => void
}

/**
 * Hộp «Sửa quyền xem báo cáo»: khối 1 (`ReportAccessGrantList`) liệt kê + thu
 * hồi dòng đang sống, khối 2 gán thêm. Được gán chỉ MỞ báo cáo — số liệu bên
 * trong vẫn theo quyền phân hệ gốc + phạm vi dữ liệu (gác kép, phase-02 kế
 * hoạch `plans/261002-0836-phan-quyen-tung-bao-cao`).
 */
export function ReportAccessDialog({ report, onOpenChange }: ReportAccessDialogProps) {
  return (
    <Dialog open={report !== null} onOpenChange={onOpenChange}>
      {/* Khóa chiều cao hộp, chỉ thân cuộn — cùng khuôn `document-access-dialog.tsx`:
          nút Đóng không được trôi tuột xuống dưới màn hình khi danh sách dài. */}
      <DialogContent className="flex max-h-[85dvh] flex-col overflow-hidden sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Quyền xem «{report?.label}»</DialogTitle>
          <DialogDescription>
            Được gán chỉ mở báo cáo; số liệu vẫn theo quyền phân hệ gốc. Cấm thắng cho phép.
          </DialogDescription>
        </DialogHeader>

        {report && (
          <div className="-mx-6 min-h-0 flex-1 space-y-4 overflow-y-auto px-6">
            <ReportAccessGrantList grants={report.grants} />
            <AddGrantForm reportKey={report.key} />
          </div>
        )}

        <DialogFooter className="shrink-0 border-t pt-4">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Đóng
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface AddGrantFormProps {
  reportKey: number
}

/** Khối 2 — chọn chủ thể + chiều tác động + lý do, gán được một lượt nhiều người. */
function AddGrantForm({ reportKey }: AddGrantFormProps) {
  const grant = useGrantReportAccess(reportKey)
  const { options, loading } = useAccessSubjectOptions()
  const [subjects, setSubjects] = useState<MixedSubject[]>([])
  const [effect, setEffect] = useState(String(EFFECT.allow))
  const [reason, setReason] = useState('')

  function handleAdd() {
    if (subjects.length === 0) return
    grant.mutate(
      { subjects, effect: Number(effect), reason: reason.trim() },
      {
        onSuccess: () => {
          setSubjects([])
          setReason('')
        },
      },
    )
  }

  return (
    <div className="space-y-3 border-t pt-4">
      <div className="space-y-1.5">
        <Label>Thêm người · phòng ban · pháp nhân · vai trò</Label>
        <AccessSubjectPicker
          value={subjects}
          onChange={setSubjects}
          options={options}
          loading={loading}
        />
      </div>

      <div className="space-y-1.5">
        <Label>Chiều tác động</Label>
        <RadioGroup value={effect} onValueChange={setEffect} className="flex gap-4">
          <label className="flex items-center gap-2 text-sm">
            <RadioGroupItem value={String(EFFECT.allow)} />
            Cho phép
          </label>
          <label className="flex items-center gap-2 text-sm">
            <RadioGroupItem value={String(EFFECT.deny)} />
            Cấm
          </label>
        </RadioGroup>
      </div>

      <div className="space-y-1">
        <Label htmlFor="report-access-reason">Lý do</Label>
        <Textarea
          id="report-access-reason"
          value={reason}
          //  Chặn ngay tại state, không trông cậy một mình `maxLength` của
          //  trình duyệt — bài kiểm gõ 501 ký tự phải thấy giá trị bị cắt.
          onChange={(event) => setReason(event.target.value.slice(0, REASON_MAX))}
          maxLength={REASON_MAX}
          rows={2}
          placeholder="Không bắt buộc"
        />
        <p className="text-right text-xs text-muted-foreground">
          {reason.length}/{REASON_MAX}
        </p>
      </div>

      <Button type="button" onClick={handleAdd} disabled={subjects.length === 0 || grant.isPending}>
        Thêm{subjects.length > 0 ? ` (${subjects.length})` : ''}
      </Button>
    </div>
  )
}
