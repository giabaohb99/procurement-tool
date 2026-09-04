import { CrudListPage } from '@/shared/crud'
import { HOLIDAY_CRUD_CONFIG } from '../config/holiday-crud'
import { LeaveSectionTabs } from '../components/leave-section-tabs'

export function HolidayListPage() {
  return <CrudListPage config={HOLIDAY_CRUD_CONFIG} beforeContent={<LeaveSectionTabs />} />
}
