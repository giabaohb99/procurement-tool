import { CrudDetailPage } from '@/shared/crud'
import { ITEM_GROUP_CRUD_CONFIG } from '../config/item-group-crud'

export function ItemGroupDetailPage() {
  return <CrudDetailPage config={ITEM_GROUP_CRUD_CONFIG} />
}
