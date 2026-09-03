import { CrudDetailPage } from '@/shared/crud'
import { LEAVE_TYPE_CRUD_CONFIG } from '../config/leave-type-crud'

export function LeaveTypeDetailPage() {
  return <CrudDetailPage config={LEAVE_TYPE_CRUD_CONFIG} />
}
