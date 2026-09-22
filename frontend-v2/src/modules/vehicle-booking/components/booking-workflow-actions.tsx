import { Ban, Check, CircleCheck, Flag, MoreHorizontal, PlayCircle, Route, Undo2 } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import {
  useApproveBooking,
  useDispatchRejectBooking,
  useDispatchReturnBooking,
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
  /**
   * `driver` = CHỈ dựng nhóm nút của tài xế (chấp nhận · bắt đầu · hoàn thành ·
   * từ chối chuyến), bỏ nhóm duyệt và nhóm điều phối.
   *
   * Dùng ở màn «Chuyến của tôi»: màn đó nói rõ "nhận, bắt đầu và hoàn tất tại
   * đây", nhưng ai có quyền `approve` (điều phối viên, admin) mở ra lại thấy
   * thêm _Điều phối lại_ · _Yêu cầu chỉnh sửa_ · _Từ chối yêu cầu_ — ba việc
   * của NGƯỜI KHÁC, và chúng đứng TRƯỚC nút mà họ thật sự cần bấm.
   */
  scope?: 'all' | 'driver'
  /**
   * `inline` = bày hết ra thành nút. `menu` = giữ ĐÚNG MỘT nút chính, phần còn
   * lại gom vào nút `⋯`.
   *
   * Dùng `menu` ở tiêu đề trang chi tiết: ở đó một người vừa có quyền điều phối
   * vừa thao tác thay tài xế nhìn thấy SÁU nút cùng cỡ, hai trong số đó cùng tô
   * đặc — không có nút nào là "nút cần bấm", và dải nút ăn hết bề ngang khiến
   * phần tóm tắt phiếu bị ép xuống ba dòng.
   */
  layout?: 'inline' | 'menu'
  /**
   * Cỡ nút. `sm` dành cho chỗ HẸP — cụ thể là thẻ ở màn «Chuyến của tôi»: ở lưới
   * ba cột, phần bấm được của thẻ chỉ rộng 285px, mà hai nút cỡ thường
   * («Chấp nhận» + «Từ chối chuyến») cần 286px nên nút thứ hai bị cắt cụt đuôi
   * ngay trong viền thẻ (thấy ngày 22/09/2026).
   */
  size?: 'default' | 'sm'
}

/** Một hành động trong cụm — dựng thành danh sách rồi mới render, để phân thứ bậc. */
interface WorkflowAction {
  key: string
  label: string
  icon: LucideIcon
  run: () => void
  /**
   * `forward` = bước TIẾN TỚI của phiếu (duyệt · điều phối · nhận · bắt đầu ·
   * hoàn thành). Chỉ hành động `forward` ĐẦU TIÊN được tô đặc; phần còn lại —
   * kể cả _Điều phối lại_, vốn là đường vòng — để nhạt.
   */
  kind?: 'forward' | 'danger'
}

/**
 * Phiếu đang chạy luồng duyệt NHIỀU BƯỚC thì 3 nút duyệt một bước phải ẩn — duyệt
 * ở màn "Việc của tôi". Đọc từ `booking.approval_running` (backend set ở API chi tiết);
 * backend cũng chặn thật bằng `block_legacy_path`, đây chỉ là ẩn cho gọn.
 */

/** Loại dialog lý do đang mở (mỗi loại một hành động khác nhau). */
type ReasonKind =
  | 'return'
  | 'reject'
  | 'driverReject'
  | 'dispatchReturn'
  | 'dispatchReject'
  | null

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
export function BookingWorkflowActions({
  booking,
  onDispatch,
  scope = 'all',
  layout = 'inline',
  size = 'default',
}: BookingWorkflowActionsProps) {
  const { can } = usePermission()
  const driverOnly = scope === 'driver'
  const canApprove = can('vehicle_booking', 'approve') && !driverOnly
  const canWrite = can('vehicle_booking', 'write')
  //  Điều phối viên = có quyền `approve` (tài xế chỉ có `write` phạm vi `assigned`).
  //  Các nút ĐIỀU PHỐI (Điều phối / Điều phối lại / trả / từ chối yêu cầu) chỉ cho
  //  điều phối viên — nếu gác bằng `write` thì tài xế cũng thấy (họ có write assigned).
  const canDispatch = canApprove

  const [reasonKind, setReasonKind] = useState<ReasonKind>(null)
  const [completeOpen, setCompleteOpen] = useState(false)

  const approve = useApproveBooking()
  const returnEdit = useReturnBooking()
  const reject = useRejectBooking()
  const dispatchReturn = useDispatchReturnBooking()
  const dispatchReject = useDispatchRejectBooking()
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
    dispatchReturn.isPending ||
    dispatchReject.isPending ||
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

  //  --- Danh sách hành động, XẾP THEO THỨ TỰ ƯU TIÊN ---
  //  Thứ tự ở đây quyết định nút nào được tô đặc: `forward` đầu tiên thắng. Nên
  //  nhóm của tài xế đứng TRƯỚC _Điều phối lại_ — cùng lúc phiếu "đã điều phối,
  //  chờ tài xế" thì việc cần làm là tài xế bấm nhận, còn phân lại xe là ngoại lệ.
  const actions: WorkflowAction[] = []

  if (showApprove) {
    actions.push({ key: 'approve', label: 'Duyệt', icon: Check, kind: 'forward',
                   run: () => approve.mutate({ id }) })
  }
  if (canDispatch && isApproved) {
    actions.push({ key: 'dispatch', label: 'Điều phối', icon: Route, kind: 'forward',
                   run: onDispatch })
  }
  if (driverStage && (dstatus === DRIVER_STATUS.waiting || dstatus === DRIVER_STATUS.rejected)) {
    actions.push({ key: 'accept', label: 'Chấp nhận', icon: CircleCheck, kind: 'forward',
                   run: () => driverAccept.mutate({ id }) })
  }
  if (driverStage && dstatus === DRIVER_STATUS.accepted) {
    actions.push({ key: 'start', label: 'Bắt đầu', icon: PlayCircle, kind: 'forward',
                   run: () => driverStart.mutate({ id }) })
  }
  if (driverStage && dstatus === DRIVER_STATUS.ongoing) {
    actions.push({ key: 'complete', label: 'Hoàn thành', icon: Flag, kind: 'forward',
                   run: () => setCompleteOpen(true) })
  }
  //  Đã điều phối (tài xế chưa nhận) hoặc tài xế từ chối → điều phối viên đổi xe/tài xế khác.
  const dispatchAgain =
    isDispatched && (dstatus === DRIVER_STATUS.waiting || dstatus === DRIVER_STATUS.rejected)
  if (canDispatch && dispatchAgain) {
    actions.push({ key: 'redispatch', label: 'Điều phối lại', icon: Route, run: onDispatch })
  }
  //  Người duyệt: trả về người tạo sửa, hoặc từ chối hẳn.
  if (showApprove) {
    actions.push({ key: 'return', label: 'Yêu cầu chỉnh sửa', icon: Undo2,
                   run: () => setReasonKind('return') })
    actions.push({ key: 'reject', label: 'Từ chối', icon: Ban, kind: 'danger',
                   run: () => setReasonKind('reject') })
  }
  //  Điều phối viên: ở khâu ĐÃ DUYỆT (chưa điều phối) hoặc khi tài xế chưa nhận.
  if (canDispatch && (isApproved || dispatchAgain)) {
    actions.push({ key: 'dispatchReturn', label: 'Yêu cầu chỉnh sửa', icon: Undo2,
                   run: () => setReasonKind('dispatchReturn') })
    actions.push({ key: 'dispatchReject', label: 'Từ chối yêu cầu', icon: Ban, kind: 'danger',
                   run: () => setReasonKind('dispatchReject') })
  }
  if (driverStage && (dstatus === DRIVER_STATUS.waiting || dstatus === DRIVER_STATUS.accepted)) {
    actions.push({ key: 'driverReject', label: 'Từ chối chuyến', icon: Ban, kind: 'danger',
                   run: () => setReasonKind('driverReject') })
  }

  //  Nút chính = hành động TIẾN TỚI đầu tiên. Không có cái nào (vd chỉ còn mấy
  //  việc chặn/lùi) thì không tô đặc nút nào cả — đừng ép một nút "Từ chối" thành
  //  nút nổi bật nhất trang.
  const primary = actions.find((a) => a.kind === 'forward')
  const rest = actions.filter((a) => a !== primary)

  return (
    <>
      {primary && (
        <Button size={size} onClick={primary.run} disabled={busy}>
          <primary.icon className="size-4" />
          {primary.label}
        </Button>
      )}

      {layout === 'menu'
        ? rest.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                variant="outline"
                size={size === 'sm' ? 'icon-sm' : 'icon'}
                disabled={busy}
                aria-label="Thao tác khác"
              >
                  <MoreHorizontal className="size-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                {rest.map((a) => (
                  <DropdownMenuItem
                    key={a.key}
                    variant={a.kind === 'danger' ? 'destructive' : 'default'}
                    onSelect={a.run}
                  >
                    <a.icon className="size-4" />
                    {a.label}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )
        : rest.map((a) => (
            <Button
              key={a.key}
              variant="outline"
              size={size}
              //  Hành động chặn/lùi để CHỮ đỏ trên nền trắng, không tô nền đỏ đặc:
              //  nền đặc hút mắt mạnh hơn cả nút chính, nên dải nút đọc ra là
              //  "Từ chối" trước rồi mới tới việc cần làm.
              className={a.kind === 'danger' ? 'text-destructive hover:text-destructive' : undefined}
              onClick={a.run}
              disabled={busy}
            >
              <a.icon className="size-4" />
              {a.label}
            </Button>
          ))}

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
      {reasonKind === 'dispatchReturn' && (
        <BookingReasonDialog
          title={`Yêu cầu chỉnh sửa "${subject}"`}
          description="Trả phiếu về người tạo để sửa rồi gửi lại (gỡ điều phối đã phân)."
          label="Lý do cần chỉnh sửa"
          placeholder="Sai lộ trình, cần đổi thời gian…"
          confirmLabel="Trả lại chỉnh sửa"
          pending={dispatchReturn.isPending}
          onConfirm={(reason) =>
            dispatchReturn.mutate({ id, reason }, { onSuccess: () => setReasonKind(null) })
          }
          onClose={() => setReasonKind(null)}
        />
      )}
      {reasonKind === 'dispatchReject' && (
        <BookingReasonDialog
          title={`Từ chối yêu cầu "${subject}"`}
          description="Từ chối yêu cầu ở khâu điều phối — phiếu bị khóa, không đi tiếp."
          label="Lý do từ chối"
          placeholder="Không bố trí được xe, yêu cầu không hợp lệ…"
          confirmLabel="Từ chối yêu cầu"
          destructive
          pending={dispatchReject.isPending}
          onConfirm={(reason) =>
            dispatchReject.mutate({ id, reason }, { onSuccess: () => setReasonKind(null) })
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
