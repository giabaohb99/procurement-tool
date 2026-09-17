import { apiDelete, apiGet, httpClient } from '@/core/api'

/**
 * BẢN SCAN của hồ sơ — đi qua cửa đính kèm dùng chung `/api/attachments`.
 *
 * Không có endpoint riêng cho hồ sơ, và đó là chủ ý: `entity=dossier` đã khai ở
 * `FILE_POLICY` (`backend/app/core/file_registry.py`), nên cửa chung tự gác đủ
 * **hai lớp** — quyền vai trò trên `dossier`, rồi phạm vi dữ liệu của ĐÚNG bộ hồ
 * sơ đó (`attachment_scope.parent_records`). Dựng cửa riêng là phải chép lại cả
 * hai lớp ấy, và bản chép sẽ thiếu lớp thứ hai như mọi lần trước (lỗ N-13).
 */

/** Một dòng đính kèm — khớp `_link_out` ở `attachment/controller.py`. */
export interface DossierAttachment {
  /** ID của LIÊN KẾT, không phải của tệp — mọi thao tác sau này dùng số này. */
  id: number
  file_id: number
  filename: string
  /**
   * ⚠️ **LUÔN RỖNG với hồ sơ.** `dossier` nằm trong `PRIVATE_ENTITIES`, nên
   * backend cố ý không trả đường đọc thẳng kho lưu trữ — chuỗi đó không qua lớp
   * kiểm nào, ai cầm được là mở được, kể cả người chưa đăng nhập.
   *
   * Xem trước thì gọi `/api/attachments/{id}/view`, tải về thì `/download`, cả
   * hai qua `httpClient` để có token. Giữ khóa này trong kiểu để người đọc thấy
   * ngay là nó CÓ nhưng rỗng, thay vì đi tìm xem sao API không trả.
   */
  url: string
  thumb_url: string
  content_type: string
  size: number
  sha256: string
  entity: string
  entity_id: number
  doc_type: string
  sort_order: number
}

const ENTITY = 'dossier'

export function fetchDossierAttachments(dossierId: number) {
  return apiGet<DossierAttachment[]>('/api/attachments', {
    params: { entity: ENTITY, entity_id: dossierId },
  })
}

/**
 * Tải lên một hoặc nhiều bản scan.
 *
 * Dùng `httpClient` thẳng chứ không `apiPost`: đây là `multipart/form-data`, mà
 * `apiPost` khai kiểu payload là JSON. Không đặt tay `Content-Type` — trình
 * duyệt phải tự sinh, vì nó còn phải chèn chuỗi `boundary` mà ta không biết
 * trước; đặt tay là backend đọc ra một thân rỗng.
 */
export async function uploadDossierAttachments(
  dossierId: number,
  files: File[],
): Promise<DossierAttachment[]> {
  const form = new FormData()
  form.append('entity', ENTITY)
  form.append('entity_id', String(dossierId))
  for (const file of files) form.append('files', file)

  const res = await httpClient.post<{ data: DossierAttachment[] }>('/api/attachments', form)
  return res.data.data
}

export function deleteDossierAttachment(linkId: number) {
  return apiDelete(`/api/attachments/${linkId}`)
}

/** Đường tải về CÓ KIỂM QUYỀN — đưa cho `downloadFile`, đừng gắn vào `<a href>`. */
export function dossierAttachmentDownloadUrl(linkId: number) {
  return `/api/attachments/${linkId}/download`
}

/** Đường xem trước CÓ KIỂM QUYỀN — đưa cho `fetchBlobUrl`, đừng gắn vào `<img src>`. */
export function dossierAttachmentViewUrl(linkId: number) {
  return `/api/attachments/${linkId}/view`
}
