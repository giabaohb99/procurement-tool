import { apiDelete, apiGet, apiPatch, apiPost, apiPut, downloadFile } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type {
  LaborContractPlaceholder,
  LaborContractTemplate,
  LaborContractTemplateContent,
  LaborContractTemplateFormValues,
  LaborContractTemplateUpdatePayload,
} from '../types/labor-contract'

const BASE_URL = '/api/labor-contract-templates'

/** Trần dung lượng tệp mẫu — khớp trần 10MB của backend. */
export const TEMPLATE_MAX_BYTES = 10 * 1024 * 1024

/** Kiểm tệp trước khi gửi. Trả câu báo lỗi, hoặc `null` nếu ổn. Backend vẫn là chuẩn. */
export function validateTemplateFile(file: File | null | undefined): string | null {
  if (!file) return 'Chọn tệp mẫu .docx'
  if (!file.name.toLowerCase().endsWith('.docx')) return 'Chỉ nhận tệp Word .docx'
  if (file.size <= 0) return 'Tệp rỗng'
  if (file.size > TEMPLATE_MAX_BYTES) return 'Tệp lớn hơn 10 MB'
  return null
}

/**
 * Dựng `multipart/form-data` cho hộp tải lên. Ném lỗi khi `company_id` / `contract_type`
 * còn 0: `0` là «chưa chọn», gửi đi chỉ để ăn 422 hoặc — tệ hơn — gắn nhầm pháp nhân.
 * KHÔNG đặt tay `Content-Type` (trình duyệt tự thêm boundary).
 */
export function buildTemplateFormData(
  values: LaborContractTemplateFormValues,
  file: File,
): FormData {
  if (!Number.isInteger(values.company_id) || values.company_id <= 0) {
    throw new Error('Chọn pháp nhân')
  }
  if (!Number.isInteger(values.contract_type) || values.contract_type <= 0) {
    throw new Error('Chọn loại hợp đồng')
  }
  const form = new FormData()
  form.append('file', file)
  form.append('name', values.name.trim())
  form.append('company_id', String(values.company_id))
  form.append('contract_type', String(values.contract_type))
  form.append('note', values.note.trim())
  return form
}

export const laborContractTemplateApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<LaborContractTemplate>>(BASE_URL, { params }),

  placeholders: () => apiGet<LaborContractPlaceholder[]>(`${BASE_URL}/placeholders`),

  get: (id: number) => apiGet<LaborContractTemplate>(`${BASE_URL}/${id}`),

  /** duoc-CR-606 — tệp mẫu mở thành HTML để soạn trên web. */
  content: (id: number) => apiGet<LaborContractTemplateContent>(`${BASE_URL}/${id}/content`),

  /** Lưu nội dung soạn trên web; biến sai → 422 kèm `details.unknown` như lúc tải tệp. */
  saveContent: (id: number, payload: LaborContractTemplateContent) =>
    apiPut<LaborContractTemplate>(`${BASE_URL}/${id}/content`, payload),

  create: (values: LaborContractTemplateFormValues, file: File) =>
    apiPost<LaborContractTemplate>(BASE_URL, buildTemplateFormData(values, file)),

  update: (id: number, payload: LaborContractTemplateUpdatePayload) =>
    apiPatch<LaborContractTemplate>(`${BASE_URL}/${id}`, payload),

  replaceFile: (id: number, file: File) => {
    const form = new FormData()
    form.append('file', file)
    return apiPut<LaborContractTemplate>(`${BASE_URL}/${id}/file`, form)
  },

  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),

  /** Đi qua `httpClient` (có token) — KHÔNG gắn vào `<a href>`; backend không trả `url`. */
  download: (template: Pick<LaborContractTemplate, 'id' | 'original_filename'>) =>
    downloadFile(`${BASE_URL}/${template.id}/file`, template.original_filename || 'mau-hop-dong.docx'),
}
