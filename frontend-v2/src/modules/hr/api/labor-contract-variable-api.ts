import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams } from '@/shared/types/api'
import type {
  LaborContractInputField,
  LaborContractVariableCreatePayload,
  LaborContractVariable,
  LaborContractVariableDetail,
  LaborContractVariableList,
  LaborContractVariableUpdatePayload,
} from '../types/labor-contract-variable'

const BASE_URL = '/api/labor-contract-variables'

export const laborContractVariableApi = {
  list: (params: ListParams) => apiGet<LaborContractVariableList>(BASE_URL, { params }),

  /** Một biến kèm nơi đang dùng + cờ khóa mã. */
  get: (id: number) => apiGet<LaborContractVariableDetail>(`${BASE_URL}/${id}`),

  /** Ô nhập của hộp hợp đồng. `includeInactive` để hộp Sửa hiện giá trị biến đã ngừng dùng (chỉ đọc). */
  inputFields: (includeInactive: boolean) =>
    apiGet<LaborContractInputField[]>(`${BASE_URL}/input-fields`, {
      params: includeInactive ? { include_inactive: true } : undefined,
    }),

  create: (payload: LaborContractVariableCreatePayload) => apiPost<LaborContractVariable>(BASE_URL, payload),

  update: (id: number, payload: LaborContractVariableUpdatePayload) =>
    apiPatch<LaborContractVariable>(`${BASE_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),
}
