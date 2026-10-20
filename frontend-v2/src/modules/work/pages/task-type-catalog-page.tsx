import { CrudListPage } from '@/shared/crud'
import { TASK_TYPE_CRUD_CONFIG } from '../config/task-type-crud'

/** Màn quản trị danh mục loại việc (duoc-CR-656). Gác quyền `setting` do `CrudListPage` lo. */
export function TaskTypeCatalogPage() {
  return <CrudListPage config={TASK_TYPE_CRUD_CONFIG} />
}
