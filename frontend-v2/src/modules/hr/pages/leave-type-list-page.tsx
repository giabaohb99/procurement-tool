import { CrudListPage } from '@/shared/crud'
import { LEAVE_TYPE_CRUD_CONFIG } from '../config/leave-type-crud'
import { LeaveSectionTabs } from '../components/leave-section-tabs'
import { LEAVE_SETTINGS_TOOLBAR_STICKY } from '../utils/leave-list-sticky'

export function LeaveTypeListPage() {
  return (
    //  Khổ hẹp: dải điều hướng HAI HÀNG (chuyển màn + tab con) ghim đỉnh, thanh
    //  công cụ ghim ngay dưới nó — xem `LEAVE_SETTINGS_TOOLBAR_STICKY`, mốc
    //  `top` bằng đúng chiều cao hai hàng đó.
    <CrudListPage
      config={LEAVE_TYPE_CRUD_CONFIG}
      beforeContent={<LeaveSectionTabs sticky />}
      toolbarClassName={LEAVE_SETTINGS_TOOLBAR_STICKY}
    />
  )
}
