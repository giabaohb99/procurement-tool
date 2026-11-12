import { CrudListPage } from '@/shared/crud'
import { HrSetupTabs } from '../components/hr-setup-tabs'
import { HOLIDAY_CRUD_CONFIG } from '../config/holiday-crud'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

export function HolidayListPage() {
  return (
    <CrudListPage
      config={HOLIDAY_CRUD_CONFIG}
      topContent={<HrSetupTabs />}
      compactHeader
      toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
    />
  )
}
