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
import { BookingNoteCard } from '../components/booking-note-card'
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
        //  Màn rộng: nội dung phiếu + Trao đổi bên trái, tiến trình · luồng duyệt ·
        //  lịch sử dồn cột phải.
        //
        //  ⚠️ **Cột phải KHÔNG có vùng cuộn riêng** (đại ca chốt 21/09/2026): cả cột
        //  cuộn theo trang, không `sticky`, không `max-h`, không `overflow-y-auto`.
        //  Bản trước ghim cột phải dưới tiêu đề rồi cho nó tự cuộn bên trong, nên
        //  trang có HAI vùng cuộn cạnh nhau: bánh xe chuột đổi nghĩa tùy con trỏ
        //  đang đậu ở nửa nào, và thanh cuộn con trong một cột rộng 360px thì vừa
        //  khó thấy vừa khó bấm. Đừng dựng lại; muốn thấy một khung trong lúc đọc
        //  phiếu thì xếp nó lên ĐẦU cột, đừng ghim cả cột.
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="flex min-w-0 flex-col gap-5">
            <BookingDetailBody booking={data} />
            {/*  Trao đổi khép lại CỘT CHÍNH, dưới nội dung phiếu (21/09/2026 — đổi
                chỗ với Lịch sử thao tác). Nó là thứ NGƯỜI TA GÕ VÀO, nên cần bề
                ngang của cột chính: ô nhập rộng 360px thì câu ba dòng đọc như một
                cột báo, mà bình luận trên phiếu thường là một đoạn trích dẫn giá
                hoặc một dãy mốc giờ. Dùng chung widget bình luận (entity/entityId). */}
            <DocumentComments entity="vehicle_booking" entityId={data.id} />
          </div>
          <div className="flex flex-col gap-5">
            {/*  Tiến trình xử lý đứng ĐẦU cột phụ: ba khung ở cột này đều trả lời
                "phiếu đang ở đâu, đã đi qua tay ai" — đọc từ trạng thái hiện thời
                (Tiến trình) xuống việc phải làm (Luồng duyệt) rồi tới dấu vết. Để
                nó ở cột chính thì nó cắt đôi mạch *chuyến đi này là gì*
                (lộ trình → hàng hóa → người yêu cầu). */}
            <BookingProgressCard booking={data} />
            {/* Luồng duyệt nhiều bước — hiện khi phiếu ĐÃ TỪNG vào bộ máy, kể cả
                phiên đã duyệt xong: thẻ này còn mang Lịch sử phê duyệt. Gác bằng
                `approval_running` là sai — luồng "Duyệt tự động bởi HOD" chỉ 1 bước
                nên đóng ngay, dấu vết không bao giờ kịp hiện (19/09/2026). */}
            {data.approval_instance_id != null && <BookingApprovalPanel bookingId={data.id} />}
            {/*  Ghi chú (21/09/2026 — dời từ cuối thân phiếu sang đây). Đó là lời
                NGƯỜI LẬP dặn thêm, mà người đọc nó là người sắp quyết định
                duyệt / điều phối / nhận chuyến — tức cùng cột với Tiến trình và
                Luồng duyệt. Thẻ TỰ ẨN khi ghi chú rỗng. */}
            <BookingNoteCard booking={data} />
            {/*  Lịch sử thao tác đứng CUỐI cột phụ: chỉ đọc, mỗi dòng một câu ngắn
                nên chịu được cột hẹp, và nó là thứ tra lại chứ không phải thứ gõ
                vào. `AuditTimeline` tự dựng thẻ có tiêu đề (không bọc thêm Card kẻo
                lặp tiêu đề); `messageOnly` vì backend đã ghi câu tự mô tả ("Đã điều
                phối Xe…", "Yêu cầu chỉnh sửa — Lý do: …"). Nó dài ra theo thời gian
                nhưng KHÔNG cần chặn chiều cao ở đây: bản thân nó chỉ hiện một số
                dòng đầu rồi để lại nút «Xem thêm», nên cột phải không phình vô hạn. */}
            <AuditTimeline entity="vehicle_booking" entityId={data.id} messageOnly dense />
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
