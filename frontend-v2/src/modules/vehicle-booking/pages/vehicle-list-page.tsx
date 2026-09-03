import { CrudListPage } from '@/shared/crud'
import { VEHICLE_CRUD_CONFIG } from '../config/vehicle-crud'

export function VehicleListPage() {
  return <CrudListPage config={VEHICLE_CRUD_CONFIG} />
}
