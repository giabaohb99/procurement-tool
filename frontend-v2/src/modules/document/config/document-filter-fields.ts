import type { FilterFieldDefinition } from '@/shared/conditional-filter'
import { DOCUMENT_TYPE_FLAGS, DOC_GROUP_LABELS } from '../types/document-type'

/**
 * Trường của BỘ LỌC NÂNG CAO trên danh sách Loại văn bản.
 *
 * Danh mục này nạp cả danh sách một lần rồi lọc NGAY TẠI TRÌNH DUYỆT
 * (`helpers/filter-document-types.ts`) — dưới 100 dòng thì lọc ở client nhanh
 * hơn gọi lại API. `name` vì thế chỉ cần trùng tên trường của `DocumentType`.
 *
 * Nếu sau này danh mục phình lên và phải lọc phía server, `name` phải nằm trong
 * whitelist `filterable` của `doc_type_router`.
 */
export const DOCUMENT_TYPE_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã loại', type: 'text' },
  { name: 'name', label: 'Tên loại', type: 'text' },
  { name: 'description', label: 'Mô tả', type: 'text' },
  {
    name: 'group_code',
    label: 'Nhóm',
    type: 'select',
    options: Object.entries(DOC_GROUP_LABELS).map(([value, label]) => ({ value, label })),
  },
  {
    name: 'id_scheme',
    label: 'Kiểu định danh',
    type: 'select',
    options: [
      { value: '1', label: 'Mã tài liệu bất biến' },
      { value: '2', label: 'Số hiệu theo sổ' },
    ],
  },
  { name: 'is_active', label: 'Đang dùng', type: 'boolean', operators: ['is'] },
  // Mỗi cờ trong "Quy tắc áp dụng" cũng là một điều kiện lọc được.
  ...DOCUMENT_TYPE_FLAGS.map(
    (flag): FilterFieldDefinition => ({
      name: flag.key,
      label: flag.label,
      type: 'boolean',
      operators: ['is'],
    }),
  ),
]
