import { Check, Loader2, X } from 'lucide-react'
import { useRef, useState } from 'react'

import { useApproveChangeRequest, useRejectChangeRequest } from '../hooks/use-employee-change-requests'
import type { EmployeeChangeRequest } from '../types/employee-change-request'
import { describeDecisionError } from '../utils/employee-change-request-review'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'

/** Trần lý do từ chối — khớp `RejectIn.reason` (1..500) của backend. */
const REJECT_REASON_MAX = 500

interface ChangeRequestDecisionActionsProps {
  request: EmployeeChangeRequest
  /** Câu lỗi khi máy chủ từ chối (409 / 403) — trang hiện thành dải báo; `''` = xóa dải. */
  onDecisionError: (message: string) => void
}

/**
 * Hai nút "Từ chối" / "Duyệt" của màn duyệt đề nghị sửa hồ sơ (duoc-CR-676) kèm hộp lý do từ chối.
 * Nơi gọi chỉ dựng khi backend báo `can_decide` và đề nghị còn chờ.
 *
 * ⚠️ Chặn bấm đúp bằng ref (bẫy thứ tư): duyệt hai lần = hai lần ghi hồ sơ + hai dòng nhật ký.
 * Lỗi máy chủ đã được http-client toast; ở đây chỉ chuyển câu đó lên trang để nó ĐỨNG LẠI trên màn
 * (toast tắt sau vài giây, mà 409 "hộ gia đình đã đổi sau lúc gửi" là thứ người duyệt phải đọc kỹ).
 */
export function ChangeRequestDecisionActions({
  request,
  onDecisionError,
}: ChangeRequestDecisionActionsProps) {
  const approve = useApproveChangeRequest(request.employee_id)
  const reject = useRejectChangeRequest(request.employee_id)
  const [rejectOpen, setRejectOpen] = useState(false)
  const busyRef = useRef(false)
  const busy = approve.isPending || reject.isPending

  async function handleApprove() {
    if (busyRef.current) return
    busyRef.current = true
    try {
      const ok = await confirm({
        title: 'Duyệt đề nghị?',
        message: `Các ô ở cột "Đề nghị" sẽ được ghi vào hồ sơ của ${request.employee_name}. Dòng tô màu là ô đã bị sửa sau lúc gửi — duyệt sẽ ghi đè giá trị hiện tại.`,
        confirmLabel: 'Duyệt',
        tone: 'default',
      })
      if (!ok) return
      onDecisionError('')
      await approve.mutateAsync(request.id)
    } catch (error) {
      onDecisionError(describeDecisionError(error))
    } finally {
      busyRef.current = false
    }
  }

  async function handleReject(reason: string) {
    if (busyRef.current) return
    busyRef.current = true
    try {
      onDecisionError('')
      await reject.mutateAsync({ id: request.id, reason: reason.slice(0, REJECT_REASON_MAX) })
      setRejectOpen(false)
    } catch (error) {
      //  Giữ hộp mở để sửa lý do; câu lỗi lên dải báo của trang.
      onDecisionError(describeDecisionError(error))
    } finally {
      busyRef.current = false
    }
  }

  return (
    <div className="flex items-center gap-2">
      <Button type="button" variant="outline" onClick={() => setRejectOpen(true)} disabled={busy}>
        <X />
        Từ chối
      </Button>
      <Button type="button" onClick={() => void handleApprove()} disabled={busy}>
        {approve.isPending ? <Loader2 className="animate-spin" /> : <Check />}
        Duyệt
      </Button>

      <ReasonConfirmDialog
        open={rejectOpen}
        onOpenChange={setRejectOpen}
        title="Từ chối đề nghị sửa hồ sơ"
        description={`Hồ sơ của ${request.employee_name} giữ nguyên. Lý do được gửi lại cho nhân viên đọc.`}
        label="Lý do từ chối"
        placeholder="Ví dụ: số tài khoản không khớp tên chủ tài khoản"
        confirmText="Từ chối"
        destructive
        maxLength={REJECT_REASON_MAX}
        pending={reject.isPending}
        onConfirm={(reason) => void handleReject(reason)}
      />
    </div>
  )
}
