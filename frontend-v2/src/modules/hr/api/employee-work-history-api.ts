import { apiDelete, apiGet, apiPatch, apiPost, httpClient } from '@/core/api'
import type {
  EmployeeWorkHistoryApplyResult,
  EmployeeWorkHistoryListResult,
  EmployeeWorkHistoryPayload,
  EmployeeWorkHistorySaveResult,
  WorkHistoryFile,
} from '../types/employee-work-history'

const BASE_URL = '/api/employees'

/** Entity dùng cho cửa đính kèm dùng chung (A6 — riêng tư, cha `employee`). */
const FILE_ENTITY = 'employee_work_history'

/**
 * `to_date` / `decision_date` rỗng phải gửi `null`, không gửi chuỗi rỗng —
 * cột đích là `DATE NULL` (cùng luật `employee-api.ts::toEmployeePayload`).
 */
export function toWorkHistoryPayload(
  values: Omit<EmployeeWorkHistoryPayload, 'to_date' | 'decision_date'> & {
    to_date: string
    decision_date: string
  },
): EmployeeWorkHistoryPayload {
  return {
    ...values,
    to_date: values.to_date ? values.to_date : null,
    decision_date: values.decision_date ? values.decision_date : null,
  }
}

export const employeeWorkHistoryApi = {
  list: (employeeId: number) =>
    apiGet<EmployeeWorkHistoryListResult>(`${BASE_URL}/${employeeId}/work-history`),

  listMine: () => apiGet<EmployeeWorkHistoryListResult>(`${BASE_URL}/me/work-history`),

  create: (employeeId: number, payload: EmployeeWorkHistoryPayload) =>
    apiPost<EmployeeWorkHistorySaveResult>(`${BASE_URL}/${employeeId}/work-history`, payload),

  update: (employeeId: number, id: number, payload: EmployeeWorkHistoryPayload) =>
    apiPatch<EmployeeWorkHistorySaveResult>(
      `${BASE_URL}/${employeeId}/work-history/${id}`,
      payload,
    ),

  remove: (employeeId: number, id: number) =>
    apiDelete<null>(`${BASE_URL}/${employeeId}/work-history/${id}`),

  apply: (employeeId: number, id: number) =>
    apiPost<EmployeeWorkHistoryApplyResult>(`${BASE_URL}/${employeeId}/work-history/${id}/apply`),
}

export function fetchWorkHistoryFiles(historyId: number) {
  return apiGet<WorkHistoryFile[]>('/api/attachments', {
    params: { entity: FILE_ENTITY, entity_id: historyId },
  })
}

/** `multipart/form-data` — dùng `httpClient` thẳng, KHÔNG đặt tay `Content-Type`. */
export async function uploadWorkHistoryFiles(
  historyId: number,
  files: File[],
): Promise<WorkHistoryFile[]> {
  const form = new FormData()
  form.append('entity', FILE_ENTITY)
  form.append('entity_id', String(historyId))
  for (const file of files) form.append('files', file)

  const res = await httpClient.post<{ data: WorkHistoryFile[] }>('/api/attachments', form)
  return res.data.data
}

export function deleteWorkHistoryFile(linkId: number) {
  return apiDelete(`/api/attachments/${linkId}`)
}

/** Đường tải về CÓ KIỂM QUYỀN — đưa cho `downloadFile`, đừng gắn vào `<a href>`. */
export function workHistoryFileDownloadUrl(linkId: number) {
  return `/api/attachments/${linkId}/download`
}

/** Đường xem CÓ KIỂM QUYỀN — đưa cho `fetchBlobUrl` (qua `AttachmentPreviewDialog`). */
export function workHistoryFileViewUrl(linkId: number) {
  return `/api/attachments/${linkId}/view`
}
