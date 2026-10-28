import { CrudListPage } from '@/shared/crud'
import { HR_COST_GROUP_CRUD_CONFIG } from '../config/hr-cost-group-crud'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

/** Màn NHÓM CHI PHÍ `/hr/hr-cost-groups` (duoc-CR-690). */
export function HrCostGroupListPage() {
  return <CrudListPage config={HR_COST_GROUP_CRUD_CONFIG} toolbarClassName={LIST_TOOLBAR_STICKY_TOP} />
}
