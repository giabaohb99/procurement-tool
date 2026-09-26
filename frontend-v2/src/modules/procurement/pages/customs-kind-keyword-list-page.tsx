// bao-CR-494 — danh mục từ khóa Thành phẩm / Nguyên liệu (cấu hình của màn Tra cứu giá hải quan).
import { CrudListPage } from '@/shared/crud'

import { CUSTOMS_KIND_KEYWORD_CRUD_CONFIG } from '../config/customs-kind-keyword-crud'

export function CustomsKindKeywordListPage() {
  return <CrudListPage config={CUSTOMS_KIND_KEYWORD_CRUD_CONFIG} />
}
