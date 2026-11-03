import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { toDateInputValue } from '@/shared/utils/format-date'
import { useUpdateLeavePolicyAssignment } from '../hooks/use-leave-policy'
import { useSingleFlight } from '../hooks/use-single-flight'
import type { LeavePolicyAssignment } from '../types/leave-policy'
import { formatPolicyRange } from '../utils/leave-policy-display'

interface LeavePolicyAssignmentEndDialogProps {
  /** Phân bổ đang sửa; `null` = đóng hộp. */
  assignment: LeavePolicyAssignment | null
  onClose: () => void
}

/**
 * Hộp KẾT THÚC một phân bổ (duoc-CR-717) — chỉ đổi "Đến ngày" (để trống = không thời hạn, tức mở lại).
 * Kéo dài mà chồng lên lượt sau thì backend trả 409 (câu dựng sẵn, http client tự bật thông báo).
 */
export function LeavePolicyAssignmentEndDialog({ assignment, onClose }: LeavePolicyAssignmentEndDialogProps) {
  return (
    <Dialog open={assignment !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        {assignment && <EndForm assignment={assignment} onClose={onClose} />}
      </DialogContent>
    </Dialog>
  )
}

function EndForm({ assignment, onClose }: { assignment: LeavePolicyAssignment; onClose: () => void }) {
  //  Gợi ý hôm nay, nhưng không sớm hơn ngày bắt đầu (phân bổ "Sắp tới" thì gợi ý chính ngày bắt đầu).
  const today = toDateInputValue(new Date())
  const [to, setTo] = useState(
    assignment.effective_to ?? (today < assignment.effective_from ? assignment.effective_from : today),
  )
  const [recalc, setRecalc] = useState(true)
  const update = useUpdateLeavePolicyAssignment()
  const runOnce = useSingleFlight()
  const rangeError = to && to < assignment.effective_from ? '"Đến ngày" không được trước "Từ ngày".' : ''

  const submit = () =>
    runOnce((release) => {
      if (rangeError) return release()
      update.mutate(
        { id: assignment.id, payload: { effective_to: to || null, recalc_current_year: recalc } },
        { onSuccess: onClose, onSettled: release },
      )
    })

  return (
    <>
      <DialogHeader>
        <DialogTitle>Kết thúc phân bổ</DialogTitle>
        <DialogDescription>
          {assignment.employee_name} · {assignment.policy_name} · đang là{' '}
          {formatPolicyRange(assignment.effective_from, assignment.effective_to)}
        </DialogDescription>
      </DialogHeader>

      <div className="space-y-4">
        <div className="space-y-1.5">
          <Label>Đến ngày</Label>
          <DatePicker value={to} onChange={setTo} placeholder="Không thời hạn" />
          {rangeError ? (
            <p className="text-xs text-destructive">{rangeError}</p>
          ) : (
            <p className="text-xs text-muted-foreground">
              Ngày cuối cùng chính sách còn áp. Để trống = không thời hạn.
            </p>
          )}
        </div>
        <label className="flex items-start gap-2 text-sm">
          <Checkbox checked={recalc} onCheckedChange={(v) => setRecalc(v === true)} className="mt-0.5" />
          <span>
            Tính lại hạn mức năm nay cho quỹ đã cấp
            <span className="block text-xs text-muted-foreground">
              Tháng sau ngày kết thúc quay về hạn mức của loại nghỉ (hoặc chính sách kế tiếp).
            </span>
          </span>
        </label>
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onClose}>
          Hủy
        </Button>
        <Button type="button" onClick={submit} disabled={Boolean(rangeError) || update.isPending}>
          Lưu
        </Button>
      </DialogFooter>
    </>
  )
}
