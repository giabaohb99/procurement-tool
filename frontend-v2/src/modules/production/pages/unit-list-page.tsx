import { CrudListPage } from '@/shared/crud'
import { UNIT_CRUD_CONFIG } from '../config/unit-crud'

export function UnitListPage() {
  return <CrudListPage config={UNIT_CRUD_CONFIG} />
}
