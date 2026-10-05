import { CrudDetailPage } from '@/shared/crud'
import { WORK_SCHEDULE_CRUD_CONFIG } from '../config/work-schedule-crud'

/** Dùng chung cho `/new` và `/:id` — `CrudDetailPage` tự nhận ra chế độ thêm mới. */
export function WorkScheduleDetailPage() {
  return <CrudDetailPage config={WORK_SCHEDULE_CRUD_CONFIG} />
}
