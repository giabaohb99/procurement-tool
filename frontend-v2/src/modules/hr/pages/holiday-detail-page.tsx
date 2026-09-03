import { CrudDetailPage } from '@/shared/crud'
import { HOLIDAY_CRUD_CONFIG } from '../config/holiday-crud'

export function HolidayDetailPage() {
  return <CrudDetailPage config={HOLIDAY_CRUD_CONFIG} />
}
