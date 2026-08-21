import { FilterField } from '../components/FilterBar'
import type { FilterFieldDefinition } from '../components/conditional-filter'
import { condDate, condSelect, condSource, condText, DEPT_SRC, EMP_SRC } from './conditional-filters'
import DepartmentMembers from '../components/DepartmentMembers'
import ProductImages from '../components/ProductImages'
import PurchaseHistoryTable from '../components/PurchaseHistoryTable'
import EmployeeAccountCard from '../components/employee-account-card'
import EmployeeAvatar from '../components/employee-avatar'
import WarehousePurchaseLines from '../components/warehouse-purchase-lines'
import { CONTRACT_TYPES, contractTypeLabel } from '../utils/contractTypes'
import { fmtDateStr, fmtDateTime } from '../utils/datetime'
import { fmtVND } from '../utils/money'
import { initialsOf } from '../utils/name'

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
  group?: string          // tên nhóm — form chi tiết chèn tiêu đề nhóm trước field đầu tiên của nhóm.
                          // Không đặt group thì form giữ nguyên dạng phẳng như cũ.
  fullWidth?: boolean     // chiếm trọn 1 dòng của lưới 2 cột + textarea cao hơn (CSS .form-row.full).
                          // Dành cho ô mô tả dài (địa chỉ kho, ghi chú), nằm nửa cột thì quá chật.
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
  /** CR-068 — hiện nút "Xuất Excel": gọi GET {apiPath}/export/xlsx với bộ lọc + dòng đã tick +
   *  danh sách cột đang hiện. Backend phải có route đó và cấp hành động `export`.
   *  Bật cờ này cũng bật luôn CỘT TICK CHỌN dòng trên bảng. */
  exportXlsx?: boolean
  /** Cho phép nút "Xóa đã chọn" (xóa hàng loạt qua `DELETE {apiPath}?ids=`). Mặc định TẮT:
   *  cột tick chọn của CR-068 chỉ để chọn phiếu cần xuất, không mở thêm đường xóa dữ liệu. */
  bulkDelete?: boolean
  rowStyle?: (row: any) => any   // tô màu dòng theo điều kiện (vd HĐ sắp hết hạn)
  txn?: boolean                  // chứng từ giao dịch (PYC/PO/khảo sát/YCTT): ai có 'read' là xem danh sách được
  cloneable?: boolean            // hiện nút "Nhân bản" mỗi dòng → POST {apiPath}/{id}/clone tạo phiếu nháp mới
  detailExtra?: (row: any) => any  // section tùy biến render dưới form ở trang chi tiết (chỉ khi đã có bản ghi)
  // Tab phụ ở trang chi tiết (chỉ khi đã có bản ghi). Tab "Thông tin" luôn tự có, không cần khai báo.
  // Dùng khi nội dung phụ đủ lớn để tách khỏi form (vd Lịch sử mua hàng của sản phẩm).
  detailTabs?: { key: string; label: string; render: (row: any) => any }[]
  detailHeader?: (row: any) => any // chèn vào ĐẦU thanh tiêu đề trang chi tiết (vd ảnh đại diện nhân sự)
  // Chip mô tả dưới tên ở thẻ đầu trang chi tiết (mã, chức vụ, trạng thái…)
  detailChips?: (row: any) => { icon?: string; text: string; cls?: string }[]
  detailTwoCols?: boolean          // trang chi tiết chia 2 cột: form trái, thẻ phụ + lịch sử phải
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
const CONTRACT_STATUS = [{ value: 'Hiệu lực', label: 'Hiệu lực' }, { value: 'Hết hạn', label: 'Hết hạn' }, { value: 'Thanh lý', label: 'Thanh lý' }]

export const PR_STATUS: Record<string, { label: string; cls: string }> = {
  draft: { label: 'Nháp', cls: 'gray' },
  submitted: { label: 'Chờ duyệt', cls: 'warn' },
  approved: { label: 'Đã duyệt', cls: 'ok' },
  // CR-034: TP duyệt xong phiếu dừng ở 'Đã duyệt' (chưa có NSTM, chưa tạo được ĐMH);
  // thu mua bấm Điều phối mới sang 'Đã điều phối' — mốc bắt đầu làm việc thật.
  dispatched: { label: 'Đã điều phối', cls: 'ok' },
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
    // KHÔNG khai báo detailHeader: đã bỏ logo pháp nhân, thẻ danh tính chỉ còn tên + chip.
    // KHÔNG bật detailTwoCols: công ty không có thẻ phụ nào bên phải, để 2 cột sẽ
    // bóp hẹp form và chừa một khoảng trống lớn. Form full chiều ngang, lịch sử xuống dưới.
    detailChips: (row) => [
      ...(row.code ? [{ icon: 'ti-hash', text: row.code, cls: 'code' }] : []),
      ...(row.tax_code ? [{ icon: 'ti-receipt-tax', text: `MST ${row.tax_code}` }] : []),
      ...(row.legal_rep_name ? [{ icon: 'ti-user-shield', text: row.legal_rep_name }] : []),
      { icon: row.is_active ? 'ti-circle-check' : 'ti-circle-x', text: row.is_active ? 'Đang dùng' : 'Ngừng' },
    ],
    columns: [
      // Ô Tên có chữ cái đầu của MÃ công ty làm ảnh đại diện (không còn logo tải lên)
      { key: 'name', label: 'Tên', render: (r) => (
        <span style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
          <span className="avatar" style={{ flex: 'none' }}>{((r.code || r.name || '?')[0] || '?').toUpperCase()}</span>
          <span style={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.name}</span>
        </span>
      ) },
      { key: 'code', label: 'Mã' }, { key: 'tax_code', label: 'MST' },
      { key: 'legal_rep_name', label: 'Người đại diện' },
      { key: 'is_active', label: 'Trạng thái', render: (r) => badge(r.is_active) },
    ],
    filters: [
      { key: 'code', label: 'Mã' }, { key: 'name', label: 'Tên' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS },
    ],
    condFilters: [
      condText('code', 'Mã'), condText('name', 'Tên'), condText('tax_code', 'MST'),
      condSelect('is_active', 'Trạng thái', ACTIVE_OPTIONS, ['eq']),
    ],
    fields: [
      { key: 'code', label: 'Mã', readonlyOnEdit: true, group: 'Định danh' },
      { key: 'name', label: 'Tên pháp nhân', group: 'Định danh' },
      { key: 'tax_code', label: 'MST', group: 'Định danh' },
      { key: 'invoice_email', label: 'Email nhận hóa đơn', group: 'Hóa đơn & Liên hệ',
        hint: 'Nơi nhận hóa đơn điện tử của pháp nhân này.' },
      { key: 'address', label: 'Địa chỉ', type: 'textarea', group: 'Hóa đơn & Liên hệ' },
      { key: 'legal_representative_id', label: 'Người đại diện pháp lý', type: 'select', group: 'Đại diện pháp lý',
        source: { url: '/api/employees', value: 'id', label: 'full_name' } },
      { key: 'legal_rep_title', label: 'Chức danh', group: 'Đại diện pháp lý',
        hint: 'Chức danh in trên hợp đồng / chứng từ, vd "Giám đốc".' },
      { key: 'parent', label: 'Công ty mẹ (ID)', type: 'number', zeroAsBlank: true, group: 'Tổ chức',
        hint: 'Nhập ID pháp nhân cấp trên; để trống nếu đây là công ty gốc.' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS, group: 'Tổ chức' },
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
      // 'legal_type' đã bỏ: backend KHÔNG xử lý param này ở đâu (không có trong FILTERABLE,
      // cũng không có nhánh riêng) nên ô lọc đó xưa nay không có tác dụng.
      { key: 'code', label: 'Mã / viết tắt' }, { key: 'name', label: 'Tên NCC' },
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
      { key: 'payment_terms', label: 'Hình thức thanh toán', type: 'select', options: PAYMENT_TERMS_OPTIONS },       // Ô này gửi thẳng TỈ LỆ lên API (khác trang chi tiết NCC — ở đó nhập theo % rồi chia 100).
      // BE chặn 0 ≤ vat < 1 (CR-058), nên nhãn phải nói rõ đơn vị kẻo người dùng gõ 8 rồi ăn 422.
      { key: 'vat', label: 'VAT — tỉ lệ, dưới 1 (0.08 = 8%)', type: 'number' },
      { key: 'is_active', label: 'Đang dùng', type: 'checkbox' },
    ],
  },
  products: {
    slug: 'products', entity: 'product', title: 'Sản phẩm / Hàng hóa', apiPath: '/api/products', importExport: true,
    detailExtra: (row) => <ProductImages productId={row.id} />,
    detailTabs: [
      { key: 'history', label: 'Lịch sử mua hàng', render: (row) => <PurchaseHistoryTable productCode={row.code} /> },
    ],
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
      { key: 'specs', label: 'Thông số kỹ thuật', type: 'textarea',
        hint: 'Tự điền vào ô "Xuất xứ / TSKT / chất liệu" của dòng hàng khi chọn SP này trong Đơn mua hàng.' },
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
      { key: 'title', label: 'Trích yếu' },
      { key: 'contract_type', label: 'Loại', render: (r) => contractTypeLabel(r.contract_type) || '—' },
      { key: 'end_date', label: 'Đến ngày' },
      { key: 'signed', label: 'Đã ký', render: (r) => (r.signed ? '✓' : '—') },
      { key: 'expiry', label: 'Hết hạn', render: (r) => contractExpiryBadge(r.expiry) },
      { key: 'status', label: 'Trạng thái' },
    ],
    filters: [
      { key: 'code', label: 'Mã HĐ' },
      { key: 'party_name', label: 'Tên đối tượng' },
      { key: 'status', label: 'Trạng thái', type: 'select', options: CONTRACT_STATUS },
      // 'expiry' và 'signed' KHÔNG đưa xuống bộ lọc điều kiện được: controller tính riêng
      // (expiry so end_date với hôm nay, signed là cột bool xử lý ngoài apply_filters).
      { key: 'expiry', label: 'Tình trạng hết hạn', type: 'select', options: ['Còn hạn', 'Sắp hết hạn', 'Hết hạn'].map((x) => ({ value: x, label: x })) },
      { key: 'signed', label: 'Đã ký', type: 'select', options: [{ value: 'true', label: 'Đã ký' }, { value: 'false', label: 'Chưa ký' }] },
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
    detailHeader: (row) => (
      <EmployeeAvatar employeeId={row.id} fullName={row.full_name} avatar={row.avatar} hasAccount={!!row.user_id} />
    ),
    detailTwoCols: true,
    detailChips: (row) => [
      ...(row.code ? [{ icon: 'ti-id-badge-2', text: row.code, cls: 'code' }] : []),
      ...(row.position ? [{ icon: 'ti-briefcase', text: row.position }] : []),
      ...(row.department_name ? [{ icon: 'ti-building', text: row.department_name }] : []),
      ...(row.status ? [{ icon: 'ti-user-check', text: row.status }] : []),
    ],
    detailExtra: (row) => <EmployeeAccountCard employeeId={row.id} email={row.email} />,
    columns: [
      // Ảnh đại diện đi kèm luôn trong ô Họ tên (không tách cột riêng).
      // Ảnh lấy từ tài khoản đăng nhập; chưa có ảnh thì hiện chữ cái đầu của tên.
      { key: 'full_name', label: 'Họ tên', render: (r) => (
        <span style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
          {r.avatar
            ? <img src={r.avatar} alt="" className="avatar" style={{ objectFit: 'cover', flex: 'none' }} />
            : <span className="avatar" style={{ flex: 'none' }}>{initialsOf(r.full_name)}</span>}
          <span style={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.full_name}</span>
        </span>
      ) },
      { key: 'code', label: 'Mã NV' },
      { key: 'email', label: 'Email' },
      { key: 'department_name', label: 'Phòng ban' },
      { key: 'position', label: 'Vị trí' },
      { key: 'status', label: 'Trạng thái', render: (r) => badge(r.status === 'Chính thức', r.status, r.status) },
    ],
    filters: [
      { key: 'code', label: 'Mã NV' }, { key: 'full_name', label: 'Họ tên' },
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
      { key: 'code', label: 'Mã NV', readonlyOnEdit: true, group: 'Định danh' },
      { key: 'full_name', label: 'Họ tên', group: 'Định danh' },
      { key: 'email', label: 'Email', group: 'Liên hệ',
        hint: 'Cũng là tên đăng nhập của tài khoản — đổi email sẽ KHÔNG tự đổi tài khoản đã cấp.' },
      { key: 'phone', label: 'Số điện thoại', group: 'Liên hệ' },
      { key: 'department_id', label: 'Phòng ban', type: 'select', group: 'Công việc', source: { url: '/api/departments', value: 'id', label: 'name' } },
      // CR-022: đây là CHỨC DANH để hiển thị/in phiếu, KHÔNG cấp quyền cho tài khoản đăng nhập.
      { key: 'position', label: 'Vị trí / Chức vụ', group: 'Công việc',
        hint: 'Chỉ là chức danh hiển thị trên phiếu — không phải phân quyền. Quyền thật của tài khoản đặt ở màn "Phân quyền tài khoản".' },
      { key: 'status', label: 'Trạng thái', type: 'select', default: 'Chính thức', group: 'Công việc', options: EMPLOYEE_STATUS },
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
    slug: 'purchase-requests', entity: 'purchase_request', title: 'Yêu cầu mua hàng (PYC)', apiPath: '/api/purchase-requests', txn: true, cloneable: true, exportXlsx: true,
    rowStyle: (r: any) => r.has_cancelled_line ? { background: '#fdecea' } : undefined,   // có dòng "Hủy đơn" → tô đỏ
    columns: [
      { key: 'code', label: 'Mã PYC' },
      { key: 'created_at', label: 'Ngày tạo', render: (r) => fmtDateTime(r.created_at) || '—' },
      { key: 'requester', label: 'Người yêu cầu' },
      { key: 'department', label: 'Bộ phận' },
      { key: 'need_date', label: 'Ngày cần hàng', render: (r) => (r.need_date ? fmtDateStr(r.need_date) : '—') },
      { key: 'total', label: 'Tổng tiền', render: (r) => (r.total ? fmtVND(r.total) + ' đ' : '0 đ') },
      { key: 'is_urgent', label: 'Gấp', render: (r) => (r.is_urgent ? <span className="badge warn">Gấp</span> : '—') },
      { key: 'status', label: 'Trạng thái', render: (r) => prBadge(r.status) },
    ],
    filters: [
      // Chỉ giữ ô tìm nhanh + các bộ lọc KHÔNG đưa xuống bộ lọc điều kiện được
      // (company_id / assignee / item_group / product lọc qua bảng con, không nằm trong FILTERABLE).
      { key: 'code', label: 'Mã PYC' },
      // CR-069: gõ một phần mã hoặc tên hàng đều ra (tìm trong các dòng hàng của phiếu)
      { key: 'product', label: 'Mã / tên hàng' },
      { key: 'company_id', label: 'Công ty', source: { url: '/api/companies', value: 'id', label: 'name' } },
      { key: 'assignee', label: 'NSTM phụ trách', source: { url: '/api/employees', value: 'code', label: 'full_name' } },
      { key: 'item_group', label: 'Phân loại', source: { url: '/api/item-groups', value: 'name', label: 'name' } },
      { key: 'status', label: 'Trạng thái', type: 'select', options: [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'dispatched', label: 'Đã điều phối' },
        { value: 'rejected', label: 'Bị trả lại' },
        { value: 'cancelled', label: 'Đã từ chối' },
        { value: 'processing', label: 'Đang xử lý' }, { value: 'completed', label: 'Hoàn thành' },
      ] },
    ],
    // company_id / assignee / item_group lọc qua bảng con hoặc scope -> không có trong FILTERABLE
    condFilters: [
      condText('code', 'Mã PYC'),
      // CR-088: hai ô này lọc theo ID (xem `conditional-filters.ts`).
      condSource('requester_id', 'Người yêu cầu', EMP_SRC),
      condSource('department_id', 'Bộ phận YC', DEPT_SRC),
      condDate('request_date', 'Ngày tạo'), condDate('need_date', 'Ngày cần hàng'),
      { name: 'is_urgent', label: 'Đơn gấp', type: 'boolean' },
      condSelect('status', 'Trạng thái', [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'dispatched', label: 'Đã điều phối' },
        { value: 'rejected', label: 'Bị trả lại' },
        { value: 'cancelled', label: 'Đã từ chối' },
        { value: 'processing', label: 'Đang xử lý' }, { value: 'completed', label: 'Hoàn thành' }]),
    ],
    fields: [],  // chi tiết dùng trang riêng (PurchaseRequestDetail)
  },
  'survey-requests': {
    slug: 'survey-requests', entity: 'survey_request', title: 'Yêu cầu báo giá', apiPath: '/api/survey-requests', txn: true, cloneable: true, exportXlsx: true,
    columns: [
      { key: 'code', label: 'Mã phiếu' },
      { key: 'purpose', label: 'Mục đích' },
      { key: 'requester', label: 'Người yêu cầu' },
      { key: 'department', label: 'Bộ phận' },
      { key: 'created_at', label: 'Ngày tạo', render: (r) => fmtDateTime(r.created_at) || '—' },
      { key: 'status', label: 'Trạng thái', render: (r) => srBadge(r.status) },
    ],
    filters: [
      // company_id / assignee / item_group / product lọc qua bảng con → không đưa xuống bộ lọc điều kiện được
      { key: 'code', label: 'Mã phiếu' },
      // CR-069: dòng YCBG chưa có mã hàng → tìm trong Thông số kỹ thuật / Yêu cầu khác
      // và mã/tên SP của phương án ĐÃ CHỐT
      { key: 'product', label: 'Sản phẩm cần báo giá' },
      { key: 'company_id', label: 'Công ty', source: { url: '/api/companies', value: 'id', label: 'name' } },
      { key: 'assignee', label: 'NSTM phụ trách', source: { url: '/api/employees', value: 'code', label: 'full_name' } },
      { key: 'item_group', label: 'Phân loại', source: { url: '/api/item-groups', value: 'name', label: 'name' } },
      { key: 'status', label: 'Trạng thái', type: 'select', options: [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'processing', label: 'Đang xử lý' },
        { value: 'survey_done', label: 'Đã khảo sát' }, { value: 'pr_created', label: 'Đã tạo YCMH' },
        { value: 'done', label: 'Hoàn thành' }, { value: 'rejected', label: 'Bị trả lại' },
        { value: 'cancelled', label: 'Đã từ chối' }] },
    ],
    condFilters: [
      condText('code', 'Mã phiếu'),
      condSource('requester_id', 'Người yêu cầu', EMP_SRC),      // CR-088: lọc theo ID
      condSource('department_id', 'Bộ phận', DEPT_SRC),
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
    detailTabs: [
      { key: 'po-lines', label: 'Đơn hàng về kho', render: (row) => <WarehousePurchaseLines warehouseCode={row.code} /> },
    ],
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
    // KHÔNG khai báo detailHeader: kho không có ảnh/logo (giống trang Phòng ban).
    // Địa chỉ KHÔNG làm chip: nhiều kho ghi địa chỉ dài 150+ ký tự, có cả xuống dòng
    // (trụ sở + nhà máy + người nhận) -> nhét vào chip sẽ vỡ thẻ danh tính.
    detailChips: (row) => [
      ...(row.code && row.code !== row.name ? [{ icon: 'ti-hash', text: row.code, cls: 'code' }] : []),
      { icon: row.is_active ? 'ti-circle-check' : 'ti-circle-x', text: row.is_active ? 'Đang dùng' : 'Ngừng / Ẩn' },
    ],
    fields: [
      { key: 'code', label: 'Mã', readonlyOnEdit: true, group: 'Định danh',
        hint: 'Mã kho dùng khi import/export và khi chọn kho nhập ở dòng hàng. Không sửa được sau khi tạo.' },
      { key: 'name', label: 'Tên kho', group: 'Định danh',
        hint: 'Tên đầy đủ, hiện trên đơn mua hàng và phiếu nhập.' },
      // Địa chỉ thường dài / nhiều dòng -> cho trọn chiều ngang
      { key: 'address', label: 'Địa chỉ', type: 'textarea', group: 'Vị trí', fullWidth: true,
        hint: 'Nơi giao hàng thực tế. Ghi thêm người nhận / số điện thoại nếu cần.' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS, group: 'Tổ chức',
        colorMap: { 'true': '#16a34a', 'false': '#dc2626' },
        hint: 'Ngừng dùng sẽ ẩn khỏi ô chọn kho; dữ liệu cũ vẫn giữ nguyên.' },
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
    // KHÔNG khai báo detailHeader: ĐVT không có ảnh/logo (giống trang Phòng ban).
    // Nhiều ĐVT có mã TRÙNG tên ("Hộp"/"Hộp") -> chip mã lặp lại tiêu đề, chỉ hiện khi khác nhau.
    detailChips: (row) => [
      ...(row.code && row.code !== row.name ? [{ icon: 'ti-hash', text: row.code, cls: 'code' }] : []),
      { icon: row.is_active ? 'ti-circle-check' : 'ti-circle-x', text: row.is_active ? 'Đang dùng' : 'Ngừng / Ẩn' },
    ],
    fields: [
      { key: 'code', label: 'Mã', readonlyOnEdit: true, group: 'Định danh',
        hint: 'Mã dùng khi import/export và khi tham chiếu ĐVT ở dòng hàng. Không sửa được sau khi tạo.' },
      { key: 'name', label: 'Tên ĐVT', group: 'Định danh',
        hint: 'Tên hiển thị trong ô chọn ĐVT (Cái, Thùng, Kg…).' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS, group: 'Tổ chức',
        colorMap: { 'true': '#16a34a', 'false': '#dc2626' },
        hint: 'Ngừng dùng sẽ ẩn khỏi ô chọn ĐVT; dữ liệu cũ vẫn giữ nguyên.' },
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
    // KHÔNG khai báo detailHeader: phân loại không có ảnh/logo (giống trang Phòng ban).
    detailChips: (row) => [
      ...(row.code ? [{ icon: 'ti-hash', text: row.code, cls: 'code' }] : []),
      ...(row.std_days || row.std_days_unavail
        ? [{ icon: 'ti-clock', text: `Ngày QĐ: ${row.std_days || '—'} (sẵn hàng) · ${row.std_days_unavail || '—'} (không sẵn)` }]
        : []),
      ...(row.apply_date ? [{ icon: 'ti-calendar', text: `Áp dụng từ ${row.apply_date}` }] : []),
      { icon: row.is_active ? 'ti-circle-check' : 'ti-circle-x', text: row.is_active ? 'Đang dùng' : 'Ngừng / Ẩn' },
    ],
    fields: [
      { key: 'name', label: 'Phân loại', readonlyOnEdit: true, group: 'Định danh' },
      { key: 'std_days', label: 'Số ngày QĐ khi NCC CÓ sẵn hàng', group: 'Thời gian quy định',
        hint: 'Số ngày chuẩn từ lúc đặt tới lúc nhận, dùng để tính hạn giao và cảnh báo trễ.' },
      { key: 'std_days_unavail', label: 'Số ngày QĐ khi KHÔNG sẵn hàng', group: 'Thời gian quy định',
        hint: 'Áp dụng khi NCC phải sản xuất/nhập thêm mới có hàng.' },
      { key: 'apply_date', label: 'Ngày áp dụng', group: 'Thời gian quy định',
        hint: 'Mốc bắt đầu áp dụng số ngày quy định ở trên.' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS, group: 'Khác',
        colorMap: { 'true': '#16a34a', 'false': '#dc2626' },
        hint: 'Ngừng dùng sẽ ẩn khỏi ô chọn phân loại; dữ liệu cũ vẫn giữ nguyên.' },
      // Ghi chú dài -> cho trọn chiều ngang, nằm nửa cột thì gõ vài chữ đã xuống dòng
      { key: 'note', label: 'Ghi chú', type: 'textarea', group: 'Khác', fullWidth: true },
    ],
  },
  departments: {
    slug: 'departments', entity: 'department', apiPath: '/api/departments',
    title: 'Phòng Ban', importExport: true,
    // KHÔNG khai báo detailHeader: phòng ban không có ảnh/logo, thẻ danh tính chỉ
    // gồm tên + chip mô tả (khác trang Công ty có logo tải lên được).
    // KHÔNG bật detailTwoCols: bảng nhân sự thuộc phòng cần trọn chiều ngang,
    // để 2 cột sẽ bóp hẹp cả form lẫn bảng. Form full ngang, nhân sự + lịch sử xuống dưới.
    detailChips: (row) => [
      ...(row.code ? [{ icon: 'ti-hash', text: row.code, cls: 'code' }] : []),
      ...(row.manager_name ? [{ icon: 'ti-user-star', text: `Trưởng BP: ${row.manager_name}` }] : []),
      { icon: row.is_active ? 'ti-circle-check' : 'ti-circle-x', text: row.is_active ? 'Hoạt động' : 'Đã ẩn' },
    ],
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
      { key: 'code', label: 'Mã Phòng ban', readonlyOnEdit: true, group: 'Định danh' },
      { key: 'name', label: 'Tên Phòng ban', group: 'Định danh' },
      { key: 'manager_id', label: 'Trưởng bộ phận', type: 'select', group: 'Phụ trách',
        source: { url: '/api/employees', value: 'id', label: 'full_name' },
        hint: 'Người duyệt/ký thay mặt phòng ban trong luồng mua hàng.' },
      { key: 'is_active', label: 'Trạng thái', type: 'select', options: DEPT_ACTIVE, group: 'Tổ chức',
        hint: 'Ẩn phòng ban đã giải thể; dữ liệu cũ vẫn giữ nguyên.' },
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
    slug: 'purchase-orders', entity: 'purchase_order', title: 'Đơn mua hàng (PO)', apiPath: '/api/purchase-orders', txn: true, cloneable: true, exportXlsx: true,
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
      { key: 'amount', label: 'Tiền hàng', render: (r) => (r.amount ? fmtVND(r.amount) + ' đ' : '0 đ') },
      { key: 'is_urgent', label: 'Gấp', render: (r) => (r.is_urgent ? <span className="badge warn">Gấp</span> : '') },
      { key: 'document_status', label: 'Hồ sơ chứng từ', render: (r) => docStatusBadge(r.document_status) },
      { key: 'status', label: 'Trạng thái', render: (r) => poBadge(r.status) },
    ],
    filters: [
      // company_id / item_group / invoice_no lọc qua bảng con hoặc scope → không đưa xuống
      // bộ lọc điều kiện được. Phần còn lại (mã MISA, NCC, NSPT, mã PYC, ngày đặt, hồ sơ
      // chứng từ, đơn gấp) đã có trong "Bộ lọc điều kiện".
      { key: 'code', label: 'Mã PO' },
      { key: 'company_id', label: 'Công ty', source: { url: '/api/companies', value: 'id', label: 'name' } },
      { key: 'item_group', label: 'Phân loại', source: { url: '/api/item-groups', value: 'name', label: 'name' } },
      { key: 'invoice_no', label: 'Số hóa đơn' },
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
      condSource('nspt_id', 'NSPT phụ trách', EMP_SRC),      // CR-088: lọc theo ID
      condSource('department_id', 'Bộ phận', DEPT_SRC),
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
      { key: 'payment_method', label: 'Hình thức TT', render: (r) => (r.payment_method === 'cash' ? 'Tiền mặt' : 'Chuyển khoản') },
      { key: 'total', label: 'Số tiền', render: (r) => (r.total ? fmtVND(r.total) + ' đ' : '0 đ') },
      { key: 'status', label: 'Trạng thái', render: (r) => (r.status === 'cancelled' ? <span className="badge err">Đã từ chối</span> : poBadge(r.status === 'paid' ? 'received' : r.status)) },
    ],
    filters: [
      // po_code / company_id lọc qua bảng con hoặc scope → không đưa xuống bộ lọc điều kiện được
      { key: 'code', label: 'Mã phiếu' },
      { key: 'po_code', label: 'Mã PO' },
      { key: 'company_id', label: 'Công ty', source: { url: '/api/companies', value: 'id', label: 'name' } },
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
      condSelect('payment_method', 'Hình thức thanh toán',
        [{ value: 'transfer', label: 'Chuyển khoản' }, { value: 'cash', label: 'Tiền mặt' }]),
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
      // product_code nằm ở dòng khảo sát (bảng con) → không đưa xuống bộ lọc điều kiện được
      { key: 'code', label: 'Mã phiếu' },
      { key: 'product_code', label: 'Mã SP (NCC)' },
      { key: 'item_group', label: 'Nhóm hàng', source: { url: '/api/item-groups', value: 'name', label: 'name' } },
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
      // Phiếu khảo sát CHƯA có cột `nspt_id` (CR-087 mới neo YCMH/YCBG/ĐMH) nên ô này vẫn
      // lọc theo TÊN. Đổi sang id ở đây là backend lặng lẽ bỏ qua điều kiện.
      condText('nspt', 'NSPT'),
      condSelect('status', 'Trạng thái', [
        { value: 'draft', label: 'Nháp' }, { value: 'submitted', label: 'Chờ duyệt' },
        { value: 'approved', label: 'Đã duyệt' }, { value: 'rejected', label: 'Bị trả lại' },
        { value: 'cancelled', label: 'Đã từ chối' }]),
    ],
    fields: [],
  },
}
