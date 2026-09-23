import { Ban, Check, Stamp, Undo2 } from 'lucide-react'
import { useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import {
  useApproveSealRequest,
  useCompleteSealRequest,
  useRejectClerkSealRequest,
  useRejectSealRequest,
  useReturnClerkSealRequest,
  useReturnSealRequest,
} from '../hooks/use-seal-requests'
import { SEAL_OUTLINE_BTN } from '../utils/action-button-class'
import { SEAL_STATUS, type SealRequest } from '../types/seal-request'
import { SealApproveDialog } from './seal-approve-dialog'
import { SealReasonDialog } from './seal-reason-dialog'

/** Loại dialog lý do đang mở (mỗi loại một hành động khác nhau). */
type ReasonKind = 'return' | 'reject' | 'returnClerk' | 'rejectClerk' | null

/**
 * Cụm nút chuyển trạng thái phiếu đóng dấu, bày THEO VAI TRÒ + trạng thái:
 *
 * - TBP (quyền `approve`), phiếu Chờ duyệt → Duyệt · Yêu cầu chỉnh sửa · Từ chối.
 * - Văn thư (quyền `write`), phiếu Đã duyệt → Hoàn thành đóng dấu · Yêu cầu chỉnh
 *   sửa · Từ chối.
 *
 * Phiếu đang chạy luồng duyệt NHIỀU BƯỚC (`request.approval_running`) thì cụm cổng-1
 * (TBP) phải ẩn — duyệt qua bảng luồng ở màn chi tiết / "Việc của tôi". Cổng-2 (Văn
 * thư) không bị ảnh hưởng. Backend mới là chốt chặn thật (`require` + đúng trạng thái);
 * ở đây chỉ ẩn/hiện.
 */
export function SealWorkflowActions({ request }: { request: SealRequest }) {
  const { can } = usePermission()
  const canApprove = can('seal_request', 'approve')

  const [reasonKind, setReasonKind] = useState<ReasonKind>(null)
  const [approveOpen, setApproveOpen] = useState(false)

  const approve = useApproveSealRequest()
  const returnEdit = useReturnSealRequest()
  const reject = useRejectSealRequest()
  const complete = useCompleteSealRequest()
  const returnClerk = useReturnClerkSealRequest()
  const rejectClerk = useRejectClerkSealRequest()

  const id = request.id
  //  Tiêu đề hộp thoại lấy MỤC ĐÍCH (lùi về mã phiếu nếu trống) thay cho mã.
  const subject = request.purpose || request.code
  const busy =
    approve.isPending ||
    returnEdit.isPending ||
    reject.isPending ||
    complete.isPending ||
    returnClerk.isPending ||
    rejectClerk.isPending

  const isPending = request.status === SEAL_STATUS.pending
  const isApproved = request.status === SEAL_STATUS.approved
  //  Đang chạy bộ máy duyệt nhiều bước thì ẩn cổng-1 (TBP); cổng-2 (Văn thư) giữ nguyên.
  const showApprove = canApprove && isPending && !request.approval_running
  //  CỔNG-2 chỉ hiện với VĂN THƯ được phân công (backend trả `can_stamp`) — không
  //  theo `write` chung, vì mọi nhân sự đều có write phạm vi own.
  const showClerk = Boolean(request.can_stamp) && isApproved

  return (
    <>
      {/* Trưởng bộ phận — phiếu Chờ duyệt */}
      {showApprove && (
        <>
          {/*  Duyệt phải qua hộp thoại xác nhận: bắt buộc tick "đã xem & hiểu" mới duyệt được. */}
          <Button onClick={() => setApproveOpen(true)} disabled={busy}>
            <Check className="size-4" />
            Duyệt
          </Button>
          <Button
            variant="outline"
            className={SEAL_OUTLINE_BTN}
            onClick={() => setReasonKind('return')}
            disabled={busy}
          >
            <Undo2 className="size-4" />
            Yêu cầu chỉnh sửa
          </Button>
          {/*  ⚠️ Từ chối là nút VIỀN chữ đỏ, KHÔNG phải nút đỏ đặc (đổi
              22/09/2026). Đỏ đặc là mảng màu nặng nhất dải nút, đặt cạnh nút
              Duyệt thì mắt rơi vào Từ chối trước — trong khi duyệt mới là lối
              đi thường ngày. Đỏ ở đây để CẢNH BÁO, không phải để mời bấm; câu
              xác nhận trong hộp thoại mới là chốt chặn thật. */}
          <Button
            variant="outline"
            onClick={() => setReasonKind('reject')}
            disabled={busy}
            className={cn(
              SEAL_OUTLINE_BTN,
              'text-destructive hover:bg-destructive/10 hover:text-destructive',
            )}
          >
            <Ban className="size-4" />
            Từ chối
          </Button>
        </>
      )}

      {/* Văn thư — phiếu Đã duyệt (chờ đóng dấu) */}
      {showClerk && (
        <>
          {/*  Hoàn thành đóng dấu chạy THẲNG khi bấm — không popup, không cần ghi chú. */}
          <Button onClick={() => complete.mutate({ id, note: '' })} disabled={busy}>
            <Stamp className="size-4" />
            Hoàn thành đóng dấu
          </Button>
          <Button
            variant="outline"
            className={SEAL_OUTLINE_BTN}
            onClick={() => setReasonKind('returnClerk')}
            disabled={busy}
          >
            <Undo2 className="size-4" />
            Yêu cầu chỉnh sửa
          </Button>
          {/* Cùng luật với cổng-1: viền chữ đỏ, không đỏ đặc. */}
          <Button
            variant="outline"
            onClick={() => setReasonKind('rejectClerk')}
            disabled={busy}
            className={cn(
              SEAL_OUTLINE_BTN,
              'text-destructive hover:bg-destructive/10 hover:text-destructive',
            )}
          >
            <Ban className="size-4" />
            Từ chối
          </Button>
        </>
      )}

      {/* --- Dialog lý do (dùng chung 4 hành động lùi/chặn) --- */}
      {reasonKind === 'return' && (
        <SealReasonDialog
          title="Yêu cầu chỉnh sửa"
          subject={subject}
          code={request.code}
          description="Trả phiếu về người tạo để sửa rồi gửi lại."
          label="Lý do cần chỉnh sửa"
          placeholder="Thiếu chứng từ đã ký, sai loại con dấu…"
          confirmLabel="Trả lại chỉnh sửa"
          pending={returnEdit.isPending}
          onConfirm={(reason) => returnEdit.mutate({ id, reason }, { onSuccess: () => setReasonKind(null) })}
          onClose={() => setReasonKind(null)}
        />
      )}
      {reasonKind === 'reject' && (
        <SealReasonDialog
          title="Từ chối yêu cầu đóng dấu"
          subject={subject}
          code={request.code}
          description="Phiếu bị khóa, không đi tiếp luồng."
          label="Lý do từ chối"
          placeholder="Không thuộc thẩm quyền đóng dấu…"
          confirmLabel="Từ chối yêu cầu"
          destructive
          pending={reject.isPending}
          onConfirm={(reason) => reject.mutate({ id, reason }, { onSuccess: () => setReasonKind(null) })}
          onClose={() => setReasonKind(null)}
        />
      )}
      {reasonKind === 'returnClerk' && (
        <SealReasonDialog
          title="Yêu cầu chỉnh sửa"
          subject={subject}
          code={request.code}
          description="Trả phiếu về người tạo để sửa rồi gửi lại."
          label="Lý do cần chỉnh sửa"
          placeholder="Chứng từ chưa đủ chữ ký, sai công ty…"
          confirmLabel="Trả lại chỉnh sửa"
          pending={returnClerk.isPending}
          onConfirm={(reason) => returnClerk.mutate({ id, reason }, { onSuccess: () => setReasonKind(null) })}
          onClose={() => setReasonKind(null)}
        />
      )}
      {reasonKind === 'rejectClerk' && (
        <SealReasonDialog
          title="Từ chối yêu cầu đóng dấu"
          subject={subject}
          code={request.code}
          description="Phiếu bị khóa, không đi tiếp luồng."
          label="Lý do từ chối"
          placeholder="Chứng từ không hợp lệ…"
          confirmLabel="Từ chối yêu cầu"
          destructive
          pending={rejectClerk.isPending}
          onConfirm={(reason) => rejectClerk.mutate({ id, reason }, { onSuccess: () => setReasonKind(null) })}
          onClose={() => setReasonKind(null)}
        />
      )}

      {approveOpen && (
        <SealApproveDialog
          subject={subject}
          pending={approve.isPending}
          onConfirm={() => approve.mutate({ id }, { onSuccess: () => setApproveOpen(false) })}
          onClose={() => setApproveOpen(false)}
        />
      )}
    </>
  )
}
