import { CrudListPage } from '@/shared/crud'
import { WORK_SCHEDULE_CRUD_CONFIG } from '../config/work-schedule-crud'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

export function WorkScheduleListPage() {
  return <CrudListPage config={WORK_SCHEDULE_CRUD_CONFIG} toolbarClassName={LIST_TOOLBAR_STICKY_TOP} />
}
