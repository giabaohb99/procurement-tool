import type { FilterFieldDefinition } from '@/shared/conditional-filter'
import { ENTITY_LABELS } from '../helpers/entity-link'

/**
 * Trường của BỘ LỌC NÂNG CAO trên màn "Việc của tôi" (I17).
 *
 * ⚠️ Lọc chạy NGAY TẠI TRÌNH DUYỆT (`applyClientFilter`), không gửi query param.
 * `/api/approvals/my-tasks` gộp việc của chính mình với việc được ủy quyền bấm
 * thay rồi mới lọc theo phiên còn mở — làm bằng vòng lặp Python nên không có
 * tầng truy vấn để cắm điều kiện vào. Bù lại đây là hộp việc của MỘT người nên
 * số dòng nhỏ, và endpoint đằng nào cũng trả hết một lượt.
 *
 * `name` phải trùng tên trường của `MyTask`.
 */
export const MY_TASK_FILTER_FIELDS: FilterFieldDefinition[] = [
  {
    name: 'entity',
    label: 'Loại chứng từ',
    type: 'select',
    options: Object.entries(ENTITY_LABELS).map(([value, label]) => ({ value, label })),
  },
  { name: 'entity_code', label: 'Số hiệu', type: 'text' },
  { name: 'entity_title', label: 'Nội dung', type: 'text' },
  { name: 'node_name', label: 'Bước duyệt', type: 'text' },
  { name: 'started_by_name', label: 'Người trình', type: 'text' },
  { name: 'on_behalf_of_name', label: 'Bấm thay ai', type: 'text' },
  { name: 'due_at', label: 'Hạn duyệt', type: 'date' },
  //  Hai cờ dưới đây là hai câu người dùng hỏi nhiều nhất khi mở màn này ra.
  { name: 'is_overdue', label: 'Quá hạn', type: 'boolean', operators: ['is'] },
  { name: 'node_seq', label: 'Chặng thứ', type: 'number' },
]
