import type { FilterFieldDefinition } from '@/shared/conditional-filter'
import { DOCUMENT_TYPE_OPTIONS } from '../types/document-type'

/**
 * Trường của BỘ LỌC NÂNG CAO trên danh sách Loại văn bản.
 *
 * Khác các màn khác: điều kiện ở đây được lọc NGAY TẠI TRÌNH DUYỆT
 * (`helpers/filter-document-types.ts`) vì chưa có backend, nên `name` chỉ cần
 * trùng tên trường của `DocumentType`. Khi nối API thì `name` phải nằm trong
 * `FILTERABLE` của controller.
 */
export const DOCUMENT_TYPE_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã loại', type: 'text' },
  { name: 'name', label: 'Tên loại', type: 'text' },
  { name: 'prefix', label: 'Tiền tố số hiệu', type: 'text' },
  { name: 'description', label: 'Mô tả', type: 'text' },
  { name: 'is_active', label: 'Đang dùng', type: 'boolean', operators: ['is'] },
  // Mỗi tùy chọn trong "Tùy chọn khác" cũng là một điều kiện lọc được.
  ...DOCUMENT_TYPE_OPTIONS.map(
    (option): FilterFieldDefinition => ({
      name: option.key,
      label: option.label,
      type: 'boolean',
      operators: ['is'],
    }),
  ),
]
