import type { FilterFieldDefinition, OperatorType } from '@/shared/conditional-filter'
import { CLERK_STATUS_LABELS } from '../types/seal-clerk'

/**
 * Trường của **BỘ LỌC NÂNG CAO** ở danh sách Phân công văn thư.
 *
 * ⚠️ Bộ lọc này chạy **TẠI TRÌNH DUYỆT** (`applyClientFilter`), không dịch thành
 * query param như phần lớn màn danh sách khác — và đó là chủ ý, không phải tắt:
 * `/api/seal-clerks` gộp/lọc/sắp bằng vòng lặp Python và chỉ nhận đúng `search`
 * + `company_id`, nên tham số kiểu `is_head__eq` gửi xuống sẽ bị **nuốt im
 * lặng** (người dùng tưởng đã lọc mà đang nhìn nguyên danh sách). Màn này vốn
 * tải hết một lần để đếm cho đúng, nên lọc tại chỗ là đường duy nhất trung thực.
 *
 * ⚠️ Vì thế **chỉ khai trường có mặt phẳng trong một dòng `SealClerkGroup`**.
 * `companies` là MẢNG object — `applyClientFilter` đem `String()` cả mảng ra so,
 * tức luôn trượt; lọc theo công ty đã có ô chọn riêng trên thanh công cụ (đường
 * đó backend lọc thật).
 */
const TEXT_OPERATORS: OperatorType[] = ['contains', 'not_contains', 'is', 'is_not']

export const SEAL_CLERK_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'employee_name', label: 'Tên văn thư', type: 'text', operators: TEXT_OPERATORS },
  { name: 'employee_code', label: 'Mã văn thư', type: 'text', operators: TEXT_OPERATORS },
  {
    name: 'is_head',
    label: 'Văn thư tổng',
    type: 'boolean',
    operators: ['is'],
    options: [
      { value: 'true', label: 'Có — đa pháp nhân' },
      { value: 'false', label: 'Không — đơn pháp nhân' },
    ],
  },
  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    operators: ['is', 'is_not', 'in', 'not_in'],
    options: Object.entries(CLERK_STATUS_LABELS).map(([value, label]) => ({ value, label })),
  },
  {
    //  "Ai đang ôm nhiều pháp nhân nhất" — câu hỏi duy nhất ở màn này mà ô tìm
    //  kiếm và dải thẻ đếm đều không trả lời được.
    name: 'company_count',
    label: 'Số công ty phụ trách',
    type: 'number',
    operators: ['is', 'is_not', 'gt', 'gte', 'lt', 'lte'],
  },
]
