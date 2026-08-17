import type { FilterFieldDefinition } from '@/shared/conditional-filter'
import { STATUS_LABELS } from '../types/document-record'
import { CONFIDENTIAL_LEVELS, URGENCY_LEVELS } from '../types/security-level'

/**
 * Trường của BỘ LỌC NÂNG CAO trên màn "Văn bản áp dụng cho tôi" (F05).
 *
 * ⚠️ Lọc chạy NGAY TẠI TRÌNH DUYỆT (`applyClientFilter`), không gửi query param.
 * Không phải vì danh sách nhỏ, mà vì `/api/documents/applies-to-me` tính phạm vi
 * bằng vòng lặp Python (`scope_service.document_ids_for`) rồi mới trả về —
 * không có tầng truy vấn nào để cắm thêm điều kiện vào. Bù lại, đằng nào endpoint
 * cũng trả hết một lượt nên lọc ở client không tốn thêm vòng gọi nào.
 *
 * `name` vì thế chỉ cần trùng tên trường của `DocumentRecord`, KHÔNG cần nằm
 * trong whitelist `filterable` của controller như các màn danh sách khác.
 */
export const DOCUMENT_APPLIED_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'title', label: 'Trích yếu', type: 'text' },
  { name: 'display_code', label: 'Số hiệu', type: 'text' },
  { name: 'doc_type_name', label: 'Loại văn bản', type: 'text' },
  { name: 'company_name', label: 'Pháp nhân ban hành', type: 'text' },
  { name: 'department_name', label: 'Phòng chủ trì', type: 'text' },
  { name: 'owner_name', label: 'Người chịu trách nhiệm', type: 'text' },
  { name: 'keywords', label: 'Từ khóa', type: 'text' },
  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    options: Object.entries(STATUS_LABELS).map(([value, label]) => ({ value, label })),
  },
  {
    name: 'secrecy_level',
    label: 'Mức mật',
    type: 'select',
    options: CONFIDENTIAL_LEVELS.map((item) => ({ value: String(item.id), label: item.name })),
  },
  {
    name: 'urgency',
    label: 'Độ khẩn',
    type: 'select',
    options: URGENCY_LEVELS.map((item) => ({ value: String(item.id), label: item.name })),
  },
  { name: 'effective_date', label: 'Ngày hiệu lực', type: 'date' },
  { name: 'expire_date', label: 'Ngày hết hiệu lực', type: 'date' },
  //  Cờ này là lý do chính người ta mở màn hình này ra: văn bản mình phải làm
  //  theo vừa bị đổi.
  { name: 'needs_review', label: 'Cần rà lại', type: 'boolean', operators: ['is'] },
]
