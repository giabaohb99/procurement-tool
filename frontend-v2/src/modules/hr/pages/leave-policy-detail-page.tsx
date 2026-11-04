import { CrudDetailPage } from '@/shared/crud'
import { LEAVE_POLICY_CRUD_CONFIG } from '../config/leave-policy-crud'

/** Chi tiết / thêm mới Chính sách nghỉ phép (duoc-CR-717) — `/new` và `/:id` dùng chung trang này. */
export function LeavePolicyDetailPage() {
  return <CrudDetailPage config={LEAVE_POLICY_CRUD_CONFIG} />
}
