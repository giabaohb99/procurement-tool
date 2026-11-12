import { CrudListPage } from '@/shared/crud'
import { HrSetupTabs } from '../components/hr-setup-tabs'
import { LEAVE_BLOCK_CRUD_CONFIG } from '../config/leave-block-crud'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

export function LeaveBlockListPage() {
  return (
    <CrudListPage
      config={LEAVE_BLOCK_CRUD_CONFIG}
      topContent={<HrSetupTabs />}
      compactHeader
      toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
    />
  )
}
