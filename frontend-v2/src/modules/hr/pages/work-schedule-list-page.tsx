import { CrudListPage } from '@/shared/crud'
import { HrSetupTabs } from '../components/hr-setup-tabs'
import { WORK_SCHEDULE_CRUD_CONFIG } from '../config/work-schedule-crud'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

export function WorkScheduleListPage() {
  return (
    <CrudListPage
      config={WORK_SCHEDULE_CRUD_CONFIG}
      topContent={<HrSetupTabs />}
      compactHeader
      toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
    />
  )
}
