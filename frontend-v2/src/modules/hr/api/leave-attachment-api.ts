import { apiDelete, apiGet, httpClient } from '@/core/api'

/**
 * TỆP ĐÍNH KÈM của đơn nghỉ phép (bao-CR-505) — đi qua cửa đính kèm dùng chung
 * `/api/attachments` với `entity=leave_request`.
 *
 * Không có endpoint riêng, và đó là chủ ý: `leave_request` đã khai ở `FILE_POLICY`
 * (`backend/app/core/file_registry.py`), nên cửa chung tự gác đủ hai lớp — quyền
 * vai trò trên `leave_request`, rồi phạm vi của ĐÚNG tờ đơn kèm ngoại lệ người
 * đang phải ký (`attachment_scope._ensure_leave_request`). Dựng cửa riêng là phải
 * chép lại cả hai lớp đó.
 */

/** Một dòng đính kèm — khớp `_link_out` ở `attachment/controller.py`. */
export interface LeaveAttachment {
  /** ID của LIÊN KẾT, không phải của tệp — mọi thao tác sau này dùng số này. */
  id: number
  file_id: number
  filename: string
  /**
   * ⚠️ **LUÔN RỖNG.** `leave_request` nằm trong `PRIVATE_ENTITIES` (giấy khám
   * bệnh là dữ liệu sức khỏe), nên backend không trả đường đọc thẳng kho. Xem
   * trước / in thì gọi `/view`, tải về thì `/download`, cả hai qua `httpClient`.
   */
  url: string
  content_type: string
  size: number
}

const ENTITY = 'leave_request'

export function fetchLeaveAttachments(requestId: number) {
  return apiGet<LeaveAttachment[]>('/api/attachments', {
    params: { entity: ENTITY, entity_id: requestId },
  })
}

/**
 * Dùng `httpClient` thẳng vì đây là `multipart/form-data`. KHÔNG đặt tay
 * `Content-Type` — trình duyệt phải tự sinh chuỗi `boundary`.
 */
export async function uploadLeaveAttachments(
  requestId: number,
  files: File[],
): Promise<LeaveAttachment[]> {
  const form = new FormData()
  form.append('entity', ENTITY)
  form.append('entity_id', String(requestId))
  for (const file of files) form.append('files', file)

  const res = await httpClient.post<{ data: LeaveAttachment[] }>('/api/attachments', form)
  return res.data.data
}

export function deleteLeaveAttachment(linkId: number) {
  return apiDelete(`/api/attachments/${linkId}`)
}

/** Đường tải về CÓ KIỂM QUYỀN — đưa cho `downloadFile`, đừng gắn vào `<a href>`. */
export function leaveAttachmentDownloadUrl(linkId: number) {
  return `/api/attachments/${linkId}/download`
}

/** Đường xem CÓ KIỂM QUYỀN — đưa cho `fetchBlobUrl`, đừng gắn vào `<img src>`. */
export function leaveAttachmentViewUrl(linkId: number) {
  return `/api/attachments/${linkId}/view`
}
