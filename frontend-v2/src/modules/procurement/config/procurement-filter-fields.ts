import type { FilterFieldDefinition, OperatorType } from '@/shared/conditional-filter'
import {
  PO_DELIVERY_STATUS,
  PO_DOCUMENT_STATUS,
  PO_PROGRESS_STATUS,
} from '@/shared/constants/statuses'
import {
  PO_STATUS_LABELS,
  PR_STATUS_LABELS,
  SR_STATUS_LABELS,
  SURVEY_STATUS_LABELS,
  SURVEY_TYPE_LABELS,
  statusOptions,
} from '../types/purchase-document'
import {
  fetchCompanyOptions,
  fetchDepartmentOptions,
  fetchEmployeeOptions,
  fetchItemGroupOptions,
  fetchSupplierCodeOptions,
  fetchWarehouseCodeOptions,
} from './ref-filter-options'

/**
 * Trường của BỘ LỌC NÂNG CAO cho các bảng chứng từ mua hàng.
 */

const STATUS_OPERATORS = ['is', 'is_not', 'in', 'not_in'] as const

/** Ô tham chiếu chỉ để `bằng` / `khác`. */
const REF_OPERATORS: OperatorType[] = ['is', 'is_not']

const COMPANY_FIELD: FilterFieldDefinition = {
  name: 'company_id',
  label: 'Công ty',
  type: 'combobox',
  operators: REF_OPERATORS,
  fetchOptions: fetchCompanyOptions,
}

/** Ô phòng ban dùng chung — mỗi màn chỉ khác cái nhãn ("Bộ phận" / "Bộ phận yêu cầu"). */
const DEPARTMENT_FIELD: Omit<FilterFieldDefinition, 'label'> = {
  name: 'department_id',
  type: 'combobox',
  operators: REF_OPERATORS,
  fetchOptions: fetchDepartmentOptions,
}

/** Ô nhân sự dùng chung — `name` khác nhau theo vai trò (người yêu cầu / NSPT). */
const EMPLOYEE_FIELD: Omit<FilterFieldDefinition, 'label' | 'name'> = {
  type: 'combobox',
  operators: REF_OPERATORS,
  fetchOptions: fetchEmployeeOptions,
}

export const PURCHASE_REQUEST_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã PYC', type: 'text' },
  COMPANY_FIELD,
  { ...EMPLOYEE_FIELD, name: 'requester_id', label: 'Người yêu cầu' },
  { ...DEPARTMENT_FIELD, label: 'Bộ phận yêu cầu' },
  { name: 'purpose', label: 'Mục đích', type: 'text' },
  // bao-CR-316: hai mốc ngày RIÊNG — `request_date` là ngày LẬP phiếu, `received_date` là ngày
  // thu mua TIẾP NHẬN (rỗng = chưa tiếp nhận). Trước CR này chỉ có một ô và nó lọc lẫn lộn
  // cả hai loại ngày, vì `dispatch_pr` ghi đè `request_date` lúc điều phối.
  { name: 'request_date', label: 'Ngày lập phiếu', type: 'date' },
  { name: 'received_date', label: 'Ngày tiếp nhận', type: 'date' },
  { name: 'need_date', label: 'Ngày cần hàng', type: 'date' },
  { name: 'is_urgent', label: 'Đơn gấp', type: 'boolean', operators: ['is'] },
  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: statusOptions(PR_STATUS_LABELS),
  },
]

export const SURVEY_REQUEST_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã phiếu', type: 'text' },
  COMPANY_FIELD,
  { ...EMPLOYEE_FIELD, name: 'requester_id', label: 'Người yêu cầu' },
  { ...DEPARTMENT_FIELD, label: 'Bộ phận yêu cầu' },
  { name: 'purpose', label: 'Mục đích', type: 'text' },
  { name: 'request_date', label: 'Ngày tạo', type: 'date' },
  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: statusOptions(SR_STATUS_LABELS),
  },
]

export const PURCHASE_ORDER_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã ĐMH', type: 'text' },
  { name: 'misa_code', label: 'Mã MISA', type: 'text' },
  { name: 'pr_code', label: 'Mã PYC', type: 'text' },
  COMPANY_FIELD,
  { name: 'supplier_code', label: 'Mã nhà cung cấp', type: 'text' },
  { ...EMPLOYEE_FIELD, name: 'nspt_id', label: 'NSPT phụ trách' },
  { ...DEPARTMENT_FIELD, label: 'Bộ phận' },
  { name: 'order_date', label: 'Ngày đặt', type: 'date' },
  { name: 'is_urgent', label: 'Đơn gấp', type: 'boolean', operators: ['is'] },
  {
    name: 'document_status',
    label: 'Hồ sơ chứng từ',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: PO_DOCUMENT_STATUS.map(({ value, label }) => ({ value, label })),
  },
  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: statusOptions(PO_STATUS_LABELS),
  },
]

/**
 * Tiến độ mua hàng (`/api/purchase-progress`) — bao-CR-442.
 *
 * Một HÀNG ở màn này là ĐƠN + DÒNG HÀNG + LẦN GIAO ghép lại, nên danh sách trường
 * cũng chia ba cụm theo đúng thứ tự đó. Khóa phải nằm trong `_cond_map()` của
 * `backend/app/modules/purchase_progress/controller.py`, mà map đó lấy thẳng từ
 * `_sort_map()` — cột nào sắp xếp được tại server thì lọc được.
 *
 * ⚠️ **`company_id` cố ý KHÔNG có ở đây**: thanh lọc nhanh đã có ô Công ty chọn theo
 * tên, còn gõ số id vào bộ lọc điều kiện thì chẳng ai dùng. Backend cũng loại nó
 * khỏi map vì lý do này.
 *
 * ⚠️ Thiếu `supplier.read` thì backend **gỡ** cụm NCC/vận chuyển khỏi map — lọc rồi
 * đếm số dòng còn lại là mò ra được tên NCC. Nên `showSupplier` phải cắt đúng cụm
 * đó ở đây, kẻo người dùng dựng điều kiện xong mà backend im lặng bỏ qua.
 */
export const PURCHASE_PROGRESS_FILTER_FIELDS = (
  showSupplier: boolean,
): FilterFieldDefinition[] => [
  // ----- Đơn mua hàng -----
  { name: 'po_code', label: 'Mã ĐMH', type: 'text' },
  { name: 'misa_code', label: 'Mã MISA', type: 'text' },
  { name: 'pr_code', label: 'Mã PYC', type: 'text' },
  { ...DEPARTMENT_FIELD, label: 'Bộ phận' },
  { ...EMPLOYEE_FIELD, name: 'nspt_id', label: 'NSPT phụ trách' },
  { name: 'order_date', label: 'Ngày đặt hàng', type: 'date' },
  {
    name: 'document_status',
    label: 'Hồ sơ chứng từ',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: PO_DOCUMENT_STATUS.map(({ value, label }) => ({ value, label })),
  },
  ...(showSupplier
    ? ([
        {
          name: 'supplier_code',
          label: 'Mã NCC',
          type: 'combobox',
          operators: REF_OPERATORS,
          fetchOptions: fetchSupplierCodeOptions,
        },
        { name: 'supplier_name', label: 'Tên nhà cung cấp', type: 'text' },
      ] as FilterFieldDefinition[])
    : []),
  // ----- Dòng hàng -----
  { name: 'product_code', label: 'Mã SP', type: 'text' },
  { name: 'product_name', label: 'Tên SP', type: 'text' },
  { name: 'invoice_name', label: 'Tên hóa đơn', type: 'text' },
  {
    name: 'item_group',
    label: 'Nhóm hàng',
    type: 'combobox',
    operators: REF_OPERATORS,
    fetchOptions: fetchItemGroupOptions,
  },
  { name: 'spec', label: 'Quy cách', type: 'text' },
  { name: 'fg_code', label: 'Mã HH', type: 'text' },
  { name: 'unit', label: 'ĐVT', type: 'text' },
  { name: 'required_date', label: 'Ngày cần', type: 'date' },
  { name: 'expected_date', label: 'Dự kiến nhận', type: 'date' },
  { name: 'qty_request', label: 'SL yêu cầu', type: 'number' },
  { name: 'qty_order', label: 'SL đặt', type: 'number' },
  { name: 'price', label: 'Đơn giá', type: 'number' },
  { name: 'vat', label: 'VAT %', type: 'number' },
  // bao-CR-439: cột thành tiền đã quy đổi hết về đồng nên giữa bảng không còn cách nào
  // nhìn ra dòng ngoại tệ — mà đó lại là cụm hay phải kiểm lại nhất.
  { name: 'currency', label: 'Đồng tiền', type: 'text' },
  { name: 'exchange_rate', label: 'Tỷ giá', type: 'number' },
  {
    name: 'progress_status',
    label: 'Tiến độ dòng',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: PO_PROGRESS_STATUS.map(({ value, label }) => ({ value, label })),
  },
  { name: 'document_delivery_date', label: 'Ngày giao chứng từ cho KT', type: 'date' },
  // ----- Lần giao -----
  { name: 'delivery_no', label: 'Lần giao', type: 'number' },
  {
    name: 'warehouse_code',
    label: 'Kho',
    type: 'combobox',
    operators: REF_OPERATORS,
    fetchOptions: fetchWarehouseCodeOptions,
  },
  { name: 'ship_qty', label: 'SL giao', type: 'number' },
  { name: 'received_qty', label: 'SL nhận', type: 'number' },
  { name: 'promised_date', label: 'Cam kết giao', type: 'date' },
  { name: 'received_date', label: 'Ngày nhận', type: 'date' },
  { name: 'regulated_date', label: 'Ngày quy định', type: 'date' },
  { name: 'std_days', label: 'Ngày QĐ (số ngày)', type: 'number' },
  { name: 'diff_promise', label: 'CL cam kết', type: 'number' },
  { name: 'diff_regulated', label: 'CL quy định', type: 'number' },
  { name: 'diff_required', label: 'CL vs yêu cầu', type: 'number' },
  { name: 'delivery_invoice_no', label: 'Số hóa đơn', type: 'text' },
  { name: 'delivery_invoice_date', label: 'Ngày hóa đơn', type: 'date' },
  { name: 'qc_result', label: 'Kết quả QC', type: 'text' },
  // B-06: cột lưu MÃ nên ô CHỮ vô dụng (gõ "Đã nhận" không khớp `received`).
  {
    name: 'delivery_status',
    label: 'Trạng thái giao',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: PO_DELIVERY_STATUS.map(({ value, label }) => ({ value, label })),
  },
  ...(showSupplier
    ? ([
        {
          name: 'carrier_code',
          label: 'Mã ĐVVC',
          type: 'combobox',
          operators: REF_OPERATORS,
          fetchOptions: fetchSupplierCodeOptions,
        },
        { name: 'carrier_name', label: 'Đơn vị vận chuyển', type: 'text' },
        { name: 'shipping_unit_price', label: 'Đơn giá VC', type: 'number' },
        { name: 'shipping_amount', label: 'Tiền VC', type: 'number' },
      ] as FilterFieldDefinition[])
    : []),
]

export const SURVEY_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã phiếu khảo sát', type: 'text' },
  {
    name: 'survey_type',
    label: 'Loại khảo sát',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: Object.entries(SURVEY_TYPE_LABELS).map(([k, v]) => ({ value: k, label: v })),
  },
  { name: 'sr_code', label: 'Mã YCBG', type: 'text' },
  { name: 'pr_code', label: 'Mã PYC', type: 'text' },
  { name: 'main_content', label: 'Nội dung chính', type: 'text' },
  { name: 'item_code', label: 'Mã hàng', type: 'text' },
  { name: 'item_group', label: 'Nhóm hàng', type: 'text' },
  { name: 'nspt', label: 'NSPT', type: 'text' },
  {
    name: 'status',
    label: 'Trạng thái',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: statusOptions(SURVEY_STATUS_LABELS),
  },
]

export const SURVEY_PROGRESS_FILTER_FIELDS: FilterFieldDefinition[] = [
  { name: 'code', label: 'Mã YCBG', type: 'text' },
  { name: 'purpose', label: 'Mục đích', type: 'text' },
  COMPANY_FIELD,
  { ...EMPLOYEE_FIELD, name: 'requester_id', label: 'Người yêu cầu' },
  { ...DEPARTMENT_FIELD, label: 'Bộ phận' },
  { name: 'request_date', label: 'Ngày yêu cầu', type: 'date' },
  {
    name: 'status',
    label: 'Trạng thái phiếu',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: statusOptions(SR_STATUS_LABELS),
  },
  { name: 'item_group', label: 'Phân loại', type: 'text' },
  { ...EMPLOYEE_FIELD, name: 'assignee', label: 'NSTM phụ trách' },
  { name: 'request_qty', label: 'SL dự kiến', type: 'number' },
  { name: 'uom', label: 'ĐVT', type: 'text' },
  { name: 'proposed_price', label: 'Giá đề xuất', type: 'number' },
  { name: 'received_date', label: 'Ngày tiếp nhận', type: 'date' },
  { name: 'result_due_date', label: 'Hạn trả kết quả', type: 'date' },
  { name: 'result_date', label: 'Ngày trả kết quả', type: 'date' },
  {
    name: 'line_status',
    label: 'Trạng thái dòng',
    type: 'select',
    operators: [...STATUS_OPERATORS],
    options: [
      { value: 'resurvey', label: 'Cần khảo sát lại' },
      { value: 'completed', label: 'Hoàn thành' },
    ],
  },
]
