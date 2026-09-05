import { ArrowLeft } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { useCrudDetail } from '@/shared/crud'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { BookingPageHeader } from '../components/booking-page-header'
import { VehicleForm } from '../components/vehicle-form'
import type { Vehicle } from '../types/vehicle'

/**
 * Trang Thêm mới (`/vehicles/new`) và Chỉnh sửa (`/vehicles/:id`) danh mục Xe.
 * Một component, phân nhánh theo có `:id` hay không.
 */
export function VehicleCatalogFormPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = Boolean(id)
  const backToList = () => navigate(appRoutes.vehicleBooking.vehicles)

  const { data, isLoading, isError } = useCrudDetail<Vehicle>('/api/vehicles', id)
  const title = isEdit ? 'Chỉnh sửa thông tin xe' : 'Thêm xe'

  return (
    <PageContainer className="w-full">
      {!isEdit ? (
        <VehicleForm title={title} onDone={backToList} />
      ) : isLoading ? (
        <>
          <BookingPageHeader title={title} onBack={backToList} />
          <Skeleton className="h-80 w-full" />
        </>
      ) : isError || !data ? (
        <>
          <BookingPageHeader title={title} onBack={backToList} />
          <ErrorState title="Không tìm thấy xe" description="Xe có thể đã bị xóa hoặc bạn không có quyền xem.">
            <Button variant="outline" onClick={backToList}>
              <ArrowLeft className="size-4" />
              Về danh sách
            </Button>
          </ErrorState>
        </>
      ) : (
        <VehicleForm item={data} title={title} onDone={backToList} />
      )}
    </PageContainer>
  )
}
