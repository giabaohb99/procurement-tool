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
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import type { DocumentAccessInput } from '../types/document-access'

/** Phần khai lại được cho cả cụm — đối tượng và chiều tác động thì không. */
type GroupPatch = Pick<DocumentAccessInput, 'can_write' | 'can_delete' | 'valid_to' | 'reason'>

interface AccessGroupEditDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Cụm đang sửa là cụm CẤM — đổi chữ cho khỏi nhầm với cụm cho phép. */
  deny: boolean
  /** Số đối tượng trong cụm, để nói rõ thay đổi này chạm tới bao nhiêu người. */
  count: number
  onApply: (patch: GroupPatch) => void
}

/**
 * Sửa BỘ QUYỀN của cả một cụm (cho phép / không cho phép).
 *
 * Chỉ sửa được phần dùng chung: được làm gì, hết hạn, lý do. Muốn đổi đối tượng
 * thì bỏ badge rồi khai lại; muốn đổi chiều tác động thì đó là cụm khác — hai
 * việc đó nằm ngoài đây cho khỏi biến hộp này thành form khai mới thứ hai.
 */
export function AccessGroupEditDialog({
  open,
  onOpenChange,
  deny,
  count,
  onApply,
}: AccessGroupEditDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Sửa quyền cụm {deny ? 'không cho phép' : 'cho phép'}</DialogTitle>
          <DialogDescription>
            Áp cho cả {count} đối tượng trong cụm. Muốn khác nhau thì tách thành cụm riêng.
          </DialogDescription>
        </DialogHeader>

        {/* Ô nhập nằm trong component con nên đóng hộp là chữ đã gõ tự mất. */}
        <GroupForm deny={deny} onCancel={() => onOpenChange(false)} onApply={onApply} />
      </DialogContent>
    </Dialog>
  )
}

interface GroupFormProps {
  deny: boolean
  onCancel: () => void
  onApply: (patch: GroupPatch) => void
}

function GroupForm({ deny, onCancel, onApply }: GroupFormProps) {
  const [canWrite, setCanWrite] = useState(false)
  const [canDelete, setCanDelete] = useState(false)
  const [validTo, setValidTo] = useState('')
  const [reason, setReason] = useState('')

  return (
    <>
      <div className="space-y-4">
        <div className="space-y-2">
          <Label>Được làm gì</Label>
          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 text-sm text-muted-foreground">
              <Checkbox checked disabled />
              Xem {deny && '(chặn cả việc nhìn thấy)'}
            </label>
            <label className="flex items-center gap-2 text-sm">
              <Checkbox
                checked={canWrite}
                onCheckedChange={(value) => setCanWrite(value === true)}
              />
              Sửa
            </label>
            <label className="flex items-center gap-2 text-sm">
              <Checkbox
                checked={canDelete}
                onCheckedChange={(value) => setCanDelete(value === true)}
              />
              Xóa
            </label>
          </div>
        </div>

        <div className="space-y-2">
          <Label>Hết hạn</Label>
          <DatePicker value={validTo} onChange={setValidTo} />
          <p className="text-xs text-muted-foreground">Trống = không đặt hạn.</p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="group-reason">Lý do</Label>
          <Input
            id="group-reason"
            placeholder="VD: Phối hợp rà soát quy chế"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </div>
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Hủy
        </Button>
        <Button
          type="button"
          onClick={() =>
            onApply({
              can_write: canWrite,
              can_delete: canDelete,
              valid_to: validTo || null,
              reason: reason.trim(),
            })
          }
        >
          Áp cho cả cụm
        </Button>
      </DialogFooter>
    </>
  )
}
