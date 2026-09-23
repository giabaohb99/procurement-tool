// bao-CR-470 (HQ6 P-01) — chi tiết một hóa chất trong danh mục theo văn bản.
import { CrudDetailPage } from '@/shared/crud'

import { CUSTOMS_REGULATION_CRUD_CONFIG } from '../config/customs-regulation-crud'

export function CustomsRegulationDetailPage() {
  return <CrudDetailPage config={CUSTOMS_REGULATION_CRUD_CONFIG} />
}
