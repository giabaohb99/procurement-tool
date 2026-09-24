/** bao-CR-453 — chi tiết Loại chi phí thu mua. */
import { CrudDetailPage } from '@/shared/crud'

import { PO_COST_TYPE_CRUD_CONFIG } from '../config/po-cost-type-crud'

export function PoCostTypeDetailPage() {
  return <CrudDetailPage config={PO_COST_TYPE_CRUD_CONFIG} />
}
