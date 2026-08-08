import type { FilterFieldDefinition, OperatorType } from '../components/conditional-filter'

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
  condSelect('status', 'Trạng thái', [
    { value: 'Chờ TT', label: 'Chờ thanh toán' },
    { value: 'Trả một phần', label: 'Thanh toán một phần' },
    { value: 'Đã TT', label: 'Đã thanh toán' }]),
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

/** Phân công phụ trách (/api/category-assignees) — lọc theo KHÓA vì tên phân loại / tên NSTM
 *  là cột join, không lọc trực tiếp trên bảng gốc được. */
export const CATEGORY_ASSIGNEE_COND_FILTERS: FilterFieldDefinition[] = [
  condSource('item_group_id', 'Phân loại', { url: '/api/item-groups', value: 'id', label: 'name' }),
  condSource('primary_employee_id', 'NSTM chính', { url: '/api/employees', value: 'id', label: 'full_name' }),
  condSource('backup_employee_id', 'NSTM dự phòng', { url: '/api/employees', value: 'id', label: 'full_name' }),
]
