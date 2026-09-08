import { CrudListPage } from '@/shared/crud'
import { SEAL_TYPE_CRUD_CONFIG } from '../config/seal-type-crud'

export function SealTypeListPage() {
  return <CrudListPage config={SEAL_TYPE_CRUD_CONFIG} />
}
