/** duoc-CR-784 — danh sách Báo giá VTBB (thêm / sửa / xóa trong hộp thoại). */
import { CrudListPage } from '@/shared/crud'

import { PACKAGING_QUOTE_CRUD_CONFIG } from '../config/packaging-quote-crud'

export function PackagingQuoteListPage() {
  return <CrudListPage config={PACKAGING_QUOTE_CRUD_CONFIG} />
}
