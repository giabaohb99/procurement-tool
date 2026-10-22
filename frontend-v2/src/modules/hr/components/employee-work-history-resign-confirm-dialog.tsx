import { Loader2, ShieldAlert } from 'lucide-react'

import {
  AlertDialog,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { Button } from '@/shared/ui/button'
import { formatDate } from '@/shared/utils/format-date'
import { useEmployeePendingWork } from '../hooks/use-employee-pending-work'
import { EmployeePendingWorkPanel } from './employee-pending-work-panel'

interface EmployeeWorkHistoryResignConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** `from_date` của dòng Thôi việc — ngày sẽ ghi vào `resign_date` của hồ sơ. */
  resignDate: string
  pending?: boolean
  /**
   * Hồ sơ sắp chuyển nghỉ việc (duoc-CR-665, V0-4). Có thì hộp liệt kê việc duyệt người này
   * đang giữ + cho chuyển trước khi khóa; còn việc treo vẫn cho qua (xác nhận), nút đổi nhãn.
   */
  employeeId?: number
  /** Nhãn nút phụ — mặc định «Chỉ lưu dòng» (hộp LƯU dòng mới, phase 04). */
  cancelLabel?: string
  /** Nhãn nút đỏ — mặc định «Lưu và chuyển sang nghỉ việc». */
  confirmLabel?: string
  /**
   * Hành động của nút phụ. Bỏ trống → gọi `onConfirm(false)` (tương thích hộp
   * LƯU dòng cũ: vẫn lưu dòng, chỉ không áp vào hồ sơ). H1 (nút ▶ «Áp vào hồ
   * sơ» trên dòng có sẵn) truyền riêng — ở đó không có khái niệm "lưu dòng",
   * nút phụ phải KHÔNG gọi gì cả, chỉ đóng hộp.
   */
  onCancel?: () => void
  /** `true` = «Lưu và chuyển sang nghỉ việc» → gửi `apply_to_profile:true`. */
  onConfirm: (applyToProfile: boolean) => void
}

/**
 * Hộp xác nhận RIÊNG của dòng «Thôi việc» (Q2) — KHÔNG dùng `confirm()` chung
 * của hộp thêm/sửa, vì hệ quả ở đây nặng hơn một câu hỏi "cập nhật hồ sơ?":
 * khóa tài khoản đăng nhập và đăng xuất khỏi MỌI thiết bị ngay lập tức.
 *
 * Hai nút nói đúng việc — không dùng «Đồng ý»/«Hủy» chung chung — để người bấm
 * nhầm có một lối ra an toàn (chỉ lưu dòng, chưa đụng tới hồ sơ) thay vì chỉ có
 * «Hủy» (không lưu được dòng vừa nhập).
 *
 * Esc / bấm ra ngoài / nút đóng → CHỈ đóng hộp, không gọi `onConfirm`/`onCancel`
 * — người dùng đổi ý thì dòng vừa nhập trong form cha vẫn còn nguyên, chưa gửi gì.
 *
 * Dùng LẠI ở nút ▶ «Áp vào hồ sơ» của từng dòng có sẵn (H1,
 * `employee-tab-work-history.tsx`) với `cancelLabel="Hủy"` +
 * `confirmLabel="Chuyển sang nghỉ việc"` + `onCancel` riêng (không lưu gì).
 */
export function EmployeeWorkHistoryResignConfirmDialog({
  open,
  onOpenChange,
  resignDate,
  pending = false,
  employeeId,
  cancelLabel = 'Chỉ lưu dòng',
  confirmLabel = 'Lưu và chuyển sang nghỉ việc',
  onCancel,
  onConfirm,
}: EmployeeWorkHistoryResignConfirmDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={(next) => !pending && onOpenChange(next)}>
      <AlertDialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <ShieldAlert className="size-5 text-destructive" />
            Chuyển hồ sơ sang nghỉ việc?
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-2 text-sm">
              <p>
                Ngày nghỉ việc ghi vào hồ sơ: <strong>{formatDate(resignDate)}</strong> (lấy từ dòng).
              </p>
              <p>
                Mọi tài khoản đăng nhập của người này sẽ bị <strong>KHÓA</strong> và bị{' '}
                <strong>ĐĂNG XUẤT</strong> khỏi mọi thiết bị ngay lập tức.
              </p>
              <p>Mở lại tài khoản phải làm tay ở tab «Tài khoản».</p>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>

        {employeeId ? <EmployeePendingWorkPanel employeeId={employeeId} /> : null}

        <AlertDialogFooter>
          <Button
            type="button"
            variant="outline"
            disabled={pending}
            onClick={() => (onCancel ? onCancel() : onConfirm(false))}
          >
            {cancelLabel}
          </Button>
          <Button
            type="button"
            variant="destructive"
            disabled={pending}
            onClick={() => onConfirm(true)}
          >
            {pending && <Loader2 className="size-4 animate-spin" />}
            {employeeId ? <ConfirmLabelWithPendingWork employeeId={employeeId} label={confirmLabel} /> : confirmLabel}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}

/**
 * Nhãn nút đỏ: còn việc duyệt treo thì thêm «Vẫn … (còn việc treo)». Tách thành component để
 * hook chỉ chạy khi có `employeeId` (hộp dùng không kèm hồ sơ không cần QueryClient).
 */
function ConfirmLabelWithPendingWork({ employeeId, label }: { employeeId: number; label: string }) {
  const { data } = useEmployeePendingWork(employeeId)
  const hasPendingWork = (data?.total_tasks ?? 0) + (data?.total_flow_steps ?? 0) > 0
  return <>{hasPendingWork ? `Vẫn ${label.toLowerCase()} (còn việc treo)` : label}</>
}
