import { FilterField } from '../components/FilterBar'
import type { FilterFieldDefinition } from '../components/conditional-filter'
import { condDate, condSelect, condSource, condText } from './conditional-filters'
import DepartmentMembers from '../components/DepartmentMembers'
import ProductImages from '../components/ProductImages'
import { fmtDateTime } from '../utils/datetime'

export type FieldDef = {
  key: string
  label: string
  type?: 'text' | 'number' | 'textarea' | 'select' | 'checkbox' | 'date' | 'select-multiple'
  options?: { value: string; label: string }[]
  readonlyOnEdit?: boolean
  source?: { url: string; value?: string; label?: string }
  onValueChange?: (val: any, form: any, setForm: (k: string, v: any) => void) => void
  colorMap?: Record<string, string>   // map giá trị option → màu chữ (vd trạng thái: true→xanh, false→đỏ)
  zeroAsBlank?: boolean   // ô số FK-sentinel: giá trị 0 hiện rỗng (để trống = 0), tránh hiện "0" mặc định
  default?: any           // giá trị mặc định khi TẠO MỚI (bản ghi mới)
  hint?: string           // dòng chú thích nhỏ dưới ô nhập (giải thích ý nghĩa field)
}
// link?: trả URL → cell thành clickable, điều hướng tới URL đó (chặn click lan ra dòng)
export type Column = { key: string; label: string; render?: (row: any) => any; link?: (row: any) => string }

export type CrudConfig = {
  slug: string
  entity: string
  title: string
  apiPath: string
  columns: Column[]
  fields: FieldDef[]
  filters: FilterField[]
  /** Bộ lọc ĐIỀU KIỆN (chứa / bằng / lớn hơn / trong khoảng… + VÀ/HOẶC) — không khai báo thì
   *  màn hình chỉ có thanh lọc cơ bản. `name` PHẢI nằm trong FILTERABLE của controller. */
  condFilters?: FilterFieldDefinition[]
  importExport?: boolean
  rowStyle?: (row: any) => any   // tô màu dòng theo điều kiện (vd HĐ sắp hết hạn)
  txn?: boolean                  // chứng từ giao dịch (PYC/PO/khảo sát/YCTT): ai có 'read' là xem danh sách được
  cloneable?: boolean            // hiện nút "Nhân bản" mỗi dòng → POST {apiPath}/{id}/clone tạo phiếu nháp mới
  detailExtra?: (row: any) => any  // section tùy biến render dưới form ở trang chi tiết (chỉ khi đã có bản ghi)
}

const badge = (v: any, on = 'Đang dùng', off = 'Ngừng') =>
  <span className={'badge ' + (v ? 'ok' : 'err')}>{v ? on : off}</span>

const SUP_TYPE = [
  { value: 'goods', label: 'NCC bán hàng' },
  { value: 'transport', label: 'Đơn vị vận chuyển' },
]

const EMPLOYEE_STATUS = [
  { value: 'Chính thức', label: 'Chính thức' },
  { value: 'Cộng tác viên', label: 'Cộng tác viên' },
  { value: 'Nghỉ thai sản', label: 'Nghỉ thai sản' },
  { value: 'Nghỉ việc', label: 'Nghỉ việc' },
]

const DEPT_ACTIVE = [{ value: 'true', label: 'Hoạt động' }, { value: 'false', label: 'Đã ẩn' }]

const ACTIVE_OPTIONS = [
  { value: 'true', label: 'Đang dùng / Hiện' },
  { value: 'false', label: 'Ngừng / Ẩn' },
]

export const PAYMENT_TERMS_OPTIONS = [
  { value: 'Công nợ 60 ngày', label: 'Công nợ 60 ngày' },
  { value: 'Thanh toán 100% khi nhận hàng', label: 'Thanh toán 100% khi nhận hàng' },
  { value: 'Công nợ 30 ngày', label: 'Công nợ 30 ngày' },
  { value: 'Thanh toán trước khi giao hàng', label: 'Thanh toán trước khi giao hàng' },
  { value: 'Thanh toán 7 ngày sau khi nhận hàng', label: 'Thanh toán 7 ngày sau khi nhận hàng' },
  { value: 'Công nợ 20 ngày', label: 'Công nợ 20 ngày' },
]

export const contractExpiryBadge = (e: string) => {
  if (!e) return '—'
  const c = e === 'Hết hạn' ? { bg: '#fee2e2', fg: '#b91c1c' } : e === 'Sắp hết hạn' ? { bg: '#fef3c7', fg: '#d97706' } : { bg: '#dcfce7', fg: '#15803d' }
  return <span className="badge" style={{ background: c.bg, color: c.fg }}>{e}</span>
}
// Tô cả dòng HĐ sắp/hết hạn (cảnh báo trực quan)
export const contractRowStyle = (r: any) => r.expiry === 'Hết hạn' ? { background: '#fdecea' } : r.expiry === 'Sắp hết hạn' ? { background: '#fff7ed' } : undefined
const CONTRACT_TYPES = [{ value: 'Mua bán', label: 'Mua bán' }, { value: 'Nguyên tắc', label: 'Nguyên tắc' }, { value: 'Vận chuyển', label: 'Vận chuyển' }]
const CONTRACT_STATUS = [{ value: 'Hiệu lực', label: 'Hiệu lực' }, { value: 'Hết hạn', label: 'Hết hạn' }, { value: 'Thanh lý', label: 'Thanh lý' }]

export const PR_STATUS: Record<string, { label: string; cls: string }> = {
  draft: { label: 'Nháp', cls: 'gray' },
  submitted: { label: 'Chờ duyệt', cls: 'warn' },
  approved: { label: 'Đã duyệt', cls: 'ok' },
  rejected: { label: 'Bị trả lại', cls: 'warn' },   // Trả về — sửa & gửi duyệt lại được
  processing: { label: 'Đang xử lý', cls: 'warn' },
  survey_done: { label: 'Đã khảo sát', cls: 'ok' },
  pr_created: { label: 'Đã tạo YCMH', cls: 'warn' },
  done: { label: 'Hoàn thành', cls: 'ok' },
  completed: { label: 'Hoàn thành', cls: 'ok' },
  cancelled: { label: 'Đã từ chối', cls: 'err' },   // Từ chối — khóa phiếu
}
export const prBadge = (st: string) => {
  const s = PR_STATUS[String(st || '').toLowerCase()] || { label: st, cls: 'gray' }
  return <span className={'badge ' + s.cls}>{s.label}</span>
}

// Yêu cầu khảo sát: 'rejected' = TRẢ ĐƠN (sửa lại được), 'cancelled' = TỪ CHỐI (khóa đơn)
export const SR_STATUS: Record<string, { label: string; cls: string }> = {
  draft: { label: 'Nháp', cls: 'gray' },
  submitted: { label: 'Chờ duyệt', cls: 'warn' },
  approved: { label: 'Đã duyệt', cls: 'ok' },
  rejected: { label: 'Bị trả lại', cls: 'warn' },
  cancelled: { label: 'Đã từ chối', cls: 'err' },
  processing: { label: 'Đang xử lý', cls: 'warn' },
  survey_done: { label: 'Đã khảo sát', cls: 'ok' },
  pr_created: { label: 'Đã tạo YCMH', cls: 'warn' },
  done: { label: 'Hoàn thành', cls: 'ok' },
}
export const srBadge = (st: string) => {
  const s = SR_STATUS[String(st || '').toLowerCase()] || { label: st, cls: 'gray' }
  return <span className={'badge ' + s.cls}>{s.label}</span>
}

export const PO_STATUS: Record<string, { label: string; cls: string }> = {
  draft: { label: 'Nháp', cls: 'gray' },
  submitted: { label: 'Chờ duyệt', cls: 'warn' },
  approved: { label: 'Đã duyệt', cls: 'ok' },
  partial: { label: 'Đã nhận một phần', cls: 'warn' },
  received: { label: 'Đã nhận đủ', cls: 'ok' },
  completed: { label: 'Hoàn thành', cls: 'ok' },
  rejected: { label: 'Bị trả lại', cls: 'warn' },
  cancelled: { label: 'Đã từ chối', cls: 'err' },
  processing: { label: 'Đang xử lý', cls: 'warn' },
}
export const poBadge = (st: string) => {
  const s = PO_STATUS[String(st || '').toLowerCase()] || { label: st, cls: 'gray' }
  return <span className={'badge ' + s.cls}>{s.label}</span>
}

// Hồ sơ chứng từ (Task 10b) — trạng thái cập nhật tay
const DOC_STATUS_BADGE: Record<string, string> = {
  'chưa có chứng từ': 'err',
  'đã có thông tin chứng từ': 'warn',
  'đã đủ chứng từ': 'ok',
}
// Nhãn hiển thị (giá trị lưu DB giữ nguyên "đã có thông tin chứng từ")
const DOC_STATUS_LABEL: Record<string, string> = {
  'chưa có chứng từ': 'Chưa có chứng từ',
  'đã có thông tin chứng từ': 'Đã có chứng từ',
  'đã đủ chứng từ': 'Đã đủ chứng từ',
}
export const docStatusBadge = (st: string) => {
  const v = String(st || 'chưa có chứng từ')
  return <span className={'badge ' + (DOC_STATUS_BADGE[v] || 'gray')}>{DOC_STATUS_LABEL[v] || v}</span>
}

export const cruds: Record<string, CrudConfig> = {
  companies: {
    slug: 'companies', entity: 'company', title: 'Công ty', apiPath: '/api/companies', importExport: true,
    columns: [
      { key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên' }, { key: 'tax_code', label: 'MST' },
      { key: 'legal_rep_name', label: 'Người đại diện' },
      { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active) },
    ],
    filters: [
      { key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên' }, { key: 'tax_code', label: 'MST' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
    ],
    condFilters: [
      condText('code', 'Mã'), condText('name', 'Tên'), condText('tax_code', 'MST'),
      condSelect('is_active', 'Trạng thái', ACTIVE_OPTIONS, ['eq']),
    ],
    fields: [
      { key: 'code', label: 'Mã', readonlyOnEdit: true }, { key: 'name', label: 'Tên pháp nhân' },
      { key: 'tax_code', label: 'MST' }, { key: 'address', label: 'Địa chỉ', type: 'textarea' },
      { key: 'invoice_email', label: 'Email nhận hóa đơn' },
      { key: 'parent', label: 'Thuộc công ty (ID cha, để trống = gốc)', type: 'number', zeroAsBlank: true },
      { key: 'legal_representative_id', label: 'Người đại diện pháp lý', type: 'select', source: { url: '/api/employees', value: 'id', label: 'full_name' } },
      { key: 'legal_rep_title', label: 'Chức danh' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
    ],
  },
  suppliers: {
    slug: 'suppliers', entity: 'supplier', title: 'Nhà cung cấp', apiPath: '/api/suppliers', importExport: true,
    columns: [
      { key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên pháp lý' },
      { key: 'legal_type', label: 'Loại NCC' }, { key: 'tax_code', label: 'MST' },
      { key: 'supplier_type', label: 'Vai trò', render: (r) => (r.supplier_type === 'transport' ? 'Vận chuyển' : 'Bán hàng') },
      { key: 'payment_terms', label: 'Thanh toán' },
      { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active) },
    ],
    filters: [
      { key: 'code', label: 'Mã / viết tắt' }, { key: 'name', label: 'Tên NCC' }, { key: 'tax_code', label: 'MST' },
      { key: 'legal_type', label: 'Loại NCC', type: 'select', options: ['Công ty', 'Cá nhân', 'Hợp danh', 'Hộ kinh doanh'].map((x) => ({ value: x, label: x })) },
      { key: 'supplier_type', label: 'Vai trò', type: 'select', options: SUP_TYPE },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
    ],
    // legal_type không nằm trong FILTERABLE của supplier nên không đưa vào đây
    condFilters: [
      condText('code', 'Mã / viết tắt'), condText('name', 'Tên NCC'), condText('tax_code', 'MST'),
      condSelect('supplier_type', 'Vai trò', SUP_TYPE),
      condSelect('is_active', 'Trạng thái', ACTIVE_OPTIONS, ['eq']),
    ],
    fields: [
      { key: 'code', label: 'Mã / viết tắt', readonlyOnEdit: true }, { key: 'name', label: 'Tên pháp lý' },
      { key: 'tax_code', label: 'MST' }, { key: 'address', label: 'Địa chỉ', type: 'textarea' },
      { key: 'supplier_type', label: 'Loại', type: 'select', options: SUP_TYPE },
      { key: 'payment_terms', label: 'Hình thức thanh toán', type: 'select', options: PAYMENT_TERMS_OPTIONS }, { key: 'vat', label: 'VAT (vd 0.08)', type: 'number' },
      { key: 'is_active', label: 'Đang dùng', type: 'checkbox' },
    ],
  },
  products: {
    slug: 'products', entity: 'product', title: 'Sản phẩm / Hàng hóa', apiPath: '/api/products', importExport: true,
    detailExtra: (row) => <ProductImages productId={row.id} />,
    columns: [
      { key: 'thumbnail', label: 'Ảnh', render: (r) => r.thumbnail_url
          ? <img src={r.thumbnail_url} alt="" style={{ width: 40, height: 40, objectFit: 'cover', borderRadius: 6 }} />
          : <span style={{ color: '#cbd5e1' }}><i className="ti ti-photo" /></span> },
      { key: 'code', label: 'Mã VTBB/NL' }, { key: 'name', label: 'Tên VTBB/NL' }, { key: 'item_group', label: 'Phân loại' },
      { key: 'unit', label: 'ĐVT' },
      { key: 'hh_code', label: 'Mã HH' }, { key: 'hh_name', label: 'Tên SP (HH)' },
      { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active) },
    ],
    filters: [
      { key: 'code', label: 'Mã VTBB/NL' }, { key: 'name', label: 'Tên' },
      { key: 'item_group', label: 'Phân loại', source: { url: '/api/item-groups', value: 'name', label: 'name' } },
      { key: 'hh_code', label: 'Mã HH (sản phẩm)' },
      { key: 'unit', label: 'ĐVT', source: { url: '/api/units', value: 'name', label: 'name' } },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
    ],
    condFilters: [
      condText('code', 'Mã VTBB/NL'), condText('name', 'Tên VTBB/NL'),
      condSource('item_group', 'Phân loại', { url: '/api/item-groups', value: 'name', label: 'name' }),
      condSource('unit', 'ĐVT', { url: '/api/units', value: 'name', label: 'name' }),
      condText('hh_code', 'Mã HH (sản phẩm)'), condText('hh_name', 'Tên SP (HH)'),
      condSelect('is_active', 'Trạng thái', ACTIVE_OPTIONS, ['eq']),
    ],
    fields: [
      { key: 'code', label: 'Mã VTBB/NL', readonlyOnEdit: true }, { key: 'name', label: 'Tên VTBB/NL' },
      { key: 'invoice_name', label: 'Tên trên hóa đơn' }, { key: 'legal_name', label: 'Tên pháp lý' },
      { key: 'item_group', label: 'Phân loại', type: 'select', source: { url: '/api/item-groups', value: 'name', label: 'name' } },
      { key: 'unit', label: 'ĐVT' },
      { key: 'hh_code', label: 'Mã HH (sản phẩm)' }, { key: 'hh_name', label: 'Tên Sản phẩm (HH)' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS, colorMap: { 'true': '#16a34a', 'false': '#dc2626' } },
    ],
  },
  contracts: {
    slug: 'contracts', entity: 'contract', title: 'Hợp đồng', apiPath: '/api/contracts',
    rowStyle: contractRowStyle,
    columns: [
      { key: 'code', label: 'Mã HĐ' },
      { key: 'party_type', label: 'Đối tượng' },
      { key: 'party_name', label: 'Tên đối tượng', render: (r) => r.party_name || r.party_code },
      { key: 'title', label: 'Trích yếu' }, { key: 'contract_type', label: 'Loại' },
      { key: 'end_date', label: 'Đến ngày' },
      { key: 'signed', label: 'Đã ký', render: (r) => (r.signed ? '✓' : '—') },
      { key: 'expiry', label: 'Hết hạn', render: (r) => contractExpiryBadge(r.expiry) },
      { key: 'status', label: 'Trạng thái' },
    ],
    filters: [
      { key: 'code', label: 'Mã HĐ' },
      { key: 'party_name', label: 'Tên đối tượng' },
      { key: 'party_type', label: 'Đối tượng', type: 'select', options: ['Nhà cung cấp', 'Khách hàng', 'Khác'].map((x) => ({ value: x, label: x })) },
      { key: 'contract_type', label: 'Loại', type: 'select', options: CONTRACT_TYPES },
      { key: 'status', label: 'Trạng thái', type: 'select', options: CONTRACT_STATUS },
      { key: 'expiry', label: 'Tình trạng hết hạn', type: 'select', options: ['Còn hạn', 'Sắp hết hạn', 'Hết hạn'].map((x) => ({ value: x, label: x })) },
      { key: 'signed', label: 'Đã ký', type: 'select', options: [{ value: 'true', label: 'Đã ký' }, { value: 'false', label: 'Chưa ký' }] },
      { key: 'end_date', label: 'Ngày hết hạn', type: 'daterange' },
    ],
    // `expiry` / `signed` là cột tính toán, không lọc điều kiện được -> chỉ có ở thanh lọc cơ bản
    condFilters: [
      condText('code', 'Mã HĐ'), condText('title', 'Trích yếu'),
      condText('party_name', 'Tên đối tượng'), condText('party_code', 'Mã đối tượng'),
      condSelect('party_type', 'Đối tượng',
        ['Nhà cung cấp', 'Khách hàng', 'Khác'].map((x) => ({ value: x, label: x }))),
      condSelect('contract_type', 'Loại HĐ', CONTRACT_TYPES),
      condSelect('status', 'Trạng thái', CONTRACT_STATUS),
      condDate('end_date', 'Ngày hết hạn'),
    ],
    fields: [],  // chi tiết dùng trang riêng (ContractDetail) — có đính kèm file
  },
  employees: {
    slug: 'employees', entity: 'employee', apiPath: '/api/employees',
    title: 'Nhân sự', importExport: true,
    columns: [
      { key: 'code', label: 'Mã NV' }, { key: 'full_name', label: 'Họ tên' }, { key: 'email', label: 'Email' },
      { key: 'department_name', label: 'Phòng ban' },
      { key: 'position', label: 'Vị trí' },
      { key: 'status', label: 'Trạng thái', render: (r) => badge(r.status === 'Chính thức', r.status, r.status) },
    ],
    filters: [
      { key: 'code', label: 'Mã NV' }, { key: 'full_name', label: 'Họ tên' }, { key: 'email', label: 'Email' },
      { key: 'status', label: 'Trạng thái', type: 'select', options: EMPLOYEE_STATUS },
    ],
    condFilters: [
      condText('code', 'Mã NV'), condText('full_name', 'Họ tên'), condText('email', 'Email'),
      condSource('department_id', 'Phòng ban', { url: '/api/departments', value: 'id', label: 'name' }),
      condText('position', 'Vị trí / Chức vụ'),
      condSelect('status', 'Trạng thái', EMPLOYEE_STATUS),
      condSelect('is_active', 'Đang dùng', ACTIVE_OPTIONS, ['eq']),
    ],
    fields: [
      { key: 'code', label: 'Mã NV', readonlyOnEdit: true }, { key: 'full_name', label: 'Họ tên' },
      { key: 'email', label: 'Email' }, { key: 'phone', label: 'Số điện thoại' },
      { key: 'department_id', label: 'Phòng ban', type: 'select', source: { url: '/api/departments', value: 'id', label: 'name' } },
      // CR-022: đây là CHỨC DANH để hiển thị/in phiếu, KHÔNG cấp quyền cho tài khoản đăng nhập.
      { key: 'position', label: 'Vị trí / Chức vụ',
        hint: 'Chỉ là chức danh hiển thị trên phiếu — không phải phân quyền. Quyền thật của tài khoản đặt ở màn "Phân quyền tài khoản".' },
      { key: 'status', label: 'Trạng thái', type: 'select', default: 'Chính thức', options: EMPLOYEE_STATUS },
    ],
  },
  roles: {
    slug: 'roles', entity: 'role', title: 'Phân quyền tài khoản', apiPath: '/api/roles',
    columns: [
      { key: 'code', label: 'Mã Vai trò' },
      { key: 'name', label: 'Tên Vai trò' },
      { key: 'description', label: 'Mô tả' }
    ],
    filters: [
      { key: 'code', label: 'Mã' },
      { key: 'name', label: 'Tên' }
    ],
    // Danh sách vai trò dùng trang riêng (pages/RolePermissions — ma trận phân quyền, có ô
    // "Tìm vai trò" sẵn) nên không gắn bộ lọc điều kiện; entry này chỉ phục vụ trang chi tiết.
    fields: [
      { key: 'code', label: 'Mã Vai trò', readonlyOnEdit: true },
      { key: 'name', label: 'Tên Vai trò' },
      { key: 'description', label: 'Mô tả', type: 'textarea' }
    ],
  },
  'purchase-requests': {
    slug: 'purchase-requests', entity: 'purchase_request', title: 'Yêu cầu mua hàng (PYC)', apiPath: '/api/purchase-requests', txn: true, cloneable: true,
    rowStyle: (r: any) => r.has_cancelled_line ? { background: '#fdecea' } : undefined,   // có dòng "Hủy đơn" → tô đỏ
    columns: [
      { key: 'code', label: 'Mã PYC' },
      { key: 'created_at', label: 'Ngày tạo', render: (r) => fmtDateTime(r.created_at) || '—' },
      { key: 'requester', label: 'Người yêu cầu' },
      { key: 'department', label: 'Bộ phận' },
      { key: 'need_date', label: 'Cần hàng' },
      { key: 'total', label: 'Tổng tiền', render: (r) => (r.total ? Number(r.total).toLocaleString('vi-VN') + ' đ' : '0 đ') },
      { key: 'is_urgent', label: 'Gấp', render: (r) => (r.is_urgent ? <span className="badge warn">Gấp</span> : '—') },
      { key: 'status', label: 'Trạng thái', render: (r) => prBadge(r.status) },
    ],
    filters: [
      { key: 'code', label: 'Mã PYC' },
      { key: 'company_id', label: 'Công ty', source: { url: '/api/companies', value: 'id', label: 'name' } },
      { key: 'requester', label: 'Người yêu cầu' },
      { key: 'department', label: 'Bộ phận YC', source: { url: '/api/departments', value: 'name', label: 'name' } },
      { key: 'assignee', label: 'NSTM phụ trách', source: { url: '/api/employees', value: 'code', label: 'full_name' } },
      { key: 'item_group', label: 'Phân loại', source: { url: '/api/item-groups', value: 'name', label: 'name' } },
      { key: 'request_date', label: 'Ngày tạo', type: 'daterange' },
      { key: 'need_date', label: 'Ngày cần hàng', type: 'daterange' },
      { key: 'is_urgent', label: 'Đơn gấp', type: 'select', options: [{ value: 'true', label: 'Gấp' }, { value: 'false', label: 'Thường' }] },
      { key: 'status', label: 'Trạng thái', type: 'select', options: [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'rejected', label: 'Bị trả lại' },
        { value: 'cancelled', label: 'Đã từ chối' },
        { value: 'processing', label: 'Đang xử lý' }, { value: 'completed', label: 'Hoàn thành' },
      ] },
    ],
    // company_id / assignee / item_group lọc qua bảng con hoặc scope -> không có trong FILTERABLE
    condFilters: [
      condText('code', 'Mã PYC'), condText('requester', 'Người yêu cầu'),
      condSource('department', 'Bộ phận YC', { url: '/api/departments', value: 'name', label: 'name' }),
      condDate('request_date', 'Ngày tạo'), condDate('need_date', 'Ngày cần hàng'),
      { name: 'is_urgent', label: 'Đơn gấp', type: 'boolean' },
      condSelect('status', 'Trạng thái', [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'rejected', label: 'Bị trả lại' },
        { value: 'cancelled', label: 'Đã từ chối' },
        { value: 'processing', label: 'Đang xử lý' }, { value: 'completed', label: 'Hoàn thành' }]),
    ],
    fields: [],  // chi tiết dùng trang riêng (PurchaseRequestDetail)
  },
  'survey-requests': {
    slug: 'survey-requests', entity: 'survey_request', title: 'Yêu cầu báo giá', apiPath: '/api/survey-requests', txn: true, cloneable: true,
    columns: [
      { key: 'code', label: 'Mã phiếu' },
      { key: 'purpose', label: 'Mục đích' },
      { key: 'requester', label: 'Người yêu cầu' },
      { key: 'department', label: 'Bộ phận' },
      { key: 'created_at', label: 'Ngày tạo', render: (r) => fmtDateTime(r.created_at) || '—' },
      { key: 'status', label: 'Trạng thái', render: (r) => srBadge(r.status) },
    ],
    filters: [
      { key: 'code', label: 'Mã phiếu' },
      { key: 'company_id', label: 'Công ty', source: { url: '/api/companies', value: 'id', label: 'name' } },
      { key: 'requester', label: 'Người yêu cầu' },
      { key: 'department', label: 'Bộ phận', source: { url: '/api/departments', value: 'name', label: 'name' } },
      { key: 'assignee', label: 'NSTM phụ trách', source: { url: '/api/employees', value: 'code', label: 'full_name' } },
      { key: 'item_group', label: 'Phân loại', source: { url: '/api/item-groups', value: 'name', label: 'name' } },
      { key: 'request_date', label: 'Ngày tạo', type: 'daterange' },
      { key: 'status', label: 'Trạng thái', type: 'select', options: [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'processing', label: 'Đang xử lý' },
        { value: 'survey_done', label: 'Đã khảo sát' }, { value: 'pr_created', label: 'Đã tạo YCMH' },
        { value: 'done', label: 'Hoàn thành' }, { value: 'rejected', label: 'Bị trả lại' },
        { value: 'cancelled', label: 'Đã từ chối' }] },
    ],
    condFilters: [
      condText('code', 'Mã phiếu'), condText('requester', 'Người yêu cầu'),
      condSource('department', 'Bộ phận', { url: '/api/departments', value: 'name', label: 'name' }),
      condDate('request_date', 'Ngày tạo'),
      condSelect('status', 'Trạng thái', [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'processing', label: 'Đang xử lý' },
        { value: 'survey_done', label: 'Đã khảo sát' }, { value: 'pr_created', label: 'Đã tạo YCMH' },
        { value: 'done', label: 'Hoàn thành' }, { value: 'rejected', label: 'Bị trả lại' },
        { value: 'cancelled', label: 'Đã từ chối' }]),
    ],
    fields: [],
  },
  warehouses: {
    slug: 'warehouses', entity: 'warehouse', title: 'Kho', apiPath: '/api/warehouses', importExport: true,
    columns: [
      { key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên kho' },
      { key: 'address', label: 'Địa chỉ', render: (r) => <div style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={r.address}>{r.address || '—'}</div> },
      { key: 'is_active', label: 'Trạng thái', render: (r) => <div style={{ textAlign: 'center', minWidth: 80 }}>{badge(r.is_active)}</div> },
    ],
    filters: [
      { key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên kho' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
    ],
    condFilters: [
      condText('code', 'Mã'), condText('name', 'Tên kho'),
      condSelect('is_active', 'Trạng thái', ACTIVE_OPTIONS, ['eq']),
    ],
    fields: [
      { key: 'code', label: 'Mã', readonlyOnEdit: true }, { key: 'name', label: 'Tên kho' },
      { key: 'address', label: 'Địa chỉ', type: 'textarea' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS, colorMap: { 'true': '#16a34a', 'false': '#dc2626' } },
    ],
  },
  units: {
    slug: 'units', entity: 'unit', title: 'Đơn vị tính', apiPath: '/api/units', importExport: true,
    columns: [
      { key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên ĐVT' },
      { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active) },
    ],
    filters: [
      { key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
    ],
    condFilters: [
      condText('code', 'Mã'), condText('name', 'Tên ĐVT'),
      condSelect('is_active', 'Trạng thái', ACTIVE_OPTIONS, ['eq']),
    ],
    fields: [
      { key: 'code', label: 'Mã', readonlyOnEdit: true }, { key: 'name', label: 'Tên ĐVT' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS, colorMap: { 'true': '#16a34a', 'false': '#dc2626' } },
    ],
  },
  'item-groups': {
    slug: 'item-groups', entity: 'item_group', title: 'Phân loại VTBB/NL', apiPath: '/api/item-groups', importExport: true,
    columns: [
      { key: 'name', label: 'Phân loại' },
      { key: 'std_days', label: 'Ngày QĐ (sẵn hàng)' }, { key: 'std_days_unavail', label: 'Ngày QĐ (không sẵn)' },
      { key: 'apply_date', label: 'Ngày áp dụng' },
      { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active) },
    ],
    filters: [
      { key: 'name', label: 'Phân loại' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
    ],
    condFilters: [
      condText('code', 'Mã'), condText('name', 'Phân loại'),
      condSelect('is_active', 'Trạng thái', ACTIVE_OPTIONS, ['eq']),
    ],
    fields: [
      { key: 'name', label: 'Phân loại', readonlyOnEdit: true },
      { key: 'std_days', label: 'Số ngày QĐ khi NCC CÓ sẵn hàng' },
      { key: 'std_days_unavail', label: 'Số ngày QĐ khi KHÔNG sẵn hàng' },
      { key: 'note', label: 'Ghi chú', type: 'textarea' }, { key: 'apply_date', label: 'Ngày áp dụng' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS, colorMap: { 'true': '#16a34a', 'false': '#dc2626' } },
    ],
  },
  departments: {
    slug: 'departments', entity: 'department', apiPath: '/api/departments',
    title: 'Phòng Ban', importExport: true,
    columns: [
      { key: 'name', label: 'Phòng ban' },
      { key: 'manager_name', label: 'Trưởng bộ phận' },
      { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active, 'Hoạt động', 'Đã ẩn') },
    ],
    filters: [
      { key: 'q', label: 'Tìm kiếm' },   // tìm chung: tên phòng ban / trưởng bộ phận
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: DEPT_ACTIVE },
    ],
    // manager_name là cột join (trưởng bộ phận) -> tìm qua ô "Tìm kiếm" chung, không lọc điều kiện được
    condFilters: [
      condText('code', 'Mã phòng ban'), condText('name', 'Tên phòng ban'),
      condSelect('is_active', 'Trạng thái', DEPT_ACTIVE, ['eq']),
    ],
    fields: [
      { key: 'code', label: 'Mã Phòng ban', readonlyOnEdit: true },
      { key: 'name', label: 'Tên Phòng ban' },
      { key: 'manager_id', label: 'Trưởng bộ phận', type: 'select', source: { url: '/api/employees', value: 'id', label: 'full_name' } },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: DEPT_ACTIVE },
    ],
    detailExtra: (row) => <DepartmentMembers departmentId={row.id} managerId={row.manager_id} />,
  },
  'category-assignees': {
    slug: 'category-assignees', entity: 'category_assignee', title: 'Phân công phụ trách (theo phân loại)', apiPath: '/api/category-assignees',
    columns: [
      { key: 'item_group_name', label: 'Phân loại' },
      { key: 'primary_name', label: 'NSTM chính' },
      { key: 'backup_name', label: 'NSTM dự phòng' },
    ],
    // Màn danh sách dùng trang riêng (pages/CategoryAssignees) — bộ lọc điều kiện khai báo ở
    // config/conditional-filters.ts (CATEGORY_ASSIGNEE_COND_FILTERS); ở đây chỉ dùng cho trang chi tiết.
    filters: [],
    fields: [
      { key: 'item_group_id', label: 'Phân loại VTBB', type: 'select', source: { url: '/api/item-groups', value: 'id', label: 'name' } },
      { key: 'primary_employee_id', label: 'NSTM chính', type: 'select', source: { url: '/api/employees', value: 'id', label: 'full_name' } },
      { key: 'backup_employee_id', label: 'NSTM dự phòng', type: 'select', source: { url: '/api/employees', value: 'id', label: 'full_name' } },
    ],
  },
  'purchase-orders': {
    slug: 'purchase-orders', entity: 'purchase_order', title: 'Đơn mua hàng (PO)', apiPath: '/api/purchase-orders', txn: true, cloneable: true,
    columns: [
      { key: 'code', label: 'Mã PO' },
      { key: 'misa_code', label: 'Mã MISA', render: (r) => r.misa_code || '' },
      { key: 'created_at', label: 'Ngày đặt', render: (r) => fmtDateTime(r.created_at) || '' },
      { key: 'note', label: 'Ghi chú', render: (r) => {
        const t = String(r.note || '').trim();
        return t
          ? <span title={t} style={{ display: 'inline-block', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', verticalAlign: 'middle' }}>{t}</span>
          : '';
      } },
      { key: 'supplier_code', label: 'Nhà cung cấp', render: (r) => r.supplier_code || r.supplier_name || '' },
      { key: 'pr_code', label: 'Mã PYC', link: (r) => (r.pr_id ? `/purchase-requests/${r.pr_id}` : '') },
      { key: 'amount', label: 'Tiền hàng', render: (r) => (r.amount ? Number(r.amount).toLocaleString('vi-VN') + ' đ' : '0 đ') },
      { key: 'is_urgent', label: 'Gấp', render: (r) => (r.is_urgent ? <span className="badge warn">Gấp</span> : '') },
      { key: 'document_status', label: 'Hồ sơ chứng từ', render: (r) => docStatusBadge(r.document_status) },
      { key: 'status', label: 'Trạng thái', render: (r) => poBadge(r.status) },
    ],
    filters: [
      { key: 'code', label: 'Mã PO' },
      { key: 'misa_code', label: 'Mã MISA' },
      { key: 'document_status', label: 'Hồ sơ chứng từ', type: 'select', options: [
        { value: 'chưa có chứng từ', label: 'Chưa có chứng từ' },
        { value: 'đã có thông tin chứng từ', label: 'Đã có chứng từ' },
        { value: 'đã đủ chứng từ', label: 'Đã đủ chứng từ' }] },
      { key: 'company_id', label: 'Công ty', source: { url: '/api/companies', value: 'id', label: 'name' } },
      { key: 'supplier_code', label: 'Nhà cung cấp', source: { url: '/api/suppliers', value: 'code', label: 'name' } },
      { key: 'nspt', label: 'NSPT phụ trách', source: { url: '/api/employees', value: 'full_name', label: 'full_name' } },
      { key: 'pr_code', label: 'Mã PYC' },
      { key: 'item_group', label: 'Phân loại', source: { url: '/api/item-groups', value: 'name', label: 'name' } },
      { key: 'invoice_no', label: 'Số hóa đơn' },
      { key: 'order_date', label: 'Ngày đặt', type: 'daterange' },
      { key: 'is_urgent', label: 'Đơn gấp', type: 'select', options: [{ value: 'true', label: 'Gấp' }, { value: 'false', label: 'Thường' }] },
      { key: 'status', label: 'Trạng thái', type: 'select', options: [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'partial', label: 'Đã nhận một phần' },
        { value: 'received', label: 'Đã nhận đủ' }, { value: 'completed', label: 'Hoàn thành' },
        { value: 'rejected', label: 'Bị trả lại' }, { value: 'cancelled', label: 'Đã từ chối' }] },
    ],
    // Chỉ khai báo cột có trong service.FILTERABLE của purchase_order — cột ngoài whitelist
    // (item_group, invoice_no… lọc qua bảng con) backend sẽ bỏ qua.
    condFilters: [
      condText('code', 'Mã PO'), condText('misa_code', 'Mã MISA'), condText('pr_code', 'Mã PYC'),
      condSource('supplier_code', 'Nhà cung cấp', { url: '/api/suppliers', value: 'code', label: 'name' }),
      condSource('nspt', 'NSPT phụ trách', { url: '/api/employees', value: 'full_name', label: 'full_name' }),
      condText('department', 'Bộ phận'),
      condDate('order_date', 'Ngày đặt'),
      { name: 'is_urgent', label: 'Đơn gấp', type: 'boolean' },
      condSelect('document_status', 'Hồ sơ chứng từ', [
        { value: 'chưa có chứng từ', label: 'Chưa có chứng từ' },
        { value: 'đã có thông tin chứng từ', label: 'Đã có chứng từ' },
        { value: 'đã đủ chứng từ', label: 'Đã đủ chứng từ' }]),
      condSelect('status', 'Trạng thái', [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'partial', label: 'Đã nhận một phần' },
        { value: 'received', label: 'Đã nhận đủ' }, { value: 'completed', label: 'Hoàn thành' },
        { value: 'rejected', label: 'Bị trả lại' }, { value: 'cancelled', label: 'Đã từ chối' }]),
    ],
    fields: [],  // chi tiết dùng trang riêng (PurchaseOrderDetail)
  },
  'payment-requests': {
    slug: 'payment-requests', entity: 'payment_request', title: 'Yêu cầu thanh toán', apiPath: '/api/payment-requests', txn: true,
    columns: [
      { key: 'code', label: 'Mã phiếu' },
      { key: 'request_date', label: 'Ngày lập' },
      { key: 'created_by_name', label: 'Người yêu cầu' },
      { key: 'supplier_name', label: 'Nhà cung cấp', render: (r) => r.supplier_name || r.supplier_code },
      { key: 'source_type', label: 'Loại', render: (r) => (r.source_type === 'shipping' ? 'Vận chuyển' : 'Hàng hóa') },
      { key: 'total', label: 'Số tiền', render: (r) => (r.total ? Number(r.total).toLocaleString('vi-VN') + ' đ' : '0 đ') },
      { key: 'status', label: 'Trạng thái', render: (r) => (r.status === 'cancelled' ? <span className="badge err">Đã từ chối</span> : poBadge(r.status === 'paid' ? 'received' : r.status)) },
    ],
    filters: [
      { key: 'code', label: 'Mã phiếu' },
      { key: 'po_code', label: 'Mã PO' },
      { key: 'company_id', label: 'Công ty', source: { url: '/api/companies', value: 'id', label: 'name' } },
      { key: 'supplier_code', label: 'Nhà cung cấp', source: { url: '/api/suppliers', value: 'code', label: 'name' } },
      { key: 'source_type', label: 'Loại', type: 'select', options: [{ value: 'goods', label: 'Hàng hóa' }, { value: 'shipping', label: 'Vận chuyển' }] },
      { key: 'request_date', label: 'Ngày lập', type: 'daterange' },
      { key: 'status', label: 'Trạng thái', type: 'select', options: [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'paid', label: 'Đã chi' },
        { value: 'cancelled', label: 'Đã từ chối' }] },
    ],
    // po_code / company_id lọc qua bảng con hoặc scope -> không có trong FILTERABLE
    condFilters: [
      condText('code', 'Mã phiếu'),
      condSource('supplier_code', 'Nhà cung cấp', { url: '/api/suppliers', value: 'code', label: 'name' }),
      condSelect('source_type', 'Loại',
        [{ value: 'goods', label: 'Hàng hóa' }, { value: 'shipping', label: 'Vận chuyển' }]),
      condDate('request_date', 'Ngày lập'),
      condSelect('status', 'Trạng thái', [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'paid', label: 'Đã chi' },
        { value: 'cancelled', label: 'Đã từ chối' }]),
    ],
    fields: [],
  },
  'surveys': {
    slug: 'surveys', entity: 'survey', title: 'Khảo sát (NCC + Sản phẩm)', apiPath: '/api/surveys', txn: true, cloneable: true,
    columns: [
      { key: 'code', label: 'Mã phiếu' }, { key: 'sr_code', label: 'Mã YCBG' },
      { key: 'main_content', label: 'Nội dung chính' },
      { key: 'item_code', label: 'Mã hàng' },
      { key: 'item_group', label: 'Nhóm hàng' }, { key: 'nspt', label: 'NSPT' },
      { key: 'created_at', label: 'Ngày tạo', render: (r) => fmtDateTime(r.created_at) || '—' },
      { key: 'status', label: 'Trạng thái', render: (r) => srBadge(r.status) },
    ],
    filters: [
      { key: 'code', label: 'Mã phiếu' },
      { key: 'sr_code', label: 'Mã YCBG' },
      { key: 'main_content', label: 'Nội dung chính' },
      { key: 'item_code', label: 'Mã hàng' },
      { key: 'product_code', label: 'Mã SP (NCC)' },
      { key: 'item_group', label: 'Nhóm hàng', source: { url: '/api/item-groups', value: 'name', label: 'name' } },
      { key: 'nspt', label: 'NSPT' },
      { key: 'status', label: 'Trạng thái', type: 'select', options: [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'rejected', label: 'Bị trả lại' },
        { value: 'cancelled', label: 'Đã từ chối' }] },
    ],
    // product_code nằm ở dòng khảo sát (bảng con) -> không có trong FILTERABLE của survey
    condFilters: [
      condText('code', 'Mã phiếu'), condText('sr_code', 'Mã YCBG'), condText('pr_code', 'Mã PYC'),
      condText('main_content', 'Nội dung chính'), condText('item_code', 'Mã hàng'),
      condSource('item_group', 'Nhóm hàng', { url: '/api/item-groups', value: 'name', label: 'name' }),
      condText('nspt', 'NSPT'),
      condSelect('status', 'Trạng thái', [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'rejected', label: 'Bị trả lại' },
        { value: 'cancelled', label: 'Đã từ chối' }]),
    ],
    fields: [],
  },
}
