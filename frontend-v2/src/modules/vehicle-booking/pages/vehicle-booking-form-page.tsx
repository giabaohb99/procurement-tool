import { ArrowLeft } from 'lucide-react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { BookingForm } from '../components/booking-form'
import { BookingPageHeader } from '../components/booking-page-header'
import { useVehicleBooking } from '../hooks/use-vehicle-bookings'

/**
 * Trang Thêm mới (`/vehicle-booking/new`, kèm `?from=<id>` khi nhân bản) và Chỉnh sửa
 * (`/vehicle-booking/:id/edit`) yêu cầu đặt xe.
 */
export function VehicleBookingFormPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const isEdit = Boolean(id)
  const fromId = Number(searchParams.get('from')) || null

  const backToList = () => navigate(appRoutes.vehicleBooking.root)
  //  SỬA thì back/hủy quay lại CHI TIẾT phiếu (`/:id`), không về danh sách.
  const backToDetail = () => navigate(appRoutes.vehicleBooking.detail(Number(id)))

  // Sửa: nạp phiếu theo :id. Nhân bản: nạp phiếu nguồn theo ?from=.
  const loadId = isEdit ? Number(id) : fromId
  const { data, isLoading, isError } = useVehicleBooking(loadId)

  const needsLoad = isEdit || fromId !== null
  const title = isEdit
    ? 'Chỉnh sửa yêu cầu đặt xe'
    : fromId
      ? 'Nhân bản yêu cầu đặt xe'
      : 'Tạo yêu cầu đặt xe'

  return (
    <PageContainer className="w-full">
      {!needsLoad ? (
        <BookingForm title={title} onDone={backToList} />
      ) : isLoading ? (
        <>
          <BookingPageHeader title={title} onBack={backToList} />
          <Skeleton className="h-96 w-full" />
        </>
      ) : isError || !data ? (
        <>
          <BookingPageHeader title={title} onBack={backToList} />
          <ErrorState title="Không tìm thấy yêu cầu đặt xe" description="Phiếu có thể đã bị xóa hoặc bạn không có quyền xem.">
            <Button variant="outline" onClick={backToList}>
              <ArrowLeft className="size-4" />
              Về danh sách
            </Button>
          </ErrorState>
        </>
      ) : isEdit ? (
        <BookingForm booking={data} title={title} onDone={backToDetail} />
      ) : (
        <BookingForm duplicateFrom={data} title={title} onDone={backToList} />
      )}
    </PageContainer>
  )
}
