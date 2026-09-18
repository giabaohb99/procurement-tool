import { CrudListPage } from '@/shared/crud'
import { HOLIDAY_CRUD_CONFIG } from '../config/holiday-crud'
import { LeaveSectionTabs } from '../components/leave-section-tabs'
import { LIST_SECTION_TOOLBAR_STICKY } from '../utils/list-sticky'

export function HolidayListPage() {
  return (
    <CrudListPage
      config={HOLIDAY_CRUD_CONFIG}
      beforeContent={<LeaveSectionTabs sticky />}
      toolbarClassName={LIST_SECTION_TOOLBAR_STICKY}
    />
  )
}
