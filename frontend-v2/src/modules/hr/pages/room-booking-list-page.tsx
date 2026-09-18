import { useNavigate } from 'react-router-dom'
import { Plus } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { UnifiedRoomBookingTable } from '../components/unified-room-booking-table'

/**
 * PHIẾU ĐẶT PHÒNG — bảng thống nhất cùng khuôn với màn Đơn nghỉ phép (CR-260).
 *
 * «Cần tôi duyệt · Phiếu của tôi · Tôi đã duyệt» không còn là 3 tab riêng mà
 * là 4 tuỳ chọn trong dropdown «Phạm vi» của thanh công cụ.  Phần điều hướng
 * giữa Lịch · Phiếu · Danh mục đã chuyển sang submenu sidebar, nên `RoomSectionTabs`
 * cũng không cần hiển thị nữa.
 */
export function RoomBookingListPage() {
  const navigate = useNavigate()
  const { can } = usePermission()

  return (
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Phiếu đặt phòng họp"
        description={
          <span className="max-md:hidden">
            Đặt phòng, theo dõi phiếu và duyệt phiếu của người khác.
          </span>
        }
        actions={
          can('room_booking', 'create') ? (
            <Button
              className="w-full md:w-auto"
              onClick={() => navigate(appRoutes.hr.roomBookingNew)}
            >
              <Plus className="size-4" />
              Đặt phòng
            </Button>
          ) : undefined
        }
      />

      <Card className="flex min-h-0 w-full min-w-0 flex-1 flex-col p-3 md:p-4">
        <UnifiedRoomBookingTable />
      </Card>
    </PageContainer>
  )
}
