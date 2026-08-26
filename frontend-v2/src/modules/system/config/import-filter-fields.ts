import type { FilterFieldDefinition } from '@/shared/conditional-filter'

/**
 * Trường của BỘ LỌC NÂNG CAO («Bộ lọc») màn Quản lý nhập dữ liệu.
 *
 * ⚠️ `name` phải nằm trong `import_tool/service._FILTER_OPS` — ngoài whitelist đó
 * backend im lặng bỏ qua, giao diện trông như bộ lọc hỏng.
 *
 * Ở đây CHỈ khai các cột SỐ LƯỢNG (kết quả xử lý) — thứ không có ô chọn nhanh
 * trên thanh công cụ. Những cột đã có ô chọn riêng (phân hệ · trạng thái · chế
 * độ · người nhập · tên file · thời gian) thì không khai lại để tránh hai chỗ
 * đặt cùng một điều kiện.
 */
export const IMPORT_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'total_rows', label: 'Tổng dòng', type: 'number' },
  { name: 'created_count', label: 'Số tạo', type: 'number' },
  { name: 'updated_count', label: 'Số cập nhật', type: 'number' },
  { name: 'skipped_count', label: 'Số bỏ qua', type: 'number' },
  { name: 'warning_count', label: 'Số cảnh báo', type: 'number' },
  { name: 'review_count', label: 'Số rà soát', type: 'number' },
  { name: 'error_count', label: 'Số lỗi', type: 'number' },
]
