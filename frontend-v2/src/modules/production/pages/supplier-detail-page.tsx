import { CrudDetailPage } from '@/shared/crud'
import { SUPPLIER_CRUD_CONFIG } from '../config/supplier-crud'

export function SupplierDetailPage() {
  return <CrudDetailPage config={SUPPLIER_CRUD_CONFIG} />
}
