import { CrudListPage } from '@/shared/crud'
import { WAREHOUSE_CRUD_CONFIG } from '../config/warehouse-crud'

export function WarehouseListPage() {
  return <CrudListPage config={WAREHOUSE_CRUD_CONFIG} />
}
