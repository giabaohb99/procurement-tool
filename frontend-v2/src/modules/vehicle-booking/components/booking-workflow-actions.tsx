import { Ban, Check, CircleCheck, Flag, PlayCircle, Route, Undo2 } from 'lucide-react'
import { useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import {
  useApproveBooking,
  useDriverAcceptBooking,
  useDriverCompleteBooking,
  useDriverRejectBooking,
  useDriverStartBooking,
  useRejectBooking,
  useReturnBooking,
} from '../hooks/use-vehicle-bookings'
import { BOOKING_STATUS, DRIVER_STATUS, type VehicleBooking } from '../types/vehicle-booking'
import { BookingCompleteDialog } from './booking-complete-dialog'
import { BookingReasonDialog } from './booking-reason-dialog'

interface BookingWorkflowActionsProps {
  booking: VehicleBooking
  /** Mở popup điều phối (page quản lý popup này). */
  onDispatch: () => void
}

/**
 * Phiếu đang chạy luồng duyệt NHIỀU BƯỚC thì 3 nút duyệt một bước phải ẩn — duyệt
 * ở màn "Việc của tôi". Đọc từ `booking.approval_running` (backend set ở API chi tiết);
 * backend cũng chặn thật bằng `block_legacy_path`, đây chỉ là ẩn cho gọn.
 */

/** Loại dialog lý do đang mở (mỗi loại một hành động khác nhau). */
type ReasonKind = 'return' | 'reject' | 'driverReject' | null

/**
 * Cụm nút chuyển trạng thái phiếu đặt xe, bày THEO VAI TRÒ + trạng thái hiện tại:
 *
 * - Người duyệt (quyền `approve`), phiếu Chờ duyệt → Duyệt · Yêu cầu chỉnh sửa · Từ chối.
 * - Điều phối (quyền `write`), phiếu Đã duyệt → Điều phối; tài xế từ chối → Điều phối lại.
 * - Tài xế ĐƯỢC PHÂN (hoặc người có quyền `write` thao tác thay), phiếu Điều phối →
 *   Chấp nhận / Từ chối chuyến / Bắt đầu / Hoàn tất theo bước của tài xế.
 *
 * Backend mới là chốt chặn thật (`require` + đúng tài xế được phân); ở đây chỉ ẩn/hiện.
 */
export function BookingWorkflowActions({ booking, onDispatch }: BookingWorkflowActionsProps) {
  const { can } = usePermission()
  const canApprove = can('vehicle_booking', 'approve')
  const canWrite = can('vehicle_booking', 'write')

  const [reasonKind, setReasonKind] = useState<ReasonKind>(null)
  const [completeOpen, setCompleteOpen] = useState(false)

  const approve = useApproveBooking()
  const returnEdit = useReturnBooking()
  const reject = useRejectBooking()
  const driverAccept = useDriverAcceptBooking()
  const driverReject = useDriverRejectBooking()
  const driverStart = useDriverStartBooking()
  const driverComplete = useDriverCompleteBooking()

  const id = booking.id
  //  Tiêu đề hộp thoại lấy MỤC ĐÍCH chuyến (lùi về mã phiếu nếu trống) thay cho mã.
  const subject = booking.purpose || booking.code
  const busy =
    approve.isPending ||
    returnEdit.isPending ||
    reject.isPending ||
    driverAccept.isPending ||
    driverReject.isPending ||
    driverStart.isPending ||
    driverComplete.isPending

  // --- Ai thấy nhóm nào ---
  const isPending = booking.status === BOOKING_STATUS.pending
  const isApproved = booking.status === BOOKING_STATUS.approved
  const isDispatched = booking.status === BOOKING_STATUS.dispatched
  const showApprove = canApprove && isPending && !booking.approval_running
  // Tài xế được phân, hoặc người có quyền write thao tác thay khi cần.
  const driverStage = isDispatched && (booking.is_assigned_driver || canWrite)
  const dstatus = booking.driver_status

  return (
    <>
      {/* Điều phối (quyền write) */}
      {canWrite && isApproved && (
        <Button onClick={onDispatch} disabled={busy}>
          <Route className="size-4" />
          Điều phối
        </Button>
      )}
      {canWrite && isDispatched && dstatus === DRIVER_STATUS.rejected && (
        <Button onClick={onDispatch} disabled={busy}>
          <Route className="size-4" />
          Điều phối lại
        </Button>
      )}

      {/* Người duyệt */}
      {showApprove && (
        <>
          <Button onClick={() => approve.mutate({ id })} disabled={busy}>
            <Check className="size-4" />
            Duyệt
          </Button>
          <Button variant="outline" onClick={() => setReasonKind('return')} disabled={busy}>
            <Undo2 className="size-4" />
            Yêu cầu chỉnh sửa
          </Button>
          <Button variant="destructive" onClick={() => setReasonKind('reject')} disabled={busy}>
            <Ban className="size-4" />
            Từ chối
          </Button>
        </>
      )}

      {/* Tài xế được phân */}
      {driverStage && (dstatus === DRIVER_STATUS.waiting || dstatus === DRIVER_STATUS.rejected) && (
        <Button onClick={() => driverAccept.mutate({ id })} disabled={busy}>
          <CircleCheck className="size-4" />
          Chấp nhận
        </Button>
      )}
      {driverStage && dstatus === DRIVER_STATUS.accepted && (
        <Button onClick={() => driverStart.mutate({ id })} disabled={busy}>
          <PlayCircle className="size-4" />
          Bắt đầu
        </Button>
      )}
      {driverStage && dstatus === DRIVER_STATUS.ongoing && (
        <Button onClick={() => setCompleteOpen(true)} disabled={busy}>
          <Flag className="size-4" />
          Hoàn tất
        </Button>
      )}
      {driverStage &&
        (dstatus === DRIVER_STATUS.waiting || dstatus === DRIVER_STATUS.accepted) && (
          <Button variant="outline" onClick={() => setReasonKind('driverReject')} disabled={busy}>
            <Ban className="size-4" />
            Từ chối chuyến
          </Button>
        )}

      {/* --- Dialog lý do (dùng chung 3 hành động lùi/chặn) --- */}
      {reasonKind === 'return' && (
        <BookingReasonDialog
          title={`Yêu cầu chỉnh sửa "${subject}"`}
          description="Trả phiếu về người tạo để sửa rồi gửi lại."
          label="Lý do cần chỉnh sửa"
          placeholder="Thiếu thời gian về, sai điểm đến…"
          confirmLabel="Trả lại chỉnh sửa"
          pending={returnEdit.isPending}
          onConfirm={(reason) =>
            returnEdit.mutate({ id, reason }, { onSuccess: () => setReasonKind(null) })
          }
          onClose={() => setReasonKind(null)}
        />
      )}
      {reasonKind === 'reject' && (
        <BookingReasonDialog
          title={`Từ chối yêu cầu "${subject}"`}
          description="Từ chối yêu cầu — phiếu bị khóa, không đi tiếp luồng."
          label="Lý do từ chối"
          placeholder="Không thuộc mục đích công tác…"
          confirmLabel="Từ chối yêu cầu"
          destructive
          pending={reject.isPending}
          onConfirm={(reason) => reject.mutate({ id, reason }, { onSuccess: () => setReasonKind(null) })}
          onClose={() => setReasonKind(null)}
        />
      )}
      {reasonKind === 'driverReject' && (
        <BookingReasonDialog
          title={`Từ chối yêu cầu "${subject}"`}
          description="Trả chuyến về điều phối để phân lại xe/tài xế."
          label="Lý do từ chối chuyến"
          placeholder="Trùng lịch, xe hỏng…"
          confirmLabel="Từ chối chuyến"
          destructive
          pending={driverReject.isPending}
          onConfirm={(reason) =>
            driverReject.mutate({ id, reason }, { onSuccess: () => setReasonKind(null) })
          }
          onClose={() => setReasonKind(null)}
        />
      )}

      {completeOpen && (
        <BookingCompleteDialog
          code={booking.code}
          pending={driverComplete.isPending}
          onConfirm={(payload) =>
            driverComplete.mutate({ id, ...payload }, { onSuccess: () => setCompleteOpen(false) })
          }
          onClose={() => setCompleteOpen(false)}
        />
      )}
    </>
  )
}
