import {
  DEFAULT_DOCUMENT_TYPES,
  DOCUMENT_TYPE_OPTIONS,
  type DocumentType,
} from '../types/document-type'
import { createLocalCollection } from './local-collection'

/** Kho tạm của danh mục LOẠI VĂN BẢN. */
export const documentTypeCollection = createLocalCollection<DocumentType>({
  storageKey: 'erp.document-types',
  seed: DEFAULT_DOCUMENT_TYPES,
  labels: {
    code: 'mã',
    name: 'tên',
    prefix: 'tiền tố',
    description: 'mô tả',
    is_active: 'trạng thái',
    // Nhãn tùy chọn lấy từ chính khai báo dùng cho form, khỏi lệch chữ.
    ...Object.fromEntries(
      DOCUMENT_TYPE_OPTIONS.map((option) => [option.key, `"${option.label}"`]),
    ),
  },
})

/** Dữ liệu form gửi lên: đúng bản ghi nhưng chưa có id. */
export type DocumentTypeInput = Omit<DocumentType, 'id'>
