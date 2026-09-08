import type { FilterFieldDefinition } from '@/shared/conditional-filter'

/**
 * Trường của BỘ LỌC NÂNG CAO trên màn *Đơn nghỉ phép*.
 *
 * Hai bộ chứ không một, vì ba tab của màn này lấy dữ liệu bằng hai đường khác
 * hẳn nhau — và bộ lọc phải chạy đúng đường ấy:
 *
 * | Tab | Dữ liệu | Lọc ở đâu |
 * |---|---|---|
 * | Cần tôi duyệt · Tôi đã duyệt | hộp việc, nạp TRỌN một lượt, không phân trang | trình duyệt (`applyClientFilter`) |
 * | Đơn của tôi | `/api/leave-requests` CÓ phân trang | backend (`useFilterQuery` → query param) |
 *
 * ⚠️ Đừng gộp làm một. Lọc ở client trên dữ liệu đã phân trang thì chỉ lọc được
 * đúng trang đang mở — gõ một cái tên rồi kết luận "không có đơn nào" trong khi
 * người đó nằm ở trang ba.
 */

/**
 * Tab hộp việc — lọc NGAY TẠI TRÌNH DUYỆT, nên `name` là tên trường của
 * `LeaveInboxRow` chứ không phải tên cột backend.
 *
 * Vì thế ở đây hỏi **tên** người nghỉ / **tên** loại nghỉ (`employee_name`,
 * `leave_type_name`): người dùng gõ chữ, và hai trường đó có sẵn trong dòng.
 * Bộ server bên dưới thì ngược lại — backend chỉ lọc được theo id.
 *
 * ⚠️ KHÔNG khai trường nào nằm trong `row.task` (hạn xử lý, quá hạn, chặng đang
 * chờ): `applyClientFilter` đọc `item[name]` một cấp, khai `task.due_at` là điều
 * kiện không đánh giá được — mà gặp thế nó LOẠI dòng đó, tức bảng trống trơn
 * chứ không phải bỏ qua điều kiện.
 */
export const LEAVE_INBOX_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Số đơn', type: 'text' },
  { name: 'employee_name', label: 'Người nghỉ', type: 'text' },
  { name: 'leave_type_name', label: 'Loại nghỉ', type: 'text' },
  { name: 'from_date', label: 'Từ ngày', type: 'date' },
  { name: 'to_date', label: 'Đến ngày', type: 'date' },
  { name: 'total_days', label: 'Số ngày', type: 'number' },
  { name: 'reason', label: 'Lý do', type: 'text' },
]

/**
 * Tab «Đơn của tôi» — lọc ở BACKEND, nên mọi `name` phải là **cột thật** và phải
 * nằm trong `request_service.FILTER_OPERATORS`; thiếu một cái là backend **bỏ
 * qua im lặng** điều kiện đó, người dùng bấm Áp dụng mà danh sách không đổi.
 *
 * KHÔNG khai lại *Loại nghỉ* và *Trạng thái*: hai ô đó đã đứng sẵn trên thanh
 * công cụ dạng ô chọn một-chạm. Bày lại trong bộ lọc nâng cao là hai đường sửa
 * cùng một tham số, và người dùng lọc ở đường này rồi ngồi nhìn ô kia không đổi
 * theo.
 */
export const LEAVE_REQUEST_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Số đơn', type: 'text' },
  { name: 'from_date', label: 'Từ ngày', type: 'date' },
  { name: 'to_date', label: 'Đến ngày', type: 'date' },
  { name: 'total_days', label: 'Số ngày', type: 'number' },
  { name: 'reason', label: 'Lý do', type: 'text' },
]
