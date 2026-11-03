import { useMemo, useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { toDateInputValue } from '@/shared/utils/format-date'
import { useEmployees } from '../hooks/use-employees'
import { useLeaveTypes } from '../hooks/use-leave'
import {
  useActiveLeavePolicies,
  useCreateLeavePolicyAssignment,
  useLeavePolicyPreview,
} from '../hooks/use-leave-policy'
import { useSingleFlight } from '../hooks/use-single-flight'
import type { PolicyPreviewPayload } from '../types/leave-policy'
import { buildLeaveTypeNameLookup } from '../utils/leave-policy-display'
import { LeavePolicyAssignFields } from './leave-policy-assign-fields'
import { LeavePolicyAssignPreview } from './leave-policy-assign-preview'

interface LeavePolicyAssignDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Hộp PHÂN BỔ CHÍNH SÁCH CHO MỘT NGƯỜI (duoc-CR-717). Điền xong là tự xem trước (`/preview`) hạn mức năm
 * nay trước → sau; Lưu chỉ mở khi xem trước sạch (không chồng ngày, không tự phân bổ cho mình).
 * Ô "Tính lại hạn mức năm nay" MẶC ĐỊNH BẬT (D3a); bỏ tick thì quỹ đã cấp giữ nguyên.
 */
export function LeavePolicyAssignDialog({ open, onOpenChange }: LeavePolicyAssignDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/*  Không `max-h` / `overflow-y-auto` ở đây: lớp phủ của `DialogContent` đã tự cuộn (xem `dialog.tsx`). */}
      <DialogContent className="sm:max-w-xl">
        {/*  Thân hộp tách riêng để mỗi lần MỞ là một bộ ô mới — Radix gỡ nội dung khi đóng. */}
        {open && <AssignForm onClose={() => onOpenChange(false)} />}
      </DialogContent>
    </Dialog>
  )
}

function AssignForm({ onClose }: { onClose: () => void }) {
  const { can } = usePermission()
  const canPickEmployee = can('employee', 'read')
  const [employeeId, setEmployeeId] = useState(0)
  const [policyId, setPolicyId] = useState(0)
  const [from, setFrom] = useState(() => toDateInputValue(new Date()))
  const [to, setTo] = useState('')
  const [note, setNote] = useState('')
  const [recalc, setRecalc] = useState(true)
  const [closePrevious, setClosePrevious] = useState(false)

  const { data: employeeData } = useEmployees(
    { page_size: 1000, is_active: true },
    { enabled: canPickEmployee },
  )
  const employees = useMemo(() => employeeData?.items ?? [], [employeeData])
  const { data: policyData } = useActiveLeavePolicies()
  const { data: typeData } = useLeaveTypes(false)
  const typeName = useMemo(() => buildLeaveTypeNameLookup(typeData?.items), [typeData])

  const rangeError = to && from && to < from ? '"Đến ngày" không được trước "Từ ngày".' : ''
  const ready = employeeId > 0 && policyId > 0 && Boolean(from) && !rangeError
  const previewPayload: PolicyPreviewPayload | null = ready
    ? {
        policy_id: policyId,
        effective_from: from,
        effective_to: to || null,
        close_previous: closePrevious,
        employee_ids: [employeeId],
      }
    : null
  const preview = useLeavePolicyPreview(previewPayload)
  const item = preview.data?.items.find((i) => i.employee_id === employeeId)

  const create = useCreateLeavePolicyAssignment()
  const runOnce = useSingleFlight()
  const canSave =
    ready && !preview.isFetching && !preview.isError && Boolean(item) && !item?.conflict && !create.isPending

  const submit = () =>
    runOnce((release) => {
      if (!canSave) return release()
      create.mutate(
        {
          employee_id: employeeId,
          policy_id: policyId,
          effective_from: from,
          effective_to: to || null,
          note: note.trim(),
          recalc_current_year: recalc,
          close_previous: closePrevious,
        },
        { onSuccess: onClose, onSettled: release },
      )
    })

  return (
    <>
      <DialogHeader>
        <DialogTitle>Phân bổ chính sách nghỉ phép</DialogTitle>
        <DialogDescription>
          Gán một chính sách cho một nhân sự trong khoảng ngày. Loại nghỉ không có trong chính sách vẫn cấp theo hạn
          mức của loại nghỉ.
        </DialogDescription>
      </DialogHeader>

      <LeavePolicyAssignFields
        canPickEmployee={canPickEmployee}
        employees={employees}
        employeeId={employeeId}
        onEmployeeChange={setEmployeeId}
        policies={policyData?.items ?? []}
        policyId={policyId}
        onPolicyChange={setPolicyId}
        from={from}
        onFromChange={setFrom}
        to={to}
        onToChange={setTo}
        rangeError={rangeError}
        note={note}
        onNoteChange={setNote}
        recalc={recalc}
        onRecalcChange={setRecalc}
      />

      <LeavePolicyAssignPreview
        ready={ready}
        isLoading={preview.isFetching}
        isError={preview.isError}
        item={item}
        closePrevious={closePrevious}
        onClosePreviousChange={setClosePrevious}
        typeName={typeName}
      />

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onClose}>
          Hủy
        </Button>
        <Button type="button" onClick={submit} disabled={!canSave}>
          Phân bổ
        </Button>
      </DialogFooter>
    </>
  )
}
