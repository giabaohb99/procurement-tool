/**
 * Tệp đính kèm của VĂN BẢN nhận những đuôi nào, nặng tối đa bao nhiêu.
 *
 * ⚠️ BẢN CHÉP TAY của `_DOC` + trần `50` MB ở mục `"document_version"` trong
 * `backend/app/core/file_registry.py` — backend là chốt thật (`guard_upload`
 * còn soi cả byte đầu tệp), bản này chỉ để NÓI TRƯỚC cho người dùng và lọc hộp
 * chọn tệp. Đổi bên kia mà quên bên này thì: thiếu đuôi → hộp chọn giấu mất tệp
 * hợp lệ; thừa đuôi → người dùng chọn được rồi mới ăn lỗi 400.
 */
export const DOCUMENT_FILE_EXTENSIONS = [
  'pdf',
  'doc',
  'docx',
  'xls',
  'xlsx',
  'jpg',
  'jpeg',
  'png',
  'webp',
  'txt',
  'csv',
  'xml',
  'msg',
  'eml',
  'cdr',
] as const

export const DOCUMENT_FILE_MAX_MB = 50

/** Thuộc tính `accept` của ô chọn tệp — `.pdf,.doc,…`. */
export const DOCUMENT_FILE_ACCEPT = DOCUMENT_FILE_EXTENSIONS.map((ext) => `.${ext}`).join(',')

/** Dòng nhắc dưới vùng thả: `Định dạng PDF, DOC, … (tối đa 50 MB mỗi tệp)`. */
export function describeDocumentFilePolicy(): string {
  const list = DOCUMENT_FILE_EXTENSIONS.map((ext) => ext.toUpperCase()).join(', ')
  return `Định dạng ${list} (tối đa ${DOCUMENT_FILE_MAX_MB} MB mỗi tệp)`
}
