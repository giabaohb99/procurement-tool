import { ArrowLeft, Pencil, Printer } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { AuditTimeline } from '@/shared/audit/audit-timeline'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { BookingApprovalPanel } from '../components/booking-approval-panel'
import { BookingDetailBody } from '../components/booking-detail-body'
import { BookingForm } from '../components/booking-form'
import { BookingDispatchDialog } from '../components/booking-dispatch-dialog'
import { BookingStatusBadge } from '../components/status-pill'
import { BookingWorkflowActions } from '../components/booking-workflow-actions'
import { useVehicleBooking } from '../hooks/use-vehicle-bookings'
import { BOOKING_STATUS } from '../types/vehicle-booking'

/** Chỉ sửa được khi phiếu còn nháp hoặc bị trả về (khớp EDITABLE_STATUSES ở backend). */
const EDITABLE = new Set<number>([BOOKING_STATUS.draft, BOOKING_STATUS.returned])

/**
 * Trang CHI TIẾT phiếu đặt xe (`/vehicle-booking/:id`) — xem + thao tác (điều phối /
 * duyệt…). Sửa mở TRANG riêng `/:id/edit` (không popup); điều phối vẫn là popup vì
 * là thao tác nhanh trên nền chi tiết.
 */
export function VehicleBookingDetailPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const { id } = useParams()
  const bookingId = Number(id)
  const { data, isLoading, isError } = useVehicleBooking(Number.isFinite(bookingId) ? bookingId : null)
  const [dispatchOpen, setDispatchOpen] = useState(false)
  //  Sửa NGAY trên trang này (không điều hướng sang trang riêng) — "1 bước".
  const [editing, setEditing] = useState(false)

  const canEdit = Boolean(data) && can('vehicle_booking', 'write') && EDITABLE.has(data!.status)

  //  Đang sửa: hiện biểu mẫu chỉnh sửa ngay trên trang chi tiết. Lưu/Hủy/back → quay
  //  lại chế độ xem. Lưu xong trạng thái đổi (vd Chờ duyệt) thì tự về chế độ xem.
  if (data && editing && canEdit) {
    return (
      <PageContainer className="w-full">
        <BookingForm
          booking={data}
          title="Chỉnh sửa yêu cầu đặt xe"
          onDone={() => setEditing(false)}
        />
      </PageContainer>
    )
  }

  return (
    <PageContainer className="w-full">
      {/* Tiêu đề: nút back bên trái · tên phiếu · badge trạng thái · cụm thao tác dồn phải. */}
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <Button
          variant="outline"
          size="icon"
          aria-label="Về danh sách yêu cầu đặt xe"
          onClick={() => navigate(appRoutes.vehicleBooking.root)}
        >
          <ArrowLeft className="size-4" />
        </Button>
        <h1 className="text-xl font-semibold tracking-tight text-navy dark:text-foreground">
          {data ? data.purpose || `Yêu cầu đặt xe ${data.code}` : 'Chi tiết yêu cầu đặt xe'}
        </h1>
        {data && <BookingStatusBadge status={data.status} />}
        <div className="min-w-4 flex-1" />
        <div className="flex flex-wrap items-center justify-end gap-2">
          {data && <BookingWorkflowActions booking={data} onDispatch={() => setDispatchOpen(true)} />}
          {canEdit && data && (
            <Button variant="outline" onClick={() => setEditing(true)}>
              <Pencil className="size-4" />
              Sửa
            </Button>
          )}
          {data && (
            <Button variant="outline" onClick={() => navigate(appRoutes.vehicleBooking.print(data.id))}>
              <Printer className="size-4" />
              In phiếu
            </Button>
          )}
        </div>
      </div>
      {isLoading && <p className="text-sm text-muted-foreground">Đang tải…</p>}
      {isError && (
        <p className="text-sm text-destructive">
          Không tải được yêu cầu. Kiểm tra kết nối hoặc quyền truy cập.
        </p>
      )}

      {data && (
        //  Màn rộng: nội dung chính bên trái, luồng duyệt + lịch sử dồn cột phải.
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
          <div className="flex min-w-0 flex-col gap-5">
            <BookingDetailBody booking={data} />
          </div>
          <div className="flex flex-col gap-5">
            {/* Luồng duyệt nhiều bước — chỉ hiện khi phiếu đang chạy trong bộ máy
                (bật ApprovalSwitch); 3 nút duyệt một bước ở đầu trang đã tự ẩn. */}
            {data.approval_running && <BookingApprovalPanel bookingId={data.id} />}
            <Card className="flex flex-col gap-3 p-5">
              <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Lịch sử thao tác
              </h3>
              <AuditTimeline entity="vehicle_booking" entityId={data.id} />
            </Card>
          </div>
        </div>
      )}

      {dispatchOpen && data && (
        <BookingDispatchDialog
          booking={data}
          onClose={() => setDispatchOpen(false)}
          onDispatched={() => setDispatchOpen(false)}
        />
      )}
    </PageContainer>
  )
}
