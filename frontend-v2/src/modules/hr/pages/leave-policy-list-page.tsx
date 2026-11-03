import { CrudListPage } from '@/shared/crud'
import { LeaveSectionTabs } from '../components/leave-section-tabs'
import { LEAVE_POLICY_CRUD_CONFIG } from '../config/leave-policy-crud'
import { LIST_SECTION_TOOLBAR_STICKY } from '../utils/list-sticky'

/** Danh sách Chính sách nghỉ phép (duoc-CR-717) — thẻ thứ 4 của "Nghỉ phép › Thiết lập". */
export function LeavePolicyListPage() {
  return (
    <CrudListPage
      config={LEAVE_POLICY_CRUD_CONFIG}
      beforeContent={<LeaveSectionTabs sticky />}
      toolbarClassName={LIST_SECTION_TOOLBAR_STICKY}
    />
  )
}
