// bao-CR-495 — danh mục từ đồng nghĩa cho ô tìm tên hàng của màn Tra cứu giá hải quan.
import { CrudListPage } from '@/shared/crud'

import { CUSTOMS_SEARCH_SYNONYM_CRUD_CONFIG } from '../config/customs-search-synonym-crud'

export function CustomsSearchSynonymListPage() {
  return <CrudListPage config={CUSTOMS_SEARCH_SYNONYM_CRUD_CONFIG} />
}
