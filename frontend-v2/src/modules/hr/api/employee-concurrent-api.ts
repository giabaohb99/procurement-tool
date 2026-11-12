import { apiDelete, apiGet, apiPatch, apiPost, httpClient } from '@/core/api'
import type {
  EmployeeConcurrent,
  EmployeeConcurrentListResult,
  EmployeeConcurrentPayload,
} from '../types/employee-concurrent'
import type { WorkHistoryFile } from '../types/employee-work-history'

const BASE_URL = '/api/employees'

/** Entity tệp QĐ kiêm nhiệm ở cửa đính kèm dùng chung (riêng tư, cha `employee`). */
const FILE_ENTITY = 'employee_concurrent'

/** Giá trị form → thân API: hai ô ngày bỏ trống gửi `null` (cột `DATE NULL`), chữ được cắt khoảng trắng. */
export function toConcurrentPayload(
  values: Omit<EmployeeConcurrentPayload, 'to_date' | 'decision_date'> & {
    to_date: string
    decision_date: string
  },
): EmployeeConcurrentPayload {
  return {
    company_id: values.company_id,
    department_id: values.department_id,
    position_id: values.position_id,
    from_date: values.from_date,
    to_date: values.to_date ? values.to_date : null,
    decision_no: values.decision_no.trim(),
    decision_date: values.decision_date ? values.decision_date : null,
    note: values.note.trim(),
    counts_scope: values.counts_scope,
  }
}

/** Tầng HTTP của tab Kiêm nhiệm — đường ở `employee/concurrent_controller.py`. */
export const employeeConcurrentApi = {
  list: (employeeId: number) =>
    apiGet<EmployeeConcurrentListResult>(`${BASE_URL}/${employeeId}/concurrents`),

  create: (employeeId: number, payload: EmployeeConcurrentPayload) =>
    apiPost<{ item: EmployeeConcurrent }>(`${BASE_URL}/${employeeId}/concurrents`, payload),

  /** Sửa TẠI CHỖ — id dòng và tệp QĐ giữ nguyên. */
  update: (employeeId: number, id: number, payload: EmployeeConcurrentPayload) =>
    apiPatch<{ item: EmployeeConcurrent }>(`${BASE_URL}/${employeeId}/concurrents/${id}`, payload),

  /** Xóa dòng kéo theo xóa tệp QĐ (backend đòi thêm quyền xem nhạy cảm nếu dòng có tệp). */
  remove: (employeeId: number, id: number) =>
    apiDelete<null>(`${BASE_URL}/${employeeId}/concurrents/${id}`),
}

export function fetchConcurrentFiles(concurrentId: number) {
  return apiGet<WorkHistoryFile[]>('/api/attachments', {
    params: { entity: FILE_ENTITY, entity_id: concurrentId },
  })
}

/** `multipart/form-data` — dùng `httpClient` thẳng, KHÔNG đặt tay `Content-Type`. */
export async function uploadConcurrentFiles(
  concurrentId: number,
  files: File[],
): Promise<WorkHistoryFile[]> {
  const form = new FormData()
  form.append('entity', FILE_ENTITY)
  form.append('entity_id', String(concurrentId))
  for (const file of files) form.append('files', file)

  const res = await httpClient.post<{ data: WorkHistoryFile[] }>('/api/attachments', form)
  return res.data.data
}

export function deleteConcurrentFile(linkId: number) {
  return apiDelete(`/api/attachments/${linkId}`)
}
