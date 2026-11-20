/** duoc-CR-784 — danh mục Định mức bao bì theo mã HH (sửa trong hộp thoại, nạp hàng loạt bằng "Nhập từ Excel"). */
import { CrudListPage } from '@/shared/crud'

import { PACKAGING_BOM_CRUD_CONFIG } from '../config/packaging-bom-crud'

export function PackagingBomListPage() {
  return <CrudListPage config={PACKAGING_BOM_CRUD_CONFIG} />
}
