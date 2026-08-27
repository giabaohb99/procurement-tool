/**
 * Luật nhận tệp đính kèm chat (CR-204) — kiểm NGAY ở client trước khi tải lên,
 * khớp trần của backend (`app/modules/assistant/attachments.py`): ảnh JPG/PNG/WebP
 * tối đa 5MB, PDF tối đa 10MB, tối đa 3 tệp một tin. Backend vẫn kiểm lại theo
 * magic bytes — đây chỉ là chặn sớm cho đỡ tốn một lượt tải vô ích.
 */

export const MAX_ATTACHMENTS = 3

const MB = 1024 * 1024
const IMAGE_LIMIT = 5 * MB
const PDF_LIMIT = 10 * MB
const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']

/** Chuỗi accept cho <input type="file"> — đúng 4 loại backend nhận. */
export const ACCEPT_ATTACHMENTS = 'image/jpeg,image/png,image/webp,application/pdf'

/** Trả thông điệp lỗi tiếng Việt nếu tệp bị từ chối; hợp lệ thì null. */
export function validateAttachment(file: File): string | null {
  if (file.type === 'application/pdf') {
    return file.size > PDF_LIMIT ? `PDF tối đa 10MB — "${file.name}" quá lớn` : null
  }
  if (IMAGE_TYPES.includes(file.type)) {
    return file.size > IMAGE_LIMIT ? `Ảnh tối đa 5MB — "${file.name}" quá lớn` : null
  }
  return `Chỉ nhận ảnh JPG/PNG/WebP hoặc PDF — "${file.name}" không đúng loại`
}
