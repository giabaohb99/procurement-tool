import { CrudListPage } from '@/shared/crud'
import { SUPPLIER_CRUD_CONFIG } from '../config/supplier-crud'

export function SupplierListPage() {
  return <CrudListPage config={SUPPLIER_CRUD_CONFIG} />
}
