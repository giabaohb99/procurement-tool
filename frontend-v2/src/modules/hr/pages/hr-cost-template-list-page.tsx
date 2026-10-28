import { CrudListPage } from '@/shared/crud'
import { HR_COST_TEMPLATE_CRUD_CONFIG } from '../config/hr-cost-template-crud'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

/** Màn MẪU KHOẢN CHI PHÍ `/hr/hr-cost-templates` (duoc-CR-690). */
export function HrCostTemplateListPage() {
  return <CrudListPage config={HR_COST_TEMPLATE_CRUD_CONFIG} toolbarClassName={LIST_TOOLBAR_STICKY_TOP} />
}
