import { CrudListPage } from '@/shared/crud'
import { WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG } from '../config/work-schedule-assignment-crud'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

export function WorkScheduleAssignmentListPage() {
  return (
    <CrudListPage
      config={WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG}
      toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
    />
  )
}
