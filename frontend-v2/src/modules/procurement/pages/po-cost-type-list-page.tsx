/** bao-CR-453 — danh sách Loại chi phí thu mua. */
import { CrudListPage } from '@/shared/crud'

import { PO_COST_TYPE_CRUD_CONFIG } from '../config/po-cost-type-crud'

export function PoCostTypeListPage() {
  return <CrudListPage config={PO_COST_TYPE_CRUD_CONFIG} />
}
