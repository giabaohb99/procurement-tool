// bao-CR-470 (HQ6 P-01) — danh sách danh mục hóa chất theo văn bản.
import { CrudListPage } from '@/shared/crud'

import { CUSTOMS_REGULATION_CRUD_CONFIG } from '../config/customs-regulation-crud'

export function CustomsRegulationListPage() {
  return <CrudListPage config={CUSTOMS_REGULATION_CRUD_CONFIG} />
}
