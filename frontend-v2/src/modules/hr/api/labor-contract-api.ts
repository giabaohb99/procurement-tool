import { apiDelete, apiGet, apiPatch, apiPost, apiPut, downloadFile } from '@/core/api'
import type {
  LaborContract,
  LaborContractGeneratePayload,
  LaborContractListResult,
  LaborContractPayload,
  LaborContractSaveResult,
  LaborContractTemplateOption,
  LaborContractTransitionPayload,
  LaborContractUpdatePayload,
} from '../types/labor-contract'

const EMPLOYEE_URL = '/api/employees'
const CONTRACT_URL = '/api/labor-contracts'

/** Lớp gọi API hợp đồng lao động — hình dạng khớp serializer/controller thật của backend. */
export const laborContractApi = {
  listByEmployee: (employeeId: number) =>
    apiGet<LaborContractListResult>(`${EMPLOYEE_URL}/${employeeId}/labor-contracts`),

  /** Mẫu `is_active` của pháp nhân HIỆN TẠI của nhân sự (dùng khi LẬP HĐ mới), lọc theo loại (bỏ trống = mọi loại). 403 nếu nhân sự ngoài phạm vi. */
  listTemplateOptions: (employeeId: number, contractType?: number) =>
    apiGet<LaborContractTemplateOption[]>(
      `${EMPLOYEE_URL}/${employeeId}/labor-contract-templates`,
      { params: contractType ? { contract_type: contractType } : undefined },
    ),

  /** Mẫu chọn được để sinh tệp cho MỘT hợp đồng: `is_active`, đúng pháp nhân + loại của CHÍNH HĐ (snapshot lúc lập, không theo pháp nhân hiện tại của nhân sự). */
  listTemplateOptionsForContract: (id: number) =>
    apiGet<LaborContractTemplateOption[]>(`${CONTRACT_URL}/${id}/templates`),

  create: (employeeId: number, payload: LaborContractPayload) =>
    apiPost<LaborContractSaveResult>(`${EMPLOYEE_URL}/${employeeId}/labor-contracts`, payload),

  getById: (id: number) => apiGet<LaborContract>(`${CONTRACT_URL}/${id}`),

  update: (id: number, payload: LaborContractUpdatePayload) =>
    apiPatch<LaborContractSaveResult>(`${CONTRACT_URL}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${CONTRACT_URL}/${id}`),

  generate: (id: number, payload: LaborContractGeneratePayload) =>
    apiPost<LaborContract>(`${CONTRACT_URL}/${id}/generate`, payload),

  transition: (id: number, payload: LaborContractTransitionPayload) =>
    apiPost<LaborContract>(`${CONTRACT_URL}/${id}/transition`, payload),

  uploadSignedFile: (id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiPut<LaborContract>(`${CONTRACT_URL}/${id}/signed-file`, form)
  },

  /** Bản .docx đã sinh — backend đòi quyền `print`. Tên tệp do server đặt. */
  downloadDocument: (id: number, fallbackName: string) =>
    downloadFile(`${CONTRACT_URL}/${id}/document`, fallbackName),

  downloadSignedFile: (id: number, fallbackName: string) =>
    downloadFile(`${CONTRACT_URL}/${id}/signed-file`, fallbackName),
}
