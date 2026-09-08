import { CrudListPage } from '@/shared/crud'
import { JOB_POSITION_CRUD_CONFIG } from '../config/job-position-crud'

export function JobPositionListPage() {
  return <CrudListPage config={JOB_POSITION_CRUD_CONFIG} />
}
