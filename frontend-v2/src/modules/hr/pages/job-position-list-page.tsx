import { CrudListPage } from '@/shared/crud'
import { HrSetupTabs } from '../components/hr-setup-tabs'
import { JOB_POSITION_CRUD_CONFIG } from '../config/job-position-crud'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

export function JobPositionListPage() {
  return (
    //  Khổ hẹp: danh sách đổi thành thẻ nên trang dài ra (13 chức vụ ≈ 1600px)
    //  và CẢ TRANG cuộn — không ghim thì ô tìm + nút Bộ lọc trôi mất ngay nhịp
    //  vuốt đầu, muốn lọc lại phải vuốt ngược lên đỉnh. duoc-CR-773: màn nằm trong
    //  dải tab Thiết lập, cùng khuôn với Danh mục phòng họp.
    <CrudListPage
      config={JOB_POSITION_CRUD_CONFIG}
      topContent={<HrSetupTabs />}
      compactHeader
      toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
    />
  )
}
