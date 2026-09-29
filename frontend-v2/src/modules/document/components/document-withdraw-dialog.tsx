import { useRef, useState } from 'react'

import { useApprovalAction } from '@/modules/approval/hooks/use-approvals'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { Textarea } from '@/shared/ui/textarea'

interface DocumentWithdrawDialogProps {
  /** Phiên duyệt đang chạy của văn bản. */
  instanceId: number
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * NGƯỜI TRÌNH TỰ RÚT văn bản đang chờ duyệt về để sửa — văn bản quay về *Nháp*.
 *
 * Backend có sẵn từ lâu (`approval.action_service.withdraw` + hook
 * `document.withdraw_document`) nhưng màn hình chưa từng có nút: người soạn muốn
 * sửa một chữ phải đi nhờ người duyệt bấm «Trả lại», và dấu vết thì ghi như thể
 * văn bản bị đánh giá là chưa đạt (29/09/2026).
 *
 * Luật do BACKEND giữ, hộp thoại chỉ nói trước cho khỏi bấm rồi nhận lỗi:
 * - chỉ người trình mới rút được;
 * - chỉ khi CHƯA ai duyệt — đã có người ký thì chữ ký đó không được thành vô
 *   nghĩa, phải nhờ Trả lại hoặc Từ chối;
 * - bắt buộc ghi lý do (hiện trong dấu vết duyệt).
 */
export function DocumentWithdrawDialog({ instanceId, open, onOpenChange }: DocumentWithdrawDialogProps) {
  const [reason, setReason] = useState('')
  const action = useApprovalAction(instanceId, 'document')
  //  `disabled={isPending}` chỉ đúng ở lần render sau — bấm đúp nhanh vẫn ra hai
  //  request. Khóa bằng ref đổi ngay trong tick (luật bẫy biểu mẫu, CLAUDE.md).
  const sending = useRef(false)

  function handleOpenChange(next: boolean) {
    if (!next) setReason('')
    onOpenChange(next)
  }

  function handleSubmit() {
    const text = reason.trim()
    if (!text || sending.current) return
    sending.current = true
    action.mutate(
      { kind: 'withdraw', text },
      {
        onSuccess: () => handleOpenChange(false),
        onSettled: () => {
          sending.current = false
        },
      },
    )
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Rút văn bản về để sửa</DialogTitle>
          <DialogDescription>
            Văn bản quay về <b>Nháp</b>, người duyệt không còn thấy việc duyệt nữa. Sửa xong bạn gửi
            duyệt lại từ đầu. Chỉ rút được khi chưa ai duyệt.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="withdraw-reason">Lý do rút</Label>
          <Textarea
            id="withdraw-reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            placeholder="Ví dụ: cần sửa lại ngày hiệu lực"
            rows={3}
            maxLength={500}
          />
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
            Đóng
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={!reason.trim() || action.isPending}
          >
            Rút về
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
