import { CrudDetailPage } from '@/shared/crud'
import { PRODUCT_CRUD_CONFIG } from '../config/product-crud'

export function ProductDetailPage() {
  return <CrudDetailPage config={PRODUCT_CRUD_CONFIG} />
}
