import { CrudDetailPage } from '@/shared/crud'
import { WAREHOUSE_CRUD_CONFIG } from '../config/warehouse-crud'

export function WarehouseDetailPage() {
  return <CrudDetailPage config={WAREHOUSE_CRUD_CONFIG} />
}
