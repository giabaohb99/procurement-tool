import { CrudListPage } from '@/shared/crud'
import { ITEM_GROUP_CRUD_CONFIG } from '../config/item-group-crud'

export function ItemGroupListPage() {
  return <CrudListPage config={ITEM_GROUP_CRUD_CONFIG} />
}
