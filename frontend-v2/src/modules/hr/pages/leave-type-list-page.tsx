import { CrudListPage } from '@/shared/crud'
import { HrSetupTabs } from '../components/hr-setup-tabs'
import { LEAVE_TYPE_CRUD_CONFIG } from '../config/leave-type-crud'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

export function LeaveTypeListPage() {
  return (
    <CrudListPage
      config={LEAVE_TYPE_CRUD_CONFIG}
      topContent={<HrSetupTabs />}
      compactHeader
      toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
    />
  )
}
