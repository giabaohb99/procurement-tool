import { CrudListPage } from '@/shared/crud'
import { PRODUCT_CRUD_CONFIG } from '../config/product-crud'

export function ProductListPage() {
  return <CrudListPage config={PRODUCT_CRUD_CONFIG} />
}
