import { CrudListPage } from '@/shared/crud'
import { JOB_POSITION_CRUD_CONFIG } from '../config/job-position-crud'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

export function JobPositionListPage() {
  return (
    //  Khổ hẹp: danh sách đổi thành thẻ nên trang dài ra (13 chức vụ ≈ 1600px)
    //  và CẢ TRANG cuộn — không ghim thì ô tìm + nút Bộ lọc trôi mất ngay nhịp
    //  vuốt đầu, muốn lọc lại phải vuốt ngược lên đỉnh. Màn này không có dải
    //  tab nào phía trên nên dùng mốc `top-0`.
    <CrudListPage
      config={JOB_POSITION_CRUD_CONFIG}
      toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
    />
  )
}
