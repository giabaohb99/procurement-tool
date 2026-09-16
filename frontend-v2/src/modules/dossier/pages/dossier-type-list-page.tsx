import { CrudListPage } from '@/shared/crud'
import { DOSSIER_TYPE_CRUD_CONFIG } from '../config/dossier-type-crud'

/** Danh mục Loại hồ sơ — toàn bộ hành vi khai ở `dossier-type-crud.tsx`. */
export function DossierTypeListPage() {
  return <CrudListPage config={DOSSIER_TYPE_CRUD_CONFIG} />
}
