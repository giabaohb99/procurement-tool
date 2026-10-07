import { Loader2 } from 'lucide-react'
import { useRef, useState } from 'react'

import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { Textarea } from '@/shared/ui/textarea'
import { toDateInputValue } from '@/shared/utils/format-date'
import { useTransitionLaborContract } from '../hooks/use-employee-labor-contracts'
import type { LaborContract } from '../types/labor-contract'
import { validateTransitionInput, type TransitionSpec } from '../utils/labor-contract-rules'

export interface PendingTransition {
  row: LaborContract
  spec: TransitionSpec
}

interface LaborContractTransitionDialogProps {
  /** `null` = đóng. */
  pending: PendingTransition | null
  employeeId: number
  onClose: () => void
}

/**
 * Hộp hỏi ngày + lý do khi đổi trạng thái (Ký / Hủy / Chấm dứt). Ký chỉ cần ngày ký — KHÔNG đòi tệp.
 * Cố ý KHÔNG dùng `<form>`: hộp nằm dưới `<form>` hồ sơ nên một form lồng sẽ làm submit nổi bọt lên trên.
 */
export function LaborContractTransitionDialog({ pending, employeeId, onClose }: LaborContractTransitionDialogProps) {
  return (
    <Dialog open={pending !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        {pending && <TransitionBody pending={pending} employeeId={employeeId} onClose={onClose} />}
      </DialogContent>
    </Dialog>
  )
}

function TransitionBody({ pending, employeeId, onClose }: { pending: PendingTransition; employeeId: number; onClose: () => void }) {
  const { row, spec } = pending
  const mutation = useTransitionLaborContract(employeeId)
  const sending = useRef(false)
  const [date, setDate] = useState(spec.dateLabel ? toDateInputValue(new Date()) : '')
  const [reason, setReason] = useState('')
  const [error, setError] = useState<string | null>(null)

  function handleConfirm() {
    if (sending.current) return
    const problem = validateTransitionInput(spec, { date, reason }, row.start_date)
    setError(problem)
    if (problem) return
    sending.current = true
    mutation.mutate(
      {
        id: row.id,
        payload: {
          to_status: spec.toStatus,
          date: spec.dateLabel ? date : null,
          reason: spec.needsReason ? reason.trim() : '',
        },
      },
      {
        onSuccess: onClose,
        onSettled: () => {
          sending.current = false
        },
      },
    )
  }

  return (
    <>
      <DialogHeader>
        <DialogTitle>{spec.actionLabel}</DialogTitle>
        <DialogDescription>Hợp đồng {row.contract_no || row.code}</DialogDescription>
      </DialogHeader>
      <div className="space-y-3">
        {spec.dateLabel && (
          <div className="space-y-1.5">
            <Label>{spec.dateLabel} *</Label>
            <DatePicker value={date} onChange={setDate} clearable={false} />
          </div>
        )}
        {spec.needsReason && (
          <div className="space-y-1.5">
            <Label htmlFor="labor-contract-reason">{spec.reasonLabel} *</Label>
            <Textarea id="labor-contract-reason" rows={3} maxLength={500} value={reason}
              onChange={(e) => setReason(e.target.value)} />
          </div>
        )}
        {spec.danger && (
          <p className="text-xs text-muted-foreground">Thao tác này không hoàn tác được.</p>
        )}
        {error && <p role="alert" className="text-sm text-destructive">{error}</p>}
      </div>
      <DialogFooter>
        <Button type="button" variant="outline" onClick={onClose}>Đóng</Button>
        <Button type="button" variant={spec.danger ? 'destructive' : 'default'} disabled={mutation.isPending}
          onClick={handleConfirm}>
          {mutation.isPending && <Loader2 className="size-4 animate-spin" />}
          Xác nhận
        </Button>
      </DialogFooter>
    </>
  )
}
