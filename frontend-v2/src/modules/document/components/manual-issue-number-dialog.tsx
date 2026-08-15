import { Loader2 } from 'lucide-react'
import { useId, useState } from 'react'

import { Button } from '@/shared/ui/button'
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
import { Textarea } from '@/shared/ui/textarea'

export function ManualIssueNumberDialog({
  open,
  currentNumber,
  pending,
  onOpenChange,
  onConfirm,
}: {
  open: boolean
  currentNumber: string
  pending: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (values: { issue_number: string; reason: string }) => void
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Chỉnh sửa số hiệu</DialogTitle>
          <DialogDescription>
            Bộ đếm đã cấp không quay lui. Số cũ, số mới và lý do sẽ được giữ trong nhật ký.
          </DialogDescription>
        </DialogHeader>
        {open && (
          <ManualIssueNumberFields
            currentNumber={currentNumber}
            pending={pending}
            onCancel={() => onOpenChange(false)}
            onConfirm={onConfirm}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

function ManualIssueNumberFields({
  currentNumber,
  pending,
  onCancel,
  onConfirm,
}: {
  currentNumber: string
  pending: boolean
  onCancel: () => void
  onConfirm: (values: { issue_number: string; reason: string }) => void
}) {
  const numberId = useId()
  const reasonId = useId()
  const [issueNumber, setIssueNumber] = useState(currentNumber)
  const [reason, setReason] = useState('')
  const ready =
    issueNumber.trim().length > 0 &&
    issueNumber.trim() !== currentNumber &&
    reason.trim().length > 0 &&
    !pending

  return (
    <>
      <div className="space-y-2">
        <Label htmlFor={numberId}>Số hiệu mới</Label>
        <Input
          id={numberId}
          autoFocus
          maxLength={100}
          value={issueNumber}
          onChange={(event) => setIssueNumber(event.target.value)}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor={reasonId}>Lý do chỉnh sửa</Label>
        <Textarea
          id={reasonId}
          rows={3}
          maxLength={1000}
          value={reason}
          placeholder="Ví dụ: điều chỉnh theo sổ giấy đã đối chiếu"
          onChange={(event) => setReason(event.target.value)}
        />
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onCancel}>
          Hủy
        </Button>
        <Button
          disabled={!ready}
          onClick={() => onConfirm({ issue_number: issueNumber.trim(), reason: reason.trim() })}
        >
          {pending && <Loader2 className="size-4 animate-spin" />}
          Lưu số hiệu
        </Button>
      </DialogFooter>
    </>
  )
}
