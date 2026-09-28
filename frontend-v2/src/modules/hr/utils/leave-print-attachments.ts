/**
 * Chia tệp đính kèm của đơn nghỉ phép thành hai nhóm cho BẢN IN (bao-CR-505):
 * ảnh thì in kèm ở mặt sau (mỗi ảnh một trang A4), tệp khác chỉ ghi tên.
 *
 * Danh sách kiểu ảnh phải khớp `INLINE_VIEW_TYPES` của
 * `backend/app/modules/attachment/controller.py`: ảnh in được là ảnh lấy về được
 * qua `/view`. Kiểu nằm ngoài danh sách đó (`image/svg+xml`, `image/heic`…) mà
 * xếp vào nhóm ảnh thì `/view` trả 415 và trang in treo ở «đang nạp ảnh» mãi.
 */

const PRINTABLE_IMAGE_TYPES = new Set([
  'image/png',
  'image/jpeg',
  'image/gif',
  'image/webp',
  'image/bmp',
])

const PRINTABLE_IMAGE_EXTENSION = /\.(png|jpe?g|gif|webp|bmp)$/i

interface AttachmentLike {
  filename: string
  content_type: string
}

/**
 * Ảnh in được hay không. `content_type` do backend suy từ nội dung tệp nên tin
 * nó trước; chỉ khi rỗng (dữ liệu cũ) mới đoán theo đuôi tên tệp.
 */
export function isPrintableImage(file: AttachmentLike): boolean {
  const type = (file.content_type || '').split(';')[0].trim().toLowerCase()
  if (type) return PRINTABLE_IMAGE_TYPES.has(type)
  return PRINTABLE_IMAGE_EXTENSION.test(file.filename || '')
}

/**
 * Câu «Tài liệu đính kèm» trên mặt đơn. Rỗng khi không có tệp nào — bên gọi
 * dựa vào đó để không in một dòng trơ trọi.
 *
 * Tệp không phải ảnh ghi TÊN (chúng không được in), ảnh chỉ ghi SỐ LƯỢNG vì bản
 * thân ảnh đã nằm ở các trang sau — ghi tên tệp ảnh kiểu `IMG_20260105.jpg`
 * không giúp người đọc giấy thêm gì.
 */
export function describeAttachmentsForPrint(
  images: readonly AttachmentLike[],
  others: readonly AttachmentLike[],
): string {
  const parts: string[] = []
  if (others.length > 0) parts.push(others.map((f) => f.filename).join(', '))
  if (images.length > 0) parts.push(`${images.length} ảnh in kèm ở các trang sau`)
  return parts.join('; ')
}

/** Tách giữ nguyên thứ tự: `images` in ở mặt sau, `others` chỉ ghi tên trên đơn. */
export function splitPrintableAttachments<T extends AttachmentLike>(
  files: readonly T[] | null | undefined,
): { images: T[]; others: T[] } {
  const images: T[] = []
  const others: T[] = []
  for (const file of files ?? []) {
    if (isPrintableImage(file)) images.push(file)
    else others.push(file)
  }
  return { images, others }
}
