import { CrudListPage } from '@/shared/crud'
import { HOLIDAY_CRUD_CONFIG } from '../config/holiday-crud'

export function HolidayListPage() {
  return <CrudListPage config={HOLIDAY_CRUD_CONFIG} />
}
