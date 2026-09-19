import { Printer } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { DocumentComments } from '@/modules/procurement/components/document-comments'
import { AuditTimeline } from '@/shared/audit/audit-timeline'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { BookingApprovalPanel } from '../components/booking-approval-panel'
import { BookingDetailBody } from '../components/booking-detail-body'
import { BookingDetailHeader } from '../components/booking-detail-header'
import { BookingForm } from '../components/booking-form'
import { BookingProgressCard } from '../components/booking-progress-card'
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

  const canEdit = Boolean(data) && can('vehicle_booking', 'write') && EDITABLE.has(data!.status)

  //  Phiếu SỬA ĐƯỢC (Nháp / Yêu cầu chỉnh sửa) mở THẲNG vào biểu mẫu chỉnh sửa —
  //  không có chế độ xem trung gian, KHÔNG có nút "Sửa". Hủy hoặc Lưu/Gửi duyệt xong
  //  (onDone) về danh sách; muốn xem lại thì mở lại phiếu (khi đó có thể đã hết sửa được).
  if (data && canEdit) {
    return (
      <PageContainer className="w-full">
        {/*  Bố cục KHỚP trang xem: một HÀNG NÚT + tiêu đề + badge trạng thái trên cùng,
            liền dưới là 2 khung (biểu mẫu nội dung | Trao đổi + Lịch sử). BookingForm tự
            dựng header full-width rồi xếp body + `aside` theo lưới. onSaved trống → LƯU /
            GỬI DUYỆT xong Ở LẠI trang (dữ liệu tự nạp lại; hết sửa được thì tự sang trang xem). */}
        <BookingForm
          booking={data}
          title={data.purpose || `Yêu cầu đặt xe ${data.code}`}
          badge={<BookingStatusBadge status={data.status} driverStatus={data.driver_status} />}
          onDone={() => navigate(appRoutes.vehicleBooking.requests)}
          onSaved={() => undefined}
          aside={
            <>
              <DocumentComments entity="vehicle_booking" entityId={data.id} />
              <AuditTimeline entity="vehicle_booking" entityId={data.id} messageOnly dense />
            </>
          }
        />
      </PageContainer>
    )
  }

  return (
    <PageContainer className="w-full">
      {/*  Tiêu đề chỉ dựng khi ĐÃ CÓ dữ liệu: nó sống bằng mã phiếu + tóm tắt chuyến,
          dựng sớm thì ra một khối khung rỗng rồi nhảy nội dung vào. Lúc đang tải /
          lỗi thì hai câu bên dưới nói thay. */}
      {data && (
        <BookingDetailHeader
          booking={data}
          onBack={() => navigate(appRoutes.vehicleBooking.requests)}
          actions={
            <>
              <BookingWorkflowActions booking={data} layout="menu" onDispatch={() => setDispatchOpen(true)} />
              {/*  Không có nút "Sửa": phiếu sửa được đã mở thẳng vào biểu mẫu ở trên.
                  `outline` cho KHỚP nút `⋯` ngay bên trái — hai nút này cùng cấp
                  (đều là việc phụ), để một cái có viền một cái không thì dải nút
                  đọc ra ba kiểu khác nhau. Thứ bậc đã nằm ở chỗ khác: chỉ nút
                  quyết định (Duyệt · Chấp nhận) được tô đặc. */}
              <Button variant="outline" onClick={() => navigate(appRoutes.vehicleBooking.print(data.id))}>
                <Printer className="size-4" />
                In phiếu
              </Button>
            </>
          }
        />
      )}
      {isLoading && <p className="text-sm text-muted-foreground">Đang tải…</p>}
      {isError && (
        <p className="text-sm text-destructive">
          Không tải được yêu cầu. Kiểm tra kết nối hoặc quyền truy cập.
        </p>
      )}

      {data && (
        //  Màn rộng: nội dung phiếu + lịch sử bên trái, tiến trình · luồng duyệt ·
        //  trao đổi dồn cột phải (những thứ cần thấy trong lúc đọc phiếu).
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="flex min-w-0 flex-col gap-5">
            <BookingDetailBody booking={data} />
            {/*  Lịch sử thao tác khép lại CỘT CHÍNH, dưới Ghi chú: nó là thứ đọc
                sau cùng (tra lại phiếu đã đi qua tay ai), dài ra theo thời gian,
                và ở cột phụ có vùng cuộn riêng thì nó đẩy Trao đổi lên trên rồi
                tự cuộn trong một khung cao 300px — đúng kiểu dữ liệu không nên
                nhốt. `AuditTimeline` tự dựng thẻ có tiêu đề (không bọc thêm Card
                kẻo lặp tiêu đề); `messageOnly` vì backend đã ghi câu tự mô tả
                ("Đã điều phối Xe…", "Yêu cầu chỉnh sửa — Lý do: …"). */}
            <AuditTimeline entity="vehicle_booking" entityId={data.id} messageOnly dense />
          </div>
          {/*  Cột phụ DÍNH dưới tiêu đề khi cuộn. Thân phiếu dài gấp mấy lần cột này,
              nên cuộn xuống giữa phiếu là khung Trao đổi trôi mất — muốn ghi một câu
              về chỗ vừa đọc thì phải cuộn ngược lên.

              Ba mảnh phải khớp nhau:
              · `self-start` — ô lưới mặc định kéo cao bằng cả hàng, mà `sticky` chỉ
                có tác dụng khi phần tử THẤP HƠN vùng cuộn của nó.
              · `top-[var(--booking-header-h)]` — tiêu đề tự đo rồi ghi biến này ra
                thẻ cha; thiếu nó thì cột phụ trượt lên và chui xuống dưới tiêu đề.
              · `max-h` + `overflow-y-auto` — Trao đổi dài ra theo số bình luận; không
                chặn thì phần đuôi bị ghim ra ngoài màn và KHÔNG cuộn tới được.
                `3.5rem` là thanh trên của khung (nằm ngoài vùng cuộn). */}
          <div className="flex flex-col gap-5 lg:sticky lg:top-[calc(var(--booking-header-h,0px)+0.75rem)] lg:max-h-[calc(100dvh-3.5rem-var(--booking-header-h,0px)-2rem)] lg:self-start lg:overflow-y-auto">
            {/*  Tiến trình xử lý đứng ĐẦU cột phụ: bốn khung ở cột này đều trả lời
                "phiếu đang ở đâu, ai đã nói gì" — đọc từ trạng thái hiện thời
                (Tiến trình) xuống việc phải làm (Luồng duyệt) rồi tới trao đổi và
                dấu vết. Để nó ở cột chính thì nó cắt đôi mạch *chuyến đi này là gì*
                (lộ trình → hàng hóa → người yêu cầu), và cuộn xuống là mất. */}
            <BookingProgressCard booking={data} />
            {/* Luồng duyệt nhiều bước — hiện khi phiếu ĐÃ TỪNG vào bộ máy, kể cả
                phiên đã duyệt xong: thẻ này còn mang Lịch sử phê duyệt. Gác bằng
                `approval_running` là sai — luồng "Duyệt tự động bởi HOD" chỉ 1 bước
                nên đóng ngay, dấu vết không bao giờ kịp hiện (19/09/2026). */}
            {data.approval_instance_id != null && <BookingApprovalPanel bookingId={data.id} />}
            {/*  Trao đổi trên phiếu — dùng chung widget bình luận (entity/entityId). */}
            <DocumentComments entity="vehicle_booking" entityId={data.id} />
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
