import type { FilterFieldDefinition } from '@/shared/conditional-filter'

/**
 * Trường của BỘ LỌC NÂNG CAO trên hộp duyệt văn bản («Chờ tôi duyệt»).
 *
 * ⚠️ Lọc chạy NGAY TẠI TRÌNH DUYỆT (`applyClientFilter`), không gửi query param:
 * bảng này gộp hai nguồn (hộp việc đang chờ + dấu vết đã bấm) rồi mới dựng dòng,
 * nên không có một endpoint nào để cắm điều kiện vào. Đằng nào cả hai nguồn cũng
 * trả hết một lượt, không phân trang.
 *
 * Vì thế `name` phải trùng **tên trường của `InboxRow`** (camelCase, xem
 * `components/approval-inbox-row.ts`), KHÔNG phải tên cột của backend.
 */
export const APPROVAL_INBOX_FILTER_FIELDS: FilterFieldDefinition[] = [
  {
    name: 'kind',
    label: 'Tình trạng',
    type: 'select',
    options: [
      { value: 'pending', label: 'Cần tôi duyệt' },
      { value: 'done', label: 'Tôi đã duyệt' },
    ],
  },
  { name: 'code', label: 'Số hiệu', type: 'text' },
  { name: 'title', label: 'Tên văn bản', type: 'text' },
  { name: 'nodeName', label: 'Bước', type: 'text' },
  { name: 'startedByName', label: 'Người trình', type: 'text' },
  { name: 'isOverdue', label: 'Quá hạn duyệt', type: 'boolean' },
  { name: 'dueAt', label: 'Hạn duyệt', type: 'date' },
  { name: 'decidedAt', label: 'Tôi bấm lúc', type: 'datetime' },
  //  Nhãn do backend cấp ("Duyệt" / "Trả lại" / "Từ chối") nên để kiểu CHỮ chứ
  //  không dựng sẵn danh sách chọn: thêm một hành động ở backend mà quên sửa
  //  chỗ này thì ô chọn thiếu mục, còn ô chữ thì vẫn tìm được.
  { name: 'actionLabel', label: 'Tôi đã bấm', type: 'text' },
  { name: 'instanceStatusLabel', label: 'Phiếu bây giờ', type: 'text' },
  { name: 'comment', label: 'Ý kiến', type: 'text' },
  { name: 'onBehalfOfName', label: 'Bấm thay', type: 'text' },
]
