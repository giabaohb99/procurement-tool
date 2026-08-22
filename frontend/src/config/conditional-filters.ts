import type { FilterFieldDefinition, OperatorType } from '../components/conditional-filter'
import {
  PAYABLE_STATUSES, PO_DELIVERY_STATUSES, PO_DOCUMENT_STATUSES, PO_PROGRESS_STATUSES,
} from '../utils/statusLabels'

// Khai báo BỘ LỌC ĐIỀU KIỆN dùng chung.
//
// Màn cấu hình sẵn (CrudList) khai báo trong `cruds.tsx` qua `condFilters`; màn tự viết
// (Công nợ, Tồn kho…) lấy hằng số ở cuối file này.
//
// LUẬT: `name` PHẢI nằm trong whitelist FILTERABLE của controller tương ứng, nếu không backend
// sẽ bỏ qua điều kiện đó (xem backend/app/core/filter_operators.py).

type Opt = { value: string; label: string }

export const condText = (name: string, label: string): FilterFieldDefinition =>
  ({ name, label, type: 'text' })

export const condDate = (name: string, label: string): FilterFieldDefinition =>
  ({ name, label, type: 'date' })

/** Cột select: mặc định chỉ cho bằng/khác/thuộc danh sách — bỏ các phép so sánh lớn/nhỏ vô nghĩa */
export const condSelect = (name: string, label: string, options: Opt[],
                           operators: OperatorType[] = ['eq', 'ne', 'in', 'not_in']): FilterFieldDefinition =>
  ({ name, label, type: 'select', options, operators })

export const condNumber = (name: string, label: string): FilterFieldDefinition =>
  ({ name, label, type: 'number' })

/** Như condSelect nhưng options nạp động từ API (NCC, phòng ban, phân loại…) */
export const condSource = (name: string, label: string,
                           source: { url: string; value?: string; label?: string },
                           operators: OperatorType[] = ['eq', 'ne', 'in', 'not_in']): FilterFieldDefinition =>
  ({ name, label, type: 'select', source, operators })

// ── Màn tự viết ───────────────────────────────────────────────────────────────

/** Công nợ (/api/payables) — theo payable/service.py FILTERABLE.
 *  Tuổi nợ / năm / khoảng ngày / khoảng tiền là tham số tính toán riêng của endpoint,
 *  không phải cột bảng nên vẫn nằm ở thanh lọc cơ bản. */
export const PAYABLE_COND_FILTERS: FilterFieldDefinition[] = [
  condSource('supplier_code', 'Nhà cung cấp', { url: '/api/suppliers', value: 'code', label: 'name' }),
  condText('po_code', 'Mã PO'),
  condText('invoice_no', 'Số hóa đơn'),
  condSelect('source_type', 'Loại nợ', [
    { value: 'goods', label: 'Hàng hóa' }, { value: 'shipping', label: 'Vận chuyển' }]),
  // Giá trị gửi lên là MÃ (`unpaid | partial | paid`) từ B-05, không phải nhãn tiếng Việt.
  condSelect('status', 'Trạng thái', PAYABLE_STATUSES),
]

/** Công nợ trong tab NCC — như trên nhưng BỎ cột "Nhà cung cấp" vì màn đã khóa theo 1 NCC. */
export const SUPPLIER_PAYABLE_COND_FILTERS: FilterFieldDefinition[] =
  PAYABLE_COND_FILTERS.filter((f) => f.name !== 'supplier_code')

/** Tồn kho (/api/inventory) — theo inventory/service.py FILTERABLE */
export const INVENTORY_COND_FILTERS: FilterFieldDefinition[] = [
  condSource('warehouse_code', 'Kho', { url: '/api/warehouses', value: 'code', label: 'name' }),
  condText('product_code', 'Mã sản phẩm'),
  condText('product_name', 'Tên sản phẩm'),
]

// ── Hai màn TIẾN ĐỘ (CR-080) ──────────────────────────────────────────────────
//
// Hai bảng này rộng 40+ cột nên thanh lọc cố định chỉ giữ mấy ô cơ bản (Công ty · Tìm kiếm ·
// tiến độ · trạng thái nhận/trễ hạn); mọi cột còn lại lọc ở đây, có đủ phép so sánh.
//
// Là HÀM chứ không phải hằng số vì cụm NCC/vận chuyển chỉ được lọc khi người dùng có
// `supplier.read` — backend cũng gỡ cột đó khỏi whitelist (xem `_cond_map` của hai controller),
// nên khai báo thêm cũng vô ích mà còn khiến người dùng tưởng lọc được.

// CR-088: ô tham chiếu (phòng ban / nhân sự) lọc theo ID, không lọc theo tên nữa. Lọc theo tên
// vỡ ở ba chỗ, cả ba đều gặp thật: phòng đổi tên -> bộ lọc trượt sạch; hai người trùng tên ->
// lọc một người ra đơn của cả hai; `contains` khớp chuỗi con -> lọc "Hân" ra "Ngọc Hân".
export const DEPT_SRC = { url: '/api/departments', value: 'id', label: 'name' }
export const EMP_SRC = { url: '/api/employees', value: 'id', label: 'full_name' }
const GROUP_SRC = { url: '/api/item-groups', value: 'name', label: 'name' }

/** Tiến độ mua hàng (/api/purchase-progress) — theo `purchase_progress/controller._cond_map` */
export const purchaseProgressCondFilters = (showSupplier: boolean): FilterFieldDefinition[] => [
  // Đơn mua hàng
  condText('po_code', 'Mã ĐMH'), condText('misa_code', 'Mã MISA'), condText('pr_code', 'Mã PYC'),
  condSource('department_id', 'Bộ phận', DEPT_SRC),
  condSource('nspt_id', 'NSPT phụ trách', EMP_SRC),
  condDate('order_date', 'Ngày đặt hàng'),
  condSelect('document_status', 'Hồ sơ chứng từ', PO_DOCUMENT_STATUSES),
  ...(showSupplier ? [
    condSource('supplier_code', 'Mã NCC', { url: '/api/suppliers', value: 'code', label: 'name' }),
    condText('supplier_name', 'Tên nhà cung cấp'),
  ] : []),
  // Dòng hàng
  condText('product_code', 'Mã SP'), condText('product_name', 'Tên SP'),
  condText('invoice_name', 'Tên hóa đơn'), condSource('item_group', 'Nhóm hàng', GROUP_SRC),
  condText('spec', 'Quy cách'), condText('fg_code', 'Mã HH'), condText('unit', 'ĐVT'),
  condDate('required_date', 'Ngày cần'), condDate('expected_date', 'Dự kiến nhận'),
  condNumber('qty_request', 'SL yêu cầu'), condNumber('qty_order', 'SL đặt'),
  condNumber('price', 'Đơn giá'), condNumber('vat', 'VAT %'),
  condSelect('progress_status', 'Tiến độ dòng', PO_PROGRESS_STATUSES),
  // Lần giao
  condNumber('delivery_no', 'Lần giao'),
  condSource('warehouse_code', 'Kho', { url: '/api/warehouses', value: 'code', label: 'name' }),
  condNumber('ship_qty', 'SL giao'), condNumber('received_qty', 'SL nhận'),
  condDate('promised_date', 'Cam kết giao'), condDate('received_date', 'Ngày nhận'),
  condDate('regulated_date', 'Ngày quy định'), condNumber('std_days', 'Ngày QĐ (số ngày)'),
  condNumber('diff_promise', 'CL cam kết'), condNumber('diff_regulated', 'CL quy định'),
  condNumber('diff_required', 'CL vs yêu cầu'),
  condText('delivery_invoice_no', 'Số hóa đơn'), condText('qc_result', 'Kết quả QC'),
  // B-06: cột lưu MÃ nên ô CHỮ hết dùng được (gõ "Đã nhận" không khớp `received`) — đổi hẳn
  // sang ô CHỌN, người dùng cũng bớt phải nhớ dấu tiếng Việt.
  condSelect('delivery_status', 'Trạng thái giao', PO_DELIVERY_STATUSES),
  ...(showSupplier ? [
    condSource('carrier_code', 'Mã ĐVVC', { url: '/api/suppliers', value: 'code', label: 'name' }),
    condText('carrier_name', 'Đơn vị vận chuyển'),
    condNumber('shipping_unit_price', 'Đơn giá VC'), condNumber('shipping_amount', 'Tiền VC'),
  ] : []),
]

/** Tiến độ báo giá (/api/survey-progress) — theo `survey_progress/controller._cond_map`.
 *  Cột TÍNH (trễ hạn, số ngày xử lý, tiến độ dòng) không lọc được ở đây vì không nằm trong DB:
 *  tiến độ dòng có ô riêng trên thanh lọc, "chưa trả kết quả" thì dùng `Ngày trả KQ` + đang trống. */
export const surveyProgressCondFilters = (showSupplier: boolean): FilterFieldDefinition[] => [
  // Đầu phiếu
  condText('code', 'Mã YCBG'), condText('purpose', 'Mục đích'),
  condSource('requester_id', 'Người yêu cầu', EMP_SRC),
  condSource('department_id', 'Bộ phận', DEPT_SRC),
  condDate('request_date', 'Ngày yêu cầu'),
  condSelect('status', 'Trạng thái phiếu', [
    { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
    { value: 'approved', label: 'Đã duyệt' }, { value: 'rejected', label: 'Từ chối' },
    { value: 'processing', label: 'Đang xử lý' }, { value: 'survey_done', label: 'Đã khảo sát' },
    { value: 'pr_created', label: 'Đã tạo YCMH' }, { value: 'done', label: 'Hoàn thành' }]),
  // Dòng yêu cầu
  condSource('item_group', 'Phân loại', GROUP_SRC),
  condSource('assignee', 'NSTM phụ trách', { url: '/api/employees', value: 'code', label: 'full_name' }),
  condNumber('request_qty', 'SL dự kiến'), condText('uom', 'ĐVT'),
  condNumber('proposed_price', 'Giá đề xuất'),
  // Mốc tiến độ
  condDate('received_date', 'Ngày tiếp nhận'), condDate('result_due_date', 'Hạn trả kết quả'),
  condDate('result_date', 'Ngày trả kết quả'),
  condSelect('line_status', 'Trạng thái dòng', [
    { value: 'resurvey', label: 'Cần khảo sát lại' },
    { value: 'completed', label: 'Hoàn thành' }]),
  ...(showSupplier ? [condText('internal_line_code', 'Mã dòng nội bộ')] : []),
]

/** Phân công phụ trách (/api/category-assignees) — lọc theo KHÓA vì tên phân loại / tên NSTM
 *  là cột join, không lọc trực tiếp trên bảng gốc được. */
export const CATEGORY_ASSIGNEE_COND_FILTERS: FilterFieldDefinition[] = [
  condSource('item_group_id', 'Phân loại', { url: '/api/item-groups', value: 'id', label: 'name' }),
  condSource('primary_employee_id', 'NSTM chính', { url: '/api/employees', value: 'id', label: 'full_name' }),
  condSource('backup_employee_id', 'NSTM dự phòng', { url: '/api/employees', value: 'id', label: 'full_name' }),
]
