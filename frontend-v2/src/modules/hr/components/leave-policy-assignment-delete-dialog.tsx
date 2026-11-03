import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { useDeleteLeavePolicyAssignment } from '../hooks/use-leave-policy'
import { useSingleFlight } from '../hooks/use-single-flight'
import type { LeavePolicyAssignment } from '../types/leave-policy'
import { formatPolicyRange } from '../utils/leave-policy-display'

interface LeavePolicyAssignmentDeleteDialogProps {
  /** Phân bổ sắp xóa; `null` = đóng hộp. */
  assignment: LeavePolicyAssignment | null
  onClose: () => void
}

/**
 * Hộp XÁC NHẬN XÓA phân bổ (duoc-CR-717), kèm ô "Tính lại hạn mức năm nay" MẶC ĐỊNH BẬT (D3a): tick thì
 * các loại nghỉ của gói quay về hạn mức của loại nghỉ; bỏ tick thì quỹ đã cấp giữ nguyên.
 * Không dùng `confirm()` dùng chung vì hộp đó không chứa được ô tick.
 */
export function LeavePolicyAssignmentDeleteDialog({ assignment, onClose }: LeavePolicyAssignmentDeleteDialogProps) {
  return (
    <Dialog open={assignment !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        {assignment && <DeleteForm assignment={assignment} onClose={onClose} />}
      </DialogContent>
    </Dialog>
  )
}

function DeleteForm({ assignment, onClose }: { assignment: LeavePolicyAssignment; onClose: () => void }) {
  const [recalc, setRecalc] = useState(true)
  const remove = useDeleteLeavePolicyAssignment()
  const runOnce = useSingleFlight()

  const submit = () =>
    runOnce((release) =>
      remove.mutate({ id: assignment.id, recalc }, { onSuccess: onClose, onSettled: release }),
    )

  return (
    <>
      <DialogHeader>
        <DialogTitle>Xóa phân bổ chính sách?</DialogTitle>
        <DialogDescription>
          {assignment.employee_name} · {assignment.policy_name} ·{' '}
          {formatPolicyRange(assignment.effective_from, assignment.effective_to)}. Muốn giữ lịch sử thì dùng{' '}
          <strong>Kết thúc</strong> thay vì xóa.
        </DialogDescription>
      </DialogHeader>

      <label className="flex items-start gap-2 text-sm">
        <Checkbox checked={recalc} onCheckedChange={(v) => setRecalc(v === true)} className="mt-0.5" />
        <span>
          Tính lại hạn mức năm nay cho quỹ đã cấp
          <span className="block text-xs text-muted-foreground">
            Các loại nghỉ của chính sách quay về hạn mức của loại nghỉ. Bỏ tick thì quỹ đã cấp giữ nguyên.
          </span>
        </span>
      </label>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onClose}>
          Hủy
        </Button>
        <Button type="button" variant="destructive" onClick={submit} disabled={remove.isPending}>
          Xóa phân bổ
        </Button>
      </DialogFooter>
    </>
  )
}
