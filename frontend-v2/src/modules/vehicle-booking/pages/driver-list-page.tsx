import { CrudListPage } from '@/shared/crud'
import { DRIVER_CRUD_CONFIG } from '../config/driver-crud'

export function DriverListPage() {
  return <CrudListPage config={DRIVER_CRUD_CONFIG} />
}
