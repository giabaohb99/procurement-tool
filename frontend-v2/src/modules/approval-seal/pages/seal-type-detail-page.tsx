import { CrudDetailPage } from '@/shared/crud'
import { SEAL_TYPE_CRUD_CONFIG } from '../config/seal-type-crud'

export function SealTypeDetailPage() {
  return <CrudDetailPage config={SEAL_TYPE_CRUD_CONFIG} />
}
