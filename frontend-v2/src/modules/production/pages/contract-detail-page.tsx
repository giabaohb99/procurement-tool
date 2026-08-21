import { CrudDetailPage } from '@/shared/crud'
import { CONTRACT_CRUD_CONFIG } from '../config/contract-crud'

export function ContractDetailPage() {
  return <CrudDetailPage config={CONTRACT_CRUD_CONFIG} />
}
