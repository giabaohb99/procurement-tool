/**
 * Tệp nào MỞ TẠI CHỖ được, và mở bằng đường nào.
 *
 * Ba nhóm, ba cách khác nhau:
 *
 * | Nhóm | Đường | Vì sao |
 * | --- | --- | --- |
 * | Ảnh | `/view` → `<img>` | trình duyệt vẽ sẵn |
 * | PDF | `/view` → `<iframe>` | trình xem PDF có sẵn, đẹp hơn mọi bản chuyển đổi |
 * | Word · Markdown · HTML | `/preview` → HTML | trình duyệt không đọc được `.docx`, phải đổi ở máy chủ |
 *
 * ⚠️ **SVG cố ý không có mặt** ở cả hai đầu. Trả tệp `inline` từ miền của API
 * nghĩa là nội dung chạy trong ngữ cảnh miền đó, mà SVG mang được JavaScript —
 * mở ra là nó đọc được token. Ảnh raster và PDF thì trình duyệt vẽ, không chạy.
 *
 * Danh sách ảnh/PDF phải khớp `KIEU_XEM_TAI_CHO` ở
 * `backend/app/modules/attachment/controller.py`; nhóm Word khớp `ALLOWED_EXTS`
 * của `document/import_service.py`.
 *
 * Để ở tệp riêng vì bên cạnh nó là component: tệp vừa xuất component vừa xuất
 * hàm thì hỏng hot reload của Vite (`react-refresh/only-export-components`).
 */
export const VIEWABLE_IMAGE_TYPES = [
  'image/png',
  'image/jpeg',
  'image/gif',
  'image/webp',
  'image/bmp',
]
export const PDF_CONTENT_TYPE = 'application/pdf'

/**
 * Đuôi tệp đọc bằng đường chuyển-sang-HTML.
 *
 * Nhận theo ĐUÔI TỆP chứ không theo `content_type`: tệp tải lên từ máy Windows
 * hay từ Zalo thường về tới nơi với kiểu rỗng hoặc
 * `application/octet-stream`, mà đuôi thì luôn còn.
 */
const HTML_EXTENSION = ['docx', 'doc', 'md', 'markdown', 'html', 'htm']

function normalizeContentType(contentType: string | undefined): string {
  return (contentType || '').split(';')[0].trim().toLowerCase()
}

function extensionOf(filename: string | undefined): string {
  const name = filename || ''
  return name.includes('.') ? name.split('.').pop()!.toLowerCase() : ''
}

export function isImage(contentType: string | undefined): boolean {
  return VIEWABLE_IMAGE_TYPES.includes(normalizeContentType(contentType))
}

export function isPdf(contentType: string | undefined, filename?: string): boolean {
  return normalizeContentType(contentType) === PDF_CONTENT_TYPE || extensionOf(filename) === 'pdf'
}

/** Tệp phải ĐỔI SANG HTML mới xem được (Word, Markdown, HTML). */
export function viewAsHtml(contentType: string | undefined, filename?: string): boolean {
  if (isImage(contentType) || isPdf(contentType, filename)) return false
  return HTML_EXTENSION.includes(extensionOf(filename))
}

export function canPreviewInline(contentType: string | undefined, filename?: string): boolean {
  return isImage(contentType) || isPdf(contentType, filename) || viewAsHtml(contentType, filename)
}
