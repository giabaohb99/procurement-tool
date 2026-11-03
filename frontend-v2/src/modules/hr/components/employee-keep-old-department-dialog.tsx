import { Building2 } from 'lucide-react'

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { Button } from '@/shared/ui/button'

interface EmployeeKeepOldDepartmentDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  oldDepartmentName: string
  newDepartmentName: string
  pending?: boolean
  /** `true` = giữ phòng cũ làm kiêm nhiệm, `false` = gỡ phòng cũ. */
  onChoose: (keepOld: boolean) => void
}

/**
 * bao-CR-709 — đổi phòng chính thì hỏi phòng CŨ giữ lại làm kiêm nhiệm hay gỡ.
 *
 * Mặc định là GỠ (nút chính, nhận Enter): trước đây phòng cũ âm thầm thành kiêm nhiệm nên người
 * vừa chuyển phòng vẫn thấy phiếu của phòng cũ — ca NSU012 chuyển về nhà máy 31/10/2026.
 */
export function EmployeeKeepOldDepartmentDialog({
  open,
  onOpenChange,
  oldDepartmentName,
  newDepartmentName,
  pending = false,
  onChoose,
}: EmployeeKeepOldDepartmentDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={(next) => !pending && onOpenChange(next)}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <Building2 className="size-5 text-primary" />
            Giữ phòng cũ làm kiêm nhiệm?
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-2 text-sm">
              <p>
                Phòng chính đổi từ <strong>{oldDepartmentName}</strong> sang{' '}
                <strong>{newDepartmentName}</strong>.
              </p>
              <p>
                Giữ phòng cũ làm kiêm nhiệm thì người này <strong>vẫn thấy</strong> phiếu và dữ
                liệu của phòng <strong>{oldDepartmentName}</strong>. Chỉ giữ khi họ thật sự còn phụ
                trách phòng đó.
              </p>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={pending}>Hủy</AlertDialogCancel>
          <Button variant="outline" disabled={pending} onClick={() => onChoose(true)}>
            Giữ làm kiêm nhiệm
          </Button>
          <Button autoFocus disabled={pending} onClick={() => onChoose(false)}>
            Không, gỡ phòng cũ
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
