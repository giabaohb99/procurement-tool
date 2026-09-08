import { CrudDetailPage } from '@/shared/crud'
import { JOB_POSITION_CRUD_CONFIG } from '../config/job-position-crud'

/** Chi tiết một chức vụ — cùng khung khai báo với danh sách. */
export function JobPositionDetailPage() {
  return <CrudDetailPage config={JOB_POSITION_CRUD_CONFIG} />
}
