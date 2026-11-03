import { CrudListPage } from '@/shared/crud'
import { LEAVE_BLOCK_CRUD_CONFIG } from '../config/leave-block-crud'
import { LeaveSectionTabs } from '../components/leave-section-tabs'
import { LIST_SECTION_TOOLBAR_STICKY } from '../utils/list-sticky'

export function LeaveBlockListPage() {
  return (
    <CrudListPage
      config={LEAVE_BLOCK_CRUD_CONFIG}
      beforeContent={<LeaveSectionTabs sticky />}
      toolbarClassName={LIST_SECTION_TOOLBAR_STICKY}
    />
  )
}
