import { FilterField } from '../components/FilterBar'

export type FieldDef = {
  key: string
  label: string
  type?: 'text' | 'number' | 'textarea' | 'select' | 'checkbox'
  options?: { value: string; label: string }[]
  readonlyOnEdit?: boolean
}
export type Column = { key: string; label: string; render?: (row: any) => any }

export type CrudConfig = {
  slug: string
  entity: string
  title: string
  apiPath: string
  columns: Column[]
  fields: FieldDef[]
  filters: FilterField[]
  importExport?: boolean
}

const badge = (v: any, on = 'Đang dùng', off = 'Ngừng') =>
  <span className={'badge ' + (v ? 'ok' : 'err')}>{v ? on : off}</span>

const SUP_TYPE = [
  { value: 'goods', label: 'NCC bán hàng' },
  { value: 'transport', label: 'Đơn vị vận chuyển' },
]

export const PR_STATUS: Record<string, { label: string; cls: string }> = {
  draft: { label: 'Nháp', cls: 'gray' },
  submitted: { label: 'Chờ duyệt', cls: 'warn' },
  approved: { label: 'Đã duyệt', cls: 'ok' },
  rejected: { label: 'Từ chối', cls: 'err' },
}
export const prBadge = (st: string) => {
  const s = PR_STATUS[st] || { label: st, cls: 'gray' }
  return <span className={'badge ' + s.cls}>{s.label}</span>
}

export const cruds: Record<string, CrudConfig> = {
  companies: {
    slug: 'companies', entity: 'company', title: 'Công ty (pháp nhân)', apiPath: '/api/companies', importExport: true,
    columns: [
      { key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên' }, { key: 'tax_code', label: 'MST' },
      { key: 'invoice_email', label: 'Email hóa đơn' },
      { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active) },
    ],
    filters: [{ key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên' }, { key: 'tax_code', label: 'MST' }],
    fields: [
      { key: 'code', label: 'Mã', readonlyOnEdit: true }, { key: 'name', label: 'Tên pháp nhân' },
      { key: 'tax_code', label: 'MST' }, { key: 'address', label: 'Địa chỉ', type: 'textarea' },
      { key: 'invoice_email', label: 'Email nhận hóa đơn' },
      { key: 'parent', label: 'Thuộc công ty (ID cha, 0 = gốc)', type: 'number' },
      { key: 'is_active', label: 'Đang dùng', type: 'checkbox' },
    ],
  },
  suppliers: {
    slug: 'suppliers', entity: 'supplier', title: 'Nhà cung cấp', apiPath: '/api/suppliers', importExport: true,
    columns: [
      { key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên pháp lý' }, { key: 'tax_code', label: 'MST' },
      { key: 'supplier_type', label: 'Loại', render: (r) => (r.supplier_type === 'transport' ? 'Vận chuyển' : 'Bán hàng') },
      { key: 'payment_terms', label: 'Thanh toán' },
      { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active) },
    ],
    filters: [
      { key: 'code', label: 'Mã / viết tắt' }, { key: 'name', label: 'Tên NCC' }, { key: 'tax_code', label: 'MST' },
      { key: 'supplier_type', label: 'Loại', type: 'select', options: SUP_TYPE },
    ],
    fields: [
      { key: 'code', label: 'Mã / viết tắt', readonlyOnEdit: true }, { key: 'name', label: 'Tên pháp lý' },
      { key: 'tax_code', label: 'MST' }, { key: 'address', label: 'Địa chỉ', type: 'textarea' },
      { key: 'supplier_type', label: 'Loại', type: 'select', options: SUP_TYPE },
      { key: 'payment_terms', label: 'Hình thức thanh toán' }, { key: 'vat', label: 'VAT (vd 0.08)', type: 'number' },
      { key: 'is_active', label: 'Đang dùng', type: 'checkbox' },
    ],
  },
  products: {
    slug: 'products', entity: 'product', title: 'Sản phẩm / Hàng hóa', apiPath: '/api/products', importExport: true,
    columns: [
      { key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên' }, { key: 'item_group', label: 'Phân loại' },
      { key: 'unit', label: 'ĐVT' }, { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active) },
    ],
    filters: [
      { key: 'code', label: 'Mã VTBB/NL' }, { key: 'name', label: 'Tên' },
      { key: 'item_group', label: 'Phân loại' }, { key: 'unit', label: 'ĐVT' },
    ],
    fields: [
      { key: 'code', label: 'Mã VTBB/NL', readonlyOnEdit: true }, { key: 'name', label: 'Tên' },
      { key: 'invoice_name', label: 'Tên trên hóa đơn' }, { key: 'item_group', label: 'Phân loại' },
      { key: 'unit', label: 'ĐVT' }, { key: 'is_active', label: 'Đang dùng', type: 'checkbox' },
    ],
  },
  employees: {
    slug: 'employees', entity: 'employee', title: 'Nhân sự', apiPath: '/api/employees', importExport: true,
    columns: [
      { key: 'code', label: 'Mã NV' }, { key: 'full_name', label: 'Họ tên' }, { key: 'email', label: 'Email' },
      { key: 'position', label: 'Chức vụ' }, { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active, 'Đang làm', 'Nghỉ') },
    ],
    filters: [{ key: 'code', label: 'Mã NV' }, { key: 'full_name', label: 'Họ tên' }, { key: 'email', label: 'Email' }],
    fields: [
      { key: 'code', label: 'Mã NV', readonlyOnEdit: true }, { key: 'full_name', label: 'Họ tên' },
      { key: 'email', label: 'Email' }, { key: 'phone', label: 'Điện thoại' },
      { key: 'company_id', label: 'Công ty (ID)', type: 'number' }, { key: 'department_id', label: 'Phòng ban (ID)', type: 'number' },
      { key: 'position', label: 'Chức vụ' }, { key: 'is_active', label: 'Đang làm', type: 'checkbox' },
    ],
  },
  'purchase-requests': {
    slug: 'purchase-requests', entity: 'purchase_request', title: 'Yêu cầu mua (PYC)', apiPath: '/api/purchase-requests',
    columns: [
      { key: 'code', label: 'Mã PYC' },
      { key: 'request_date', label: 'Ngày tạo' },
      { key: 'requester', label: 'Người yêu cầu' },
      { key: 'department', label: 'Bộ phận' },
      { key: 'need_date', label: 'Cần hàng' },
      { key: 'total', label: 'Tổng tiền', render: (r) => (r.total ? Number(r.total).toLocaleString('vi-VN') + ' đ' : '0 đ') },
      { key: 'is_urgent', label: 'Gấp', render: (r) => (r.is_urgent ? <span className="badge warn">Gấp</span> : '—') },
      { key: 'status', label: 'Trạng thái', render: (r) => prBadge(r.status) },
    ],
    filters: [
      { key: 'code', label: 'Mã PYC' }, { key: 'requester', label: 'Người yêu cầu' },
      { key: 'status', label: 'Trạng thái', type: 'select', options: [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'rejected', label: 'Từ chối' },
      ] },
    ],
    fields: [],  // chi tiết dùng trang riêng (PurchaseRequestDetail)
  },
  warehouses: {
    slug: 'warehouses', entity: 'warehouse', title: 'Kho', apiPath: '/api/warehouses', importExport: true,
    columns: [
      { key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên kho' }, { key: 'address', label: 'Địa chỉ' },
      { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active) },
    ],
    filters: [{ key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên kho' }],
    fields: [
      { key: 'code', label: 'Mã', readonlyOnEdit: true }, { key: 'name', label: 'Tên kho' },
      { key: 'address', label: 'Địa chỉ', type: 'textarea' }, { key: 'is_active', label: 'Đang dùng', type: 'checkbox' },
    ],
  },
  units: {
    slug: 'units', entity: 'unit', title: 'Đơn vị tính', apiPath: '/api/units', importExport: true,
    columns: [
      { key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên ĐVT' },
      { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active) },
    ],
    filters: [{ key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên' }],
    fields: [
      { key: 'code', label: 'Mã', readonlyOnEdit: true }, { key: 'name', label: 'Tên ĐVT' },
      { key: 'is_active', label: 'Đang dùng', type: 'checkbox' },
    ],
  },
  'item-groups': {
    slug: 'item-groups', entity: 'item_group', title: 'Phân loại VTBB/NL', apiPath: '/api/item-groups', importExport: true,
    columns: [
      { key: 'name', label: 'Phân loại' }, { key: 'std_days', label: 'Số ngày quy định' },
      { key: 'apply_date', label: 'Ngày áp dụng' },
      { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active) },
    ],
    filters: [{ key: 'name', label: 'Phân loại' }],
    fields: [
      { key: 'name', label: 'Phân loại', readonlyOnEdit: true }, { key: 'std_days', label: 'Số ngày quy định' },
      { key: 'note', label: 'Ghi chú', type: 'textarea' }, { key: 'apply_date', label: 'Ngày áp dụng' },
      { key: 'is_active', label: 'Đang dùng', type: 'checkbox' },
    ],
  },
  brands: {
    slug: 'brands', entity: 'brand', title: 'Phòng ban', apiPath: '/api/brands', importExport: true,
    columns: [
      { key: 'code', label: 'Viết tắt' }, { key: 'department', label: 'Bộ phận đặt hàng' },
      { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active) },
    ],
    filters: [{ key: 'code', label: 'Viết tắt' }, { key: 'department', label: 'Bộ phận' }],
    fields: [
      { key: 'code', label: 'Viết tắt', readonlyOnEdit: true }, { key: 'department', label: 'Bộ phận đặt hàng' },
      { key: 'is_active', label: 'Đang dùng', type: 'checkbox' },
    ],
  },
  'surveys-supplier': {
    slug: 'surveys-supplier', entity: 'survey', title: 'Khảo sát Nhà cung cấp', apiPath: '/api/surveys-supplier',
    columns: [
      { key: 'code', label: 'Mã phiếu' }, { key: 'pr_code', label: 'Mã YC (PYC)' },
      { key: 'item_group', label: 'Nhóm hàng' }, { key: 'nspt', label: 'NSPT' },
      { key: 'status', label: 'Trạng thái', render: (r) => prBadge(r.status) },
    ],
    filters: [
      { key: 'code', label: 'Mã phiếu' }, { key: 'pr_code', label: 'Mã YC' }, { key: 'nspt', label: 'NSPT' },
      { key: 'status', label: 'Trạng thái', type: 'select', options: [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'rejected', label: 'Từ chối' }] },
    ],
    fields: [],
  },
  'surveys-product': {
    slug: 'surveys-product', entity: 'survey', title: 'Khảo sát Sản phẩm', apiPath: '/api/surveys-product',
    columns: [
      { key: 'code', label: 'Mã phiếu' }, { key: 'pr_code', label: 'Mã YC (PYC)' },
      { key: 'item_group', label: 'Nhóm hàng' }, { key: 'nspt', label: 'NSPT' },
      { key: 'status', label: 'Trạng thái', render: (r) => prBadge(r.status) },
    ],
    filters: [
      { key: 'code', label: 'Mã phiếu' }, { key: 'pr_code', label: 'Mã YC' }, { key: 'nspt', label: 'NSPT' },
      { key: 'status', label: 'Trạng thái', type: 'select', options: [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'rejected', label: 'Từ chối' }] },
    ],
    fields: [],
  },
}
