import { CrudDetailPage } from '@/shared/crud'
import { VEHICLE_CRUD_CONFIG } from '../config/vehicle-crud'

export function VehicleCatalogDetailPage() {
  return <CrudDetailPage config={VEHICLE_CRUD_CONFIG} />
}
