import { CrudListPage } from '@/shared/crud'
import { LEAVE_TYPE_CRUD_CONFIG } from '../config/leave-type-crud'
import { LeaveSectionTabs } from '../components/leave-section-tabs'
import { LIST_SECTION_TOOLBAR_STICKY } from '../utils/list-sticky'

export function LeaveTypeListPage() {
  return (
    <CrudListPage
      config={LEAVE_TYPE_CRUD_CONFIG}
      beforeContent={<LeaveSectionTabs sticky />}
      toolbarClassName={LIST_SECTION_TOOLBAR_STICKY}
    />
  )
}
