import { useState } from 'react'
import { useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { ArrowLeft, Ban, Check, Save, Send, Trash2, X } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Card, CardContent } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'
import { formatDateTime } from '@/shared/utils/format-date'
import { RoomBookingForm } from '../components/room-booking-form'
import { RoomBookingSidePanel } from '../components/room-booking-side-panel'
import { RoomBookingStatusPanel } from '../components/room-booking-status-panel'
import { RoomBookingSummary } from '../components/room-booking-summary'
import { RoomDecisionActions } from '../components/room-decision-actions'
import { RoomStatusBadge } from '../components/room-status-badge'
import {
  useDeleteRoomBooking,
  useRoomBooking,
  useRoomBookingAction,
  useSaveRoomBooking,
  type RoomBookingAction,
} from '../hooks/use-room'
import { EDITABLE_ROOM_STATUSES, ROOM_BOOKING_STATUS, type RoomBooking } from '../types/room'
import {
  emptyRoomForm,
  formValuesOf,
  missingBeforeSubmit,
  toRoomPayload,
  type RoomBookingFormValues,
} from '../utils/room-form-values'
import { toLocalInput } from '../utils/room-time'

/**
 * CHI TIẾT / ĐẶT MỚI phiếu phòng họp — một trang cho cả hai, phân biệt bằng `:id`.
 *
 * Phiếu còn sửa được (Nháp hoặc Trả về) thì dựng form; đã gửi duyệt thì dựng
 * bản chỉ-xem. **Không** dựng form với cờ `disabled` — xem docstring của
 * `RoomBookingSummary`.
 */
/** Câu dưới tiêu đề: nói việc phải làm TIẾP THEO, theo đúng trạng thái phiếu. */
function describeStatus(booking?: RoomBooking): string {
  if (!booking) return 'Chọn phòng và khung giờ, lưu nháp rồi gửi duyệt.'
  switch (booking.status) {
    case ROOM_BOOKING_STATUS.PENDING:
      return booking.submitted_at
        ? `Đã gửi duyệt lúc ${formatDateTime(booking.submitted_at)} — phòng đang được giữ, chờ người duyệt.`
        : 'Đang chờ duyệt — phòng đã được giữ.'
    case ROOM_BOOKING_STATUS.APPROVED:
      return 'Đã duyệt — phòng thuộc về phiếu này trong khung giờ đã đặt.'
    case ROOM_BOOKING_STATUS.REJECTED:
      return 'Bị từ chối — phòng đã nhả ra. Cần họp thì lập phiếu khác.'
    case ROOM_BOOKING_STATUS.RETURNED:
      return 'Bị trả về — sửa lại theo ý kiến bên phải rồi gửi duyệt lần nữa.'
    case ROOM_BOOKING_STATUS.CANCELLED:
      return 'Đã hủy — phòng đã nhả ra cho người khác đặt.'
    default:
      return 'Bản nháp — lưu rồi gửi duyệt khi đã chọn xong phòng và giờ.'
  }
}

export function RoomBookingDetailPage() {
  const { id } = useParams<{ id: string }>()
  const bookingId = Number(id) || 0
  const navigate = useNavigate()
  const location = useLocation()
  const { can } = usePermission()

  //  Nút «Về danh sách» LÙI THEO LỊCH SỬ: đường cứng làm mất bộ lọc người dùng
  //  vừa đặt ở màn danh sách (bài học 04/09/2026 của Nghỉ phép). `location.key
  //  === 'default'` = vào thẳng từ link trong thư mời, lùi lúc đó là đẩy họ ra
  //  khỏi ứng dụng.
  const goBack = () => {
    if (location.key === 'default') navigate(appRoutes.hr.roomBookings)
    else navigate(-1)
  }

  const { data: booking, isLoading } = useRoomBooking(bookingId)
  const save = useSaveRoomBooking()
  const remove = useDeleteRoomBooking()
  const act = useRoomBookingAction()

  //  Mở từ ô trống trên LỊCH: `?room_id=&start=` mang sẵn phòng và giờ vừa bấm.
  //  Người dùng vừa nhìn thấy chỗ trống, bắt họ gõ lại đúng con số đó là thao
  //  tác thừa. Chỉ đọc MỘT LẦN lúc dựng state — đọc mỗi lần render thì người
  //  dùng sửa giờ xong bị kéo về giá trị trên URL.
  const [searchParams] = useSearchParams()
  const [form, setForm] = useState<RoomBookingFormValues>(() => {
    const base = emptyRoomForm()
    const roomId = Number(searchParams.get('room_id')) || 0
    const start = searchParams.get('start') || ''
    if (!roomId && !start) return base
    const startAt = start || base.startAt
    const end = new Date(`${startAt}:00`)
    end.setHours(end.getHours() + 1)
    return {
      ...base,
      roomId: roomId || base.roomId,
      startAt,
      endAt: start ? toLocalInput(end) : base.endAt,
    }
  })
  const [reasonFor, setReasonFor] = useState<'reject' | 'cancel' | null>(null)

  //  ⚠️ MỘT chốt cho CẢ TRANG, không phải mỗi nút một chốt.
  //
  //  `disabled={isPending}` không đỡ được: đó là state của React, chỉ bật ở lần
  //  render kế, nên năm cú bấm trong cùng một nhịp đều lọt — đo được ngày
  //  04/09/2026, bấm «Lưu nháp» 5 lần ra **5 lệnh POST**, tức 5 phiếu trùng.
  //
  //  Dùng chung một chốt cho mọi thao tác ghi của trang cũng là có chủ ý: hai
  //  thao tác khác nhau trên CÙNG một phiếu (vừa Lưu vừa Gửi duyệt) chạy song
  //  song thì lệnh sau đọc phải trạng thái nửa vời của lệnh trước.
  const once = useSingleFlight()

  //  Nạp giá trị khi chuyển sang MỘT PHIẾU KHÁC — theo `id`, không theo tham
  //  chiếu của `booking`. Theo tham chiếu thì mọi lượt nạp lại cache sẽ xóa thứ
  //  người dùng vừa gõ. Đặt trong lúc render, không trong `useEffect`: effect
  //  chạy sau khi commit nên người dùng thấy một khung hình với form RỖNG.
  if (useHasChanged(booking?.id ?? 0) && booking) {
    setForm(formValuesOf(booking))
  }

  const isNew = bookingId === 0
  const editable = isNew || (booking ? EDITABLE_ROOM_STATUSES.includes(booking.status) : false)
  const canWrite = can('room_booking', isNew ? 'create' : 'write')
  const missingFields = missingBeforeSubmit(form)

  const submitSave = () =>
    void once(async () => {
      const saved = await save.mutateAsync({
        id: isNew ? undefined : bookingId,
        values: toRoomPayload(form),
      })
      if (isNew) navigate(appRoutes.hr.roomBookingDetail(saved.id), { replace: true })
    })

  /** Bốn thao tác trên tờ phiếu, đi chung một chốt với nút Lưu. */
  const runAction = (action: RoomBookingAction, reason = '', onDone?: () => void) =>
    void once(async () => {
      await act.mutateAsync({ id: bookingId, action, reason })
      onDone?.()
    })

  if (!isNew && isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Đang tải phiếu…</p>
      </PageContainer>
    )
  }

  if (!isNew && !booking) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">
          Không tìm thấy phiếu đặt phòng này, hoặc nó nằm ngoài phạm vi dữ liệu của bạn.
        </p>
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <PageHeader
        sticky
        leading={
          <Button
            variant="outline"
            size="icon"
            title="Về danh sách"
            aria-label="Về danh sách"
            onClick={goBack}
          >
            <ArrowLeft className="size-4" />
          </Button>
        }
        title={isNew ? 'Đặt phòng họp' : `Phiếu ${booking?.code}`}
        //  Câu mô tả nói đúng việc phải làm TIẾP THEO ở trạng thái hiện tại.
        //  Bản đầu luôn ghi "Lưu nháp rồi gửi duyệt…" kể cả với phiếu đã chờ
        //  duyệt — đọc ra như thể người dùng chưa làm gì (khách chê 04/09/2026).
        description={describeStatus(booking)}
        actions={
          <>
            {booking && <RoomStatusBadge status={booking.status} label={booking.status_label} />}

            {editable && canWrite && (
              <>
                {!isNew && can('room_booking', 'delete') && (
                  <Button
                    variant="outline"
                    onClick={() =>
                      void once(async () => {
                        await remove.mutateAsync(bookingId)
                        navigate(appRoutes.hr.roomBookings)
                      })
                    }
                    disabled={remove.isPending}
                  >
                    <Trash2 className="size-4" />
                    Xóa phiếu
                  </Button>
                )}
                <Button onClick={submitSave} disabled={save.isPending}>
                  <Save className="size-4" />
                  Lưu nháp
                </Button>
                {/*  Gửi duyệt chỉ hiện khi phiếu ĐÃ có id: trình một phiếu chưa
                     lưu thì không có gì để trình. `title` nói ra thiếu gì —
                     nút mờ mà im lặng là kiểu chặn khó chịu nhất. */}
                {!isNew && (
                  <Button
                    onClick={() => runAction('submit')}
                    disabled={act.isPending || Boolean(missingFields)}
                    title={missingFields || undefined}
                  >
                    <Send className="size-4" />
                    Gửi duyệt
                  </Button>
                )}
              </>
            )}

            {/*  Phiếu ĐANG CHẠY TRONG LUỒNG: ba nút quyết định của bộ máy, chỉ
                 hiện cho người đang thật sự phải ký. */}
            {booking && booking.approval_instance_id > 0 && (
              <RoomDecisionActions bookingId={bookingId} />
            )}

            {/*  Duyệt / từ chối THẲNG — chỉ khi môi trường CHƯA khai luồng.
                 ⚠️ Điều kiện `approval_instance_id === 0` không được bỏ: thiếu
                 nó thì phiếu đang trong luồng vẫn hiện hai nút này, bấm vào chỉ
                 ăn câu "phiếu đang chạy trong luồng" — đúng luật nhưng vô nghĩa
                 với người vừa bấm, và nó lại nằm cạnh ba nút duyệt THẬT. */}
            {booking?.status === ROOM_BOOKING_STATUS.PENDING &&
              booking.approval_instance_id === 0 &&
              can('room_booking', 'approve') && (
                <>
                  <Button
                    variant="outline"
                    onClick={() => setReasonFor('reject')}
                    disabled={act.isPending}
                  >
                    <X className="size-4" />
                    Từ chối
                  </Button>
                  <Button
                    onClick={() => runAction('approve')}
                    disabled={act.isPending}
                  >
                    <Check className="size-4" />
                    Duyệt phiếu
                  </Button>
                </>
              )}

            {booking &&
              (booking.status === ROOM_BOOKING_STATUS.PENDING ||
                booking.status === ROOM_BOOKING_STATUS.APPROVED) &&
              can('room_booking', 'cancel') && (
                <Button
                  variant="outline"
                  onClick={() => setReasonFor('cancel')}
                  disabled={act.isPending}
                >
                  <Ban className="size-4" />
                  Hủy phiếu
                </Button>
              )}
          </>
        }
      />

      {/*  HAI CỘT trên màn rộng: trái để NHẬP, phải để QUYẾT ĐỊNH (phòng nào
           trống · họp bao lâu · có quá sức chứa không). Một cột chạy suốt bề
           ngang thì trên màn 2200px mỗi ô nhập dài hơn hai gang tay và nửa dưới
           trang trắng trơn — khách báo 04/09/2026.

           `max-w-[1600px]`: màn siêu rộng thì form không kéo dài vô tận nữa.
           Dấu vết nằm NGOÀI lưới hai cột, chạy hết bề ngang: nó là dòng thời
           gian, đọc theo chiều ngang mới thoải mái. */}
      <div className="mx-auto w-full max-w-[1600px] space-y-4">
        <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[minmax(0,1fr)_340px]">
          <div className="space-y-4">
            {editable && canWrite ? (
              <RoomBookingForm
                value={form}
                onChange={setForm}
                lockedRoom={Boolean(searchParams.get('room_id'))}
              />
            ) : (
              booking && (
                <Card>
                  <CardContent className="py-6">
                    <RoomBookingSummary booking={booking} />
                  </CardContent>
                </Card>
              )
            )}

          </div>

          {/*  Cột phải đổi vai theo chế độ: đang SỬA thì soi lại thứ vừa nhập,
               còn CHỈ XEM thì «phiếu này đang ở đâu» — trạng thái, mốc thời
               gian, ý kiến người duyệt. Bỏ trống nửa phải là phí đúng chỗ mắt
               người đọc tìm tới. */}
          {editable && canWrite ? (
            <RoomBookingSidePanel value={form} />
          ) : (
            booking && <RoomBookingStatusPanel booking={booking} />
          )}
        </div>

        {booking && <AuditTimeline entity="room_booking" entityId={booking.id} showMessage />}
      </div>

      <ReasonConfirmDialog
        open={reasonFor !== null}
        onOpenChange={(open) => !open && setReasonFor(null)}
        title={reasonFor === 'cancel' ? 'Hủy phiếu đặt phòng' : 'Từ chối phiếu'}
        description={
          reasonFor === 'cancel'
            ? 'Phòng được nhả ra ngay để người khác đặt được. Lý do hiện trên dấu vết của phiếu.'
            : 'Người đặt sẽ đọc đúng câu này để biết vì sao.'
        }
        placeholder={reasonFor === 'cancel' ? 'Vì sao không họp nữa?' : 'Vì sao không duyệt?'}
        confirmText={reasonFor === 'cancel' ? 'Hủy phiếu' : 'Từ chối'}
        destructive
        pending={act.isPending}
        onConfirm={(reason) => {
          if (!reasonFor) return
          //  Đóng hộp trong `onDone`, không đóng ngay lúc bấm: gọi hỏng mà hộp
          //  đã đóng thì người dùng tưởng mình đã xong.
          runAction(reasonFor, reason, () => setReasonFor(null))
        }}
      />
    </PageContainer>
  )
}
