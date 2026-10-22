import { Loader2, ShieldAlert } from 'lucide-react'
import type { ReactNode } from 'react'

import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { Button } from '@/shared/ui/button'
import { useEmployeePendingWork } from '../hooks/use-employee-pending-work'
import { EmployeePendingWorkPanel } from './employee-pending-work-panel'

interface EmployeePendingWorkConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  employeeId: number
  title: string
  /** Hệ quả của thao tác (khóa tài khoản, đăng xuất…). */
  description: ReactNode
  confirmLabel: string
  pending?: boolean
  onConfirm: () => void
}

/**
 * Hộp «kiểm việc treo» trước khi khóa tài khoản / lưu hồ sơ sang nghỉ việc (duoc-CR-665, V0-4).
 *
 * CHO QUA CÓ XÁC NHẬN (không chặn cứng): tài liệu không đòi chặn, và có người nghỉ đột xuất
 * cần khóa ngay. Còn việc treo thì nút xác nhận đổi thành «Vẫn khóa…» để người bấm biết mình
 * đang để phiếu kẹt; chuyển hết rồi thì nút trở lại bình thường (danh sách làm mới sau mỗi lần chuyển).
 */
export function EmployeePendingWorkConfirmDialog({
  open,
  onOpenChange,
  employeeId,
  title,
  description,
  confirmLabel,
  pending = false,
  onConfirm,
}: EmployeePendingWorkConfirmDialogProps) {
  const { data, isLoading } = useEmployeePendingWork(employeeId, open)
  const remaining = (data?.total_tasks ?? 0) + (data?.total_flow_steps ?? 0)

  return (
    <AlertDialog open={open} onOpenChange={(next) => !pending && onOpenChange(next)}>
      <AlertDialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <ShieldAlert className="size-5 text-destructive" />
            {title}
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-2 text-sm">{description}</div>
          </AlertDialogDescription>
        </AlertDialogHeader>

        <EmployeePendingWorkPanel employeeId={employeeId} />

        <AlertDialogFooter>
          <Button type="button" variant="outline" disabled={pending} onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={pending || isLoading}
            onClick={onConfirm}
          >
            {pending && <Loader2 className="size-4 animate-spin" />}
            {remaining > 0 ? `Vẫn ${confirmLabel.toLowerCase()} (còn việc treo)` : confirmLabel}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
