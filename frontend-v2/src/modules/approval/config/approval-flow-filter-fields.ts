import type { FilterFieldDefinition } from '@/shared/conditional-filter'
import { ENTITY_LABELS } from '../helpers/entity-link'

/**
 * Trường của BỘ LỌC NÂNG CAO trên danh sách Luồng duyệt.
 *
 * Danh sách này nạp cả một lượt rồi lọc NGAY TẠI TRÌNH DUYỆT
 * (`applyClientFilter`) — số luồng đếm bằng chục, lọc ở client nhanh hơn gọi lại
 * API. `name` chỉ cần trùng tên trường của `ApprovalFlow`.
 */
export const APPROVAL_FLOW_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'name', label: 'Tên luồng', type: 'text' },
  { name: 'code', label: 'Mã luồng', type: 'text' },
  { name: 'description', label: 'Mô tả', type: 'text' },
  {
    name: 'entity',
    label: 'Loại chứng từ',
    type: 'select',
    options: Object.entries(ENTITY_LABELS).map(([value, label]) => ({ value, label })),
  },
  { name: 'is_active', label: 'Đang dùng', type: 'boolean', operators: ['is'] },
  { name: 'node_count', label: 'Số bước', type: 'number' },
  { name: 'version_no', label: 'Bản', type: 'number' },
  { name: 'priority', label: 'Độ ưu tiên', type: 'number' },
  //  Luồng không khai điều kiện là luồng MẶC ĐỊNH — lọc "để trống" là tìm đúng
  //  những luồng đó.
  { name: 'condition', label: 'Điều kiện áp dụng', type: 'text' },
]
