import { Fragment, useEffect, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { askConfirm, askPrompt } from '../components/confirm'
import { useAuth } from '../auth/AuthContext'
import { poBadge, PAYMENT_TERMS_OPTIONS } from '../config/cruds'
import SearchSelect from '../components/SearchSelect'
import ProductPicker from '../components/ProductPicker'
import CopyText from '../components/CopyText'
import PurchaseHistoryPickerModal, { HistoryPick } from '../components/PurchaseHistoryPickerModal'
import NumberInput from '../components/NumberInput'
import { VAT_MAX, VAT_DECIMALS } from '../utils/vat'
import DateInput from '../components/DateInput'
import TextAreaAuto from '../components/TextAreaAuto'
import NotFound from '../components/NotFound'
import { toast } from '../components/toast'
import DocumentUploadModal from '../components/DocumentUploadModal'
import DocumentAttachmentSection from '../components/DocumentAttachmentSection'
import CommentThread from '../components/CommentThread'
import AuditTimeline from '../components/AuditTimeline'
import { fmtSize, fileIcon } from '../utils/file-type'
import { newDupCodes } from '../utils/lines'
import { normGroup, regulatedDate, stdDaysMap, stdDaysOf } from '../utils/lead-time'
import { fmtDateStr } from '../utils/datetime'

const API = '/api/purchase-orders'
// Ô/cột ĐƠN GIÁ cho lẻ tới 4 chữ số thập phân — giá quy đổi hay lẻ tới phần nghìn đồng
// (vd 1.668,182 đ/cái); làm tròn ở đây là lệch tiền khi nhân với số lượng lớn.
const PRICE_DECIMALS = 4
// SỐ LƯỢNG và các số chung
const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
// TIỀN thì LÀM TRÒN VỀ ĐỒNG khi hiển thị: đơn giá lẻ 4 chữ số kéo theo thành tiền có đuôi
// lẻ (733.999,2 · 4.760.000,08) mà kế toán chỉ ghi nhận tới đồng. Vẫn tính toán và lưu ở
// độ chính xác đầy đủ, chỉ làm tròn lúc in ra màn hình.
const fmtVND = (n: any) => Math.round(Number(n) || 0).toLocaleString('vi-VN')
// ĐƠN GIÁ thì ngược lại — phải hiện đủ 4 chữ số lẻ, cắt bớt là người dùng tưởng bị mất số
const fmtPrice = (n: any) => Number(n || 0).toLocaleString('vi-VN', { maximumFractionDigits: PRICE_DECIMALS })
const SHIP_UNITS = ['Kiện', 'Chuyến', 'm2', 'tấn']
const CurrencyInput = ({ value, onChange, disabled, style, className }: any) =>
  <NumberInput value={value} onChange={onChange} disabled={disabled} style={style}
    maxDecimals={PRICE_DECIMALS} className={className ?? 'cell-input'} />

// Ô chữ dài trong popup chi tiết dòng: cao vừa 1 dòng rồi tự giãn khi nội dung dài
const POPUP_TEXT = { minHeight: 40, fontSize: 14 }

// Màu badge TIẾN ĐỘ dòng ĐMH (progress_status). 4 bước thường TỰ ĐỘNG theo dữ liệu (backend);
// tay chỉ còn Tạm ngưng / Hủy đơn / Tiếp tục.
const PG_COLOR: Record<string, string> = {
  'Chưa đặt hàng': '#94a3b8', 'Đã đặt hàng': '#2563eb', 'Đã nhận hàng': '#0891b2',
  'Chưa gửi ĐMH cho KT': '#db2777', 'Đã gửi ĐMH cho KT': '#7c3aed',
  'Hoàn thành': '#16a34a', 'Tạm ngưng': '#d97706', 'Hủy đơn': '#dc2626',
}

// Trạng thái hồ sơ chứng từ (cập nhật tay, Task 10b)
const DOC_STATUS_OPTS = ['chưa có chứng từ', 'đã có thông tin chứng từ', 'đã đủ chứng từ']
const DOC_STATUS_COLOR: Record<string, string> = {
  'chưa có chứng từ': '#dc2626', 'đã có thông tin chứng từ': '#d97706', 'đã đủ chứng từ': '#16a34a',
}

// bao-CR-319 — loại đơn. Số phải khớp `OrderType` ở backend
// (app/modules/purchase_order/model.py); tiếng Việt chỉ nằm ở tầng hiển thị.
const ORDER_TYPE_DOMESTIC = 1
const ORDER_TYPE_IMPORT = 2
const ORDER_TYPE_OPTS: [number, string][] = [
  [ORDER_TYPE_DOMESTIC, 'Trong nước'], [ORDER_TYPE_IMPORT, 'Nhập khẩu'],
]
// Loại tiền hay dùng. Gõ tay được loại khác nên danh sách này chỉ là lối tắt.
const DEFAULT_CURRENCY = 'VND'
const CURRENCY_OPTS = ['VND', 'USD', 'CNY', 'EUR', 'JPY', 'KRW', 'THB']

// bao-CR-319 P3 — chi phí lô hàng nhập khẩu. Số phải khớp `ImportCostType` /
// `AllocationMethod` ở backend (app/modules/purchase_order/model.py).
const IMPORT_COST_TYPE_OPTS: [number, string][] = [
  [1, 'Cước vận tải quốc tế'], [2, 'Phí địa phương tại cảng'], [3, 'Phí dịch vụ hải quan'],
  [4, 'Thuế nhập khẩu'], [5, 'Thuế GTGT hàng nhập khẩu'], [6, 'Thuế tiêu thụ đặc biệt'],
  [7, 'Thuế bảo vệ môi trường'], [8, 'Phí kiểm tra chuyên ngành'], [9, 'Bảo hiểm hàng hóa'],
  [10, 'Vận chuyển nội địa'], [11, 'Lưu kho / lưu bãi'], [99, 'Chi phí khác'],
]
const COST_TYPE_LABEL = (v: any) =>
  IMPORT_COST_TYPE_OPTS.find(([n]) => n === (Number(v) || 99))?.[1] || 'Chi phí khác'
// Khoản nộp cho nhà nước — chọn mấy loại này thì tự điền NCC "Ngân sách nhà nước"
const IMPORT_COST_TAX_TYPES = [4, 5, 6, 7]
const STATE_BUDGET_SUPPLIER_CODE = 'NSNN'
const STATE_BUDGET_SUPPLIER_NAME = 'Ngân sách nhà nước'
const ALLOC_BY_VALUE = 1
const ALLOC_BY_PRODUCT = 4
// Cách 5: thu mua gõ tay số tiền từng dòng hàng ở bảng "Chi phí theo dòng hàng" (để cân số
// với chứng từ); tổng phải bằng số quy đổi của khoản, backend chặn khi Lưu.
const ALLOC_MANUAL = 5
const ALLOCATION_OPTS: [number, string][] = [
  [ALLOC_BY_VALUE, 'Theo giá trị'], [2, 'Theo khối lượng'], [3, 'Theo số lượng'],
  [ALLOC_BY_PRODUCT, 'Chỉ định một mã hàng'], [ALLOC_MANUAL, 'Nhập tay'],
]
// Tổng nhập tay được lệch tối đa chừng này so với số quy đổi (khớp MANUAL_ALLOCATION_TOLERANCE backend)
const MANUAL_ALLOC_TOLERANCE = 1
// bao-CR-319 P5 — popup Tạo YCTT có 3 luồng nợ; `import_cost` là nợ từng dòng chi phí lô hàng
type PayTab = 'goods' | 'shipping' | 'import_cost'
const PAY_TABS: [PayTab, string][] = [
  ['goods', 'NCC sản xuất (hàng)'], ['shipping', 'NCC vận chuyển'], ['import_cost', 'Chi phí lô hàng'],
]
// Trạng thái đơn mà công nợ chi phí đã sinh (khớp IMPORT_COST_PAYABLE_STATUSES ở backend)
const PO_PAYABLE_STATUSES = ['approved', 'partial', 'received', 'completed']
const emptyImportCost = {
  cost_type: 1, description: '', supplier_code: '', supplier_name: '',
  // Để trống đồng tiền / tỷ giá là cố ý: backend chép xuống từ đơn (xem _save_import_costs)
  currency: '', exchange_rate: 0, amount: 0, vat: 0,
  allocation_method: ALLOC_BY_VALUE, allocation_target: '', manual_allocation: {} as Record<string, number>,
  invoice_no: '', invoice_date: '', payment_due_date: '', note: '',
}

const emptyItem = {
  product_code: '', product_name: '', invoice_name: '', item_group: '', spec: '', fg_code: '', fg_name: '',
  supplier_ready: true, required_date: '', expected_date: '', unit: '', invoice_no: '', invoice_date: '', document_delivery_date: '',   // NCC có sẵn hàng — mặc định check cho dòng mới
  qty_request: 0, qty_order: 0, price: 0, vat: 8, warehouse_code: '', note: '', deliveries: [],
  // Tiền tệ theo dòng — để trống thì backend chép xuống từ đơn (bao-CR-319)
  currency: '', exchange_rate: 0, weight_kg: 0, dimension: '',
}
const emptyDelivery = {
  delivery_no: 1, warehouse_code: '', carrier_code: '', carrier_name: '', ship_qty: 0, ship_unit: '',
  received_qty: 0, promised_date: '', expected_date: '', received_date: '', invoice_no: '',
  shipping_unit_price: 0, shipping_amount: 0, qc_result: '', progress_note: '',
}

// CR-095 (phiếu hỗ trợ TK19082601) — bộ trường BẮT BUỘC của một dòng hàng trước khi
// gửi duyệt. PHẢI khớp `REQUIRED_LINE_FIELDS` ở backend
// (app/modules/purchase_order/service.py): lệch một ô là nút Gửi duyệt mở ra nhưng API
// trả 400, hoặc ngược lại — nút khóa mà không ai biết vì sao.
//
// Không có VAT: 0 vừa là "chưa nhập" vừa là "hàng không chịu thuế", chặn thì khóa luôn
// mặt hàng 0% hợp lệ. Xem chú thích dài ở backend.
const REQUIRED_LINE_FIELDS: [string, string][] = [
  ['product_code', 'Mã hàng'],
  ['item_group', 'Phân loại'],
  ['product_name', 'Tên hàng'],
  ['invoice_name', 'Tên trên hóa đơn'],
  ['required_date', 'Ngày yêu cầu có hàng'],
  ['expected_date', 'Ngày dự kiến có hàng'],
  ['unit', 'ĐVT'],
  ['warehouse_code', 'Kho nhận mặc định'],
  ['qty_request', 'SL yêu cầu'],
  ['qty_order', 'SL đặt NCC'],
  ['price', 'Đơn giá'],
]
const NUMERIC_LINE_FIELDS = ['qty_request', 'qty_order', 'price']

// Dấu * đỏ sau nhãn ô bắt buộc — theo lệ đang dùng ở cột "Tên hàng *" của bảng dòng hàng
const Req = () => <span style={{ color: 'var(--red)' }} title="Bắt buộc trước khi gửi duyệt"> *</span>

// Nhãn các ô còn trống của 1 dòng hàng (rỗng ⇒ chưa gửi duyệt được)
function missingLineFields(it: any): string[] {
  return REQUIRED_LINE_FIELDS
    .filter(([k]) => NUMERIC_LINE_FIELDS.includes(k)
      ? !(Number(it?.[k]) > 0)
      : !String(it?.[k] ?? '').trim())
    .map(([, label]) => label)
}

// Số ngày giữa 2 mốc "YYYY-MM-DD" (a − b); null nếu thiếu/không hợp lệ
function daysBetween(a: string, b: string): number | null {
  if (!a || !b) return null
  const da = new Date(a + 'T00:00:00').getTime(), db = new Date(b + 'T00:00:00').getTime()
  if (isNaN(da) || isNaN(db)) return null
  return Math.round((da - db) / 86400000)
}

// Đơn gấp = có ≥1 dòng mà thời gian giao (ngày yêu cầu − ngày đặt) NHỎ HƠN số ngày QĐ của phân loại
// VTBB/NL. Số ngày QĐ nay LUÔN lấy mốc dài nhất (không sẵn hàng), không còn theo checkbox "NCC có
// sẵn hàng" — xem utils/lead-time.ts.
function computeUrgent(items: any[], orderDate: string, stdMap: Record<string, number>): boolean {
  if (!orderDate) return false
  for (const it of items || []) {
    const std = stdDaysOf(stdMap, it.item_group)
    if (std <= 0) continue
    const lead = daysBetween(it.required_date, orderDate)
    if (lead === null) continue
    if (lead < std) return true
  }
  return false
}

export default function PurchaseOrderDetail() {
  const { id } = useParams()
  const isNew = id === 'new'
  const { can, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [po, setPo] = useState<any>({
    code: '', misa_code: '', pr_code: '', survey_code: '', company_id: 0, supplier_code: '',
    supplier_name: '', department: '', nspt: '', order_date: new Date().toISOString().slice(0, 10),
    vat_rate: 0.08, payment_terms: '', is_urgent: false, note: '', status: 'draft', items: [],
    order_type: ORDER_TYPE_DOMESTIC, currency: DEFAULT_CURRENCY, exchange_rate: 1,
    customs_decl_no: '', customs_decl_date: '',
    // bao-CR-321 — điều khoản in, chép từ NCC lúc chọn; 0 / rỗng = bản in dùng NCC rồi mặc định
    inspection_days: 0, return_days: 0, invoice_deadline: '',
  })
  const [companies, setCompanies] = useState<any[]>([])
  const [suppliers, setSuppliers] = useState<any[]>([])
  const [units, setUnits] = useState<string[]>([])
  const [warehouses, setWarehouses] = useState<any[]>([])
  const [prList, setPrList] = useState<any[]>([])
  const [itemGroups, setItemGroups] = useState<any[]>([])   // danh mục phân loại VTBB/NL (có ngày QĐ) để tự tính đơn gấp
  const [employees, setEmployees] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [docModal, setDocModal] = useState(false)
  const [docTypeLabels, setDocTypeLabels] = useState<Record<string, string>>({})
  const [attByDelivery, setAttByDelivery] = useState<Record<number, any[]>>({})
  const [editingItemIdx, setEditingItemIdx] = useState<number | null>(null)
  const [editingCostIdx, setEditingCostIdx] = useState<number | null>(null)   // popup chi tiết một khoản chi phí NK
  const [historyIdx, setHistoryIdx] = useState<number | null>(null)   // dòng đang mở popup lịch sử mua hàng
  const [printOpen, setPrintOpen] = useState(false)   // dropdown chọn loại bản in
  const [allocOpen, setAllocOpen] = useState<Set<number>>(new Set())   // dòng hàng đang mở ở panel chi phí theo dòng
  const [notFound, setNotFound] = useState(false)
  const [payModal, setPayModal] = useState(false)              // popup tạo yêu cầu thanh toán
  const [payables, setPayables] = useState<any[]>([])          // các khoản nợ chưa trả đủ của đơn (hàng + vận chuyển)
  const [paySel, setPaySel] = useState<number[]>([])           // id khoản nợ được chọn
  const [payTab, setPayTab] = useState<PayTab>('goods')
  const [costSel, setCostSel] = useState<number[]>([])         // bao-CR-319 P5: id khoản nợ chi phí được tick ở bảng chi phí

  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    api.get('/api/suppliers', { params: { page_size: 1000 } }).then((r) => setSuppliers(r.data.data.items))
    api.get('/api/units', { params: { page_size: 300 } }).then((r) => setUnits(r.data.data.items.map((x: any) => x.name)))
    api.get('/api/warehouses', { params: { page_size: 300 } }).then((r) => setWarehouses(r.data.data.items))
    api.get('/api/purchase-requests', { params: { page_size: 1000 } }).then((r) => setPrList(r.data.data.items))
    api.get('/api/item-groups', { params: { page_size: 1000 } }).then((r) => setItemGroups(r.data.data.items)).catch(() => {})
    // Danh sách nhân sự cho dropdown NSPT phụ trách (admin); user thường có thể bị 403 → bỏ qua
    api.get('/api/employees', { params: { page_size: 1000 } }).then((r) => setEmployees(r.data.data.items)).catch(() => {})
  }, [])

  async function loadAll() {
    try {
      const r = await api.get(`${API}/${id}`); setPo(r.data.data)
      savedCodes.current = (r.data.data.items || []).map((it: any) => it.product_code || '')
      api.get('/api/audit-logs', { params: { entity: 'purchase_order', entity_id: id } }).then((x) => setLogs(x.data.data))
      api.get('/api/attachments', { params: { entity: 'purchase_order', entity_id: id } }).then((x) => setFiles(x.data.data))
    } catch (ex: any) {
      if (ex?.response?.status === 403 || ex?.response?.status === 404) {
        setNotFound(true); return
      }
      throw ex
    }
  }
  useEffect(() => { if (!isNew) { setNotFound(false); loadAll() } }, [id])

  // nạp nhãn loại chứng từ 1 lần để hiện badge cạnh file
  useEffect(() => {
    api.get('/api/attachments/doc-types')
      .then((x) => setDocTypeLabels(Object.fromEntries((x.data.data || []).map((t: any) => [t.value, t.label]))))
      .catch(() => {})
  }, [])

  // Điền sẵn khi tạo ĐMH từ phiếu YCMH đã duyệt (điều hướng kèm state.fromPr). Chưa lưu — user xem lại rồi bấm Tạo.
  useEffect(() => {
    if (!isNew) return
    const fromPr = (location.state as any)?.fromPr
    if (!fromPr) return
    setPo((s: any) => ({
      ...s,
      pr_code: fromPr.pr_code || '',
      company_id: fromPr.company_id || 0,
      department: fromPr.department || '',
      nspt: fromPr.nspt || '',   // hiện sẵn người phụ trách dòng ở YCMH (backend vẫn tự suy nếu để trống)
      supplier_name: fromPr.supplier_name || '',
      supplier_code: fromPr.supplier_code || '',
      vat_rate: fromPr.vat_rate || 0.08,
      is_urgent: !!fromPr.is_urgent,
      note: fromPr.note || '',
      items: (fromPr.items || []).map((it: any) => ({ ...emptyItem, ...it })),
    }))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isNew])

  const goodsSuppliers = suppliers.filter((s) => s.supplier_type !== 'transport')
  const carriers = suppliers.filter((s) => s.supplier_type === 'transport')

  // Đơn CHƯA hoàn thành (và chưa hủy) thì vẫn cho sửa sản phẩm/thông tin bên trong.
  // CR-073: đơn đang CHỜ DUYỆT cũng khóa — sửa lúc này là người duyệt bấm duyệt cho một
  // nội dung khác với nội dung đã trình. Muốn sửa thì người duyệt trả đơn về (Bị trả lại).
  // CR-108 (phiếu hỗ trợ TK19082604): đơn ĐÃ DUYỆT cũng khóa. Trước đây 'approved' không
  // nằm trong danh sách này nên duyệt xong vẫn đổi được mã hàng, số lượng, đơn giá — nội
  // dung trưởng phòng đã ký không còn khớp đơn gửi NCC. Muốn đổi thì bấm "Hủy duyệt".
  const approved = ['approved', 'partial', 'received'].includes(po.status)
  const locked = ['submitted', 'completed', 'cancelled'].includes(po.status) || approved
  const canWrite = can('purchase_order', isNew ? 'create' : 'write')
  const headerEditable = (isNew || !locked) && canWrite
  // Vài ô CHỈ có thông tin sau khi duyệt (tên trên hóa đơn, ngày dự kiến có hàng, kho nhận,
  // ghi chú, ngày giao chứng từ cho KT) — khóa luôn thì không ai nhập được. Backend mở đúng
  // bấy nhiêu ô, xem LINE_FIELDS_EDITABLE_AFTER_APPROVAL ở purchase_order/service.py.
  const afterApproveEditable = !isNew && approved && canWrite
  const deliveryEditable = !isNew && ['approved', 'partial', 'received'].includes(po.status) && can('purchase_order', 'write')
  // Đính kèm chứng từ vào lần giao: cho phép CẢ khi đơn đã 'Hoàn thành' (chỉ chặn khi Hủy / chưa lưu).
  // Chỉ mở nút gắn/xóa file — KHÔNG mở các field khác (SL nhận, ngày nhận...). Task 10a.
  const deliveryAttachEditable = !isNew && ['approved', 'partial', 'received', 'completed'].includes(po.status) && can('purchase_order', 'write')
  const canDelete = isNew || ['draft', 'rejected'].includes(po.status)
  // Tiến độ dòng: người phụ trách cập nhật khi đơn đã duyệt trở đi
  const progressEditable = !isNew && ['approved', 'partial', 'received'].includes(po.status) && can('purchase_order', 'write')
  // Dòng đã Hoàn thành / Hủy đơn → khóa HẲN dòng đó (kể cả bảng vận chuyển), không sửa gì được
  const lineLocked = (it: any) => ['Hoàn thành', 'Hủy đơn'].includes(it?.progress_status || '')
  // Dòng ĐÃ NHẬN HÀNG → khóa nhận diện sản phẩm (Mã hàng, ĐVT). Đổi lúc này sẽ dời
  // phiếu nhập kho + tồn kho đã ghi theo mã cũ sang mã khác. Backend cũng chặn.
  const lineReceived = (it: any) => Number(it?.qty_received || 0) > 0
  // CR-096: popup lịch sử mua hàng mở được ở MỌI trạng thái đơn (nó chỉ đọc), nhưng chỉ cho
  // "Dùng giá này" khi dòng thật sự còn sửa được — nếu không, lượt lưu sẽ bị backend chặn.
  const historyReadOnly = (it: any) => !headerEditable || lineLocked(it)
  const PRODUCT_LOCK_HINT = 'Dòng đã nhận hàng — không đổi được Mã hàng / Tên hàng / ĐVT (đã ghi nhận nhập kho theo hàng này). Hủy dòng rồi thêm dòng mới nếu cần.'
  // NSPT phụ trách CHỈ admin/người có quyền duyệt được giao (không auto-gán, không tự điền)
  const canPickNspt = can('purchase_order', 'approve')
  const employeeOptions = employees.map((e) => ({ value: e.full_name, label: e.full_name }))

  // Số ngày QĐ theo tên phân loại (mốc dài nhất, thiếu thì 15 ngày — khớp backend)
  const groupMap = useMemo(() => stdDaysMap(itemGroups), [itemGroups])
  // Ngày QĐ có hàng của 1 dòng = Ngày đặt hàng + số ngày QĐ của phân loại
  const qdDate = (it: any) => regulatedDate(groupMap, it?.item_group || '', po.order_date || '')
  // CR-083: Phân loại chọn từ Danh mục Phân loại (trước đây gõ tay nên sai chính tả -> sai ngày QĐ).
  const groupNames = useMemo(() => itemGroups.map((g) => String(g.name || '')).filter(Boolean), [itemGroups])
  // Dòng cũ có thể ghi lệch hoa/thường so với danh mục -> hiện đúng cách viết của danh mục.
  const canonGroup = (v: any) => groupNames.find((n) => normGroup(n) === normGroup(v)) || String(v || '').trim()
  // Phân loại đã bị bỏ khỏi danh mục vẫn phải thấy được, không thì mở dòng cũ là mất chữ.
  const groupOptions = (v: any) => {
    const cur = canonGroup(v)
    return !cur || groupNames.includes(cur) ? groupNames : [{ value: cur, label: `${cur} (ngoài danh mục)` }, ...groupNames]
  }
  // Tự tính lại cờ Đơn gấp khi dữ liệu nguồn (ngày đặt / dòng hàng) đổi. KHÔNG chạy lúc mở đơn (loadAll không qua đây) → giữ đè tay.
  const recalcUrgent = (next: any) => {
    if (Object.keys(groupMap).length === 0) return next   // chưa nạp danh mục → chưa tính
    const u = computeUrgent(next.items || [], next.order_date, groupMap)
    return u === !!next.is_urgent ? next : { ...next, is_urgent: u }
  }
  // Đơn MỚI: tự tính cờ gấp khi có đủ dữ liệu (kể cả tạo từ YCMH). Đơn cũ dùng setter khi user sửa.
  useEffect(() => {
    if (!isNew || Object.keys(groupMap).length === 0) return
    setPo((s: any) => { const u = computeUrgent(s.items || [], s.order_date, groupMap); return s.is_urgent === u ? s : { ...s, is_urgent: u } })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isNew, groupMap, po.order_date, po.items])

  const setH = (k: string, v: any) =>
    setPo((s: any) => (k === 'order_date' ? recalcUrgent({ ...s, order_date: v }) : { ...s, [k]: v }))
  const items = po.items || []
  // CR-073: thiếu thông tin bắt buộc thì chặn ngay tại nút Gửi duyệt (backend chặn lần nữa)
  // CR-095: kiểm thêm bộ trường bắt buộc của TỪNG dòng hàng, và nói rõ dòng nào thiếu ô nào.
  const lineIssues = items
    .map((it: any, i: number) => ({ i: i + 1, code: it.product_code || 'chưa có mã hàng', missing: missingLineFields(it) }))
    .filter((x: any) => x.missing.length > 0)
  const submitBlockReason = !(po.supplier_code || '').trim()
    ? 'Chưa chọn nhà cung cấp — không gửi duyệt được'
    : items.length === 0
      ? 'Đơn chưa có dòng hàng — không gửi duyệt được'
      : lineIssues.length > 0
        ? 'Chưa gửi duyệt được — còn thiếu ' + lineIssues.map((x: any) => `dòng ${x.i} (${x.code}): ${x.missing.join(', ')}`).join('; ')
        : ''
  // Mã hàng đang lưu trên server — mốc để chỉ chặn TRÙNG MỚI (xem utils/lines.newDupCodes)
  const savedCodes = useRef<string[]>([])
  const dupCodes = useMemo(() => newDupCodes(items.map((it: any) => it.product_code || ''), savedCodes.current), [items])
  const setItem = (i: number, patch: any) =>
    setPo((s: any) => recalcUrgent({ ...s, items: s.items.map((it: any, idx: number) => idx === i ? { ...it, ...patch } : it) }))
  const addItems = (n = 1) => setPo((s: any) => recalcUrgent({ ...s, items: [...(s.items || []), ...Array.from({ length: n }, () => ({ ...emptyItem }))] }))
  const delItem = (i: number) => setPo((s: any) => recalcUrgent({ ...s, items: s.items.filter((_: any, idx: number) => idx !== i) }))
  const dupItem = (i: number) => setPo((s: any) => {
    const src = s.items[i]
    // Dòng mới: reset tiến độ + tiền + lần giao (chưa lưu nên chưa có id/công nợ)
    const copy = { ...src, id: undefined, qty_received: 0, qty_remaining: 0, line_status: '', deliveries: [],
      progress_status: 'Chưa đặt hàng', pause_reason: '', status_before_pause: '',
      goods_total: 0, paid_total: 0, remaining_total: 0 }
    const items = [...s.items]; items.splice(i + 1, 0, copy); return recalcUrgent({ ...s, items })
  })

  // Thành tiền đơn hàng = SL đặt × đơn giá × (1+VAT) — cập nhật ngay khi nhập SL/đơn giá
  const orderAmount = (it: any) => (Number(it.qty_order) || 0) * (Number(it.price) || 0) * (1 + (Number(it.vat) || 0) / 100)
  const orderTotal = items.reduce((s: number, it: any) => s + orderAmount(it), 0)
  // Tiền theo ĐƠN HÀNG (SL đặt × đơn giá) — cập nhật ngay khi nhập SL/đơn giá
  const orderBeforeTax = items.reduce((s: number, it: any) => s + (Number(it.qty_order) || 0) * (Number(it.price) || 0), 0)
  const orderTax = orderTotal - orderBeforeTax
  const shippingTotal = items.reduce((s: number, it: any) => s + (it.deliveries || []).reduce((a: number, d: any) => a + (Number(d.shipping_amount) || 0), 0), 0)

  // ---- bao-CR-319: tiền tệ + loại đơn ----
  const isImport = Number(po.order_type || ORDER_TYPE_DOMESTIC) === ORDER_TYPE_IMPORT
  const poCurrency = (po.currency || '').trim() || DEFAULT_CURRENCY
  // Đồng tiền / tỷ giá THỰC của một dòng: dòng để trống thì chạy theo đơn (backend cũng vậy)
  const lineCurrency = (it: any) => (it?.currency || '').trim() || poCurrency
  const lineRate = (it: any) => Number(it?.exchange_rate) || Number(po.exchange_rate) || 1
  // Đơn thuần VNĐ thì giấu hết phần tỷ giá đi — đơn trong nước chiếm gần hết số phiếu,
  // bày thêm hai ô luôn bằng 1 chỉ làm rối màn hình.
  const showCurrency = isImport || items.some((it: any) => lineCurrency(it) !== DEFAULT_CURRENCY)
  // Tổng QUY ĐỔI — số này mới so sánh được với công nợ và với các đơn khác
  const orderBaseTotal = items.reduce((s: number, it: any) => s + orderAmount(it) * lineRate(it), 0)
  // Tiền ngoại tệ KHÔNG làm tròn về đồng: 7.530,45 USD mà cắt phần lẻ là mất 400 nghìn đồng.
  const fmtAmt = (n: any) => (showCurrency ? fmtPrice(n) : fmtVND(n))

  // ---- bao-CR-319 P3: chi phí lô hàng nhập khẩu ----
  const importCosts: any[] = po.import_costs || []
  // Hóa đơn cước, tờ khai thuế, phí lưu bãi đều về SAU ngày duyệt, nên bảng này mở cả khi
  // đơn đã duyệt (backend cũng cho — xem block_edit_approved_order).
  const costEditable = headerEditable || afterApproveEditable
  const setCost = (i: number, patch: any) =>
    setPo((s: any) => ({ ...s, import_costs: (s.import_costs || []).map((c: any, idx: number) => idx === i ? { ...c, ...patch } : c) }))
  const addCost = () => setPo((s: any) => ({ ...s, import_costs: [...(s.import_costs || []), { ...emptyImportCost }] }))
  const delCost = (i: number) => setPo((s: any) => ({ ...s, import_costs: (s.import_costs || []).filter((_: any, idx: number) => idx !== i) }))
  const costCurrency = (c: any) => (c?.currency || '').trim() || poCurrency
  // Nhắc lại luật của backend: chi phí ghi bằng ĐÚNG đồng tiền của đơn thì theo tỷ giá đơn;
  // khác đồng tiền (cước nội địa trả bằng VNĐ trong đơn USD) thì để 1 chứ không mượn tỷ giá đơn.
  const costRate = (c: any) => Number(c?.exchange_rate) || (costCurrency(c) === poCurrency ? (Number(po.exchange_rate) || 1) : 1)
  // Quy đổi VNĐ, ĐÃ GỒM VAT — khớp import_cost_base() ở backend
  const costBase = (c: any) => (Number(c?.amount) || 0) * (1 + (Number(c?.vat) || 0) / 100) * costRate(c)
  const costTotal = importCosts.reduce((s: number, c: any) => s + costBase(c), 0)
  const landedTotal = orderBaseTotal + costTotal
  // Gom theo loại chi phí và theo NCC — hai câu hỏi thường gặp nhất khi soát một lô nhập
  const groupCosts = (key: (c: any) => string) => {
    const m = new Map<string, { label: string, total: number, count: number }>()
    for (const c of importCosts) {
      const k = key(c)
      const cur = m.get(k) || { label: k, total: 0, count: 0 }
      cur.total += costBase(c); cur.count += 1
      m.set(k, cur)
    }
    return [...m.values()].sort((a, b) => b.total - a.total)
  }
  // P4: kết quả chia về dòng hàng do backend tính từ dữ liệu ĐÃ LƯU (xem panel bên dưới)
  const allocation: any = po.import_cost_allocation || null
  // Cách "Nhập tay": số gõ nằm trong `c.manual_allocation` {id dòng hàng: số tiền}, chỉ có hiệu
  // lực khi bấm Lưu của đơn. Ba hàm dưới dùng chung cho ô nhập, dải báo lệch và chặn lúc Lưu.
  const isManualCost = (c: any) => Number(c?.allocation_method) === ALLOC_MANUAL
  const manualEntered = (c: any): number =>
    Object.values((c?.manual_allocation || {}) as Record<string, any>).reduce((s: number, v: any) => s + (Number(v) || 0), 0)
  const manualDiff = (c: any): number => manualEntered(c) - costBase(c)
  const setManualAmount = (i: number, itemId: any, value: string) =>
    setPo((s: any) => ({
      ...s,
      import_costs: (s.import_costs || []).map((c: any, idx: number) => {
        if (idx !== i) return c
        const next: Record<string, number> = { ...(c.manual_allocation || {}) }
        const n = Number(value)
        if (value === '' || !(n > 0)) delete next[String(itemId)]
        else next[String(itemId)] = n
        return { ...c, manual_allocation: next }
      }),
    }))
  // Đổi sang "Nhập tay" thì điền sẵn số đang chia (từ dữ liệu đã lưu) để thu mua chỉ sửa
  // vài dòng cần cân, khỏi gõ lại từ đầu. Khoản mới chưa Lưu thì chưa có số để điền.
  const switchAllocationMethod = (i: number, c: any, method: number) => {
    const patch: any = { allocation_method: method }
    if (method === ALLOC_MANUAL && !Object.keys(c.manual_allocation || {}).length && c.id && allocation?.lines) {
      const prefill: Record<string, number> = {}
      for (const ln of allocation.lines) {
        const hit = (ln.costs || []).find((x: any) => Number(x.cost_id) === Number(c.id))
        if (hit && Number(hit.base_amount) > 0) prefill[String(ln.item_id)] = Math.round(Number(hit.base_amount))
      }
      patch.manual_allocation = prefill
    }
    // Mở sẵn mọi dòng hàng ở bảng dưới để thấy ngay ô gõ số
    if (method === ALLOC_MANUAL && allocation?.lines?.length) {
      setAllocOpen(new Set(allocation.lines.map((ln: any, k: number) => Number(ln.item_id) || -(k + 1))))
    }
    setCost(i, patch)
  }
  const manualCostIndexes = importCosts.map((c: any, i: number) => (isManualCost(c) ? i : -1)).filter((i) => i >= 0)
  const costByType = groupCosts((c) => COST_TYPE_LABEL(c.cost_type))
  const costBySupplier = groupCosts((c) => (c.supplier_name || '').trim() || (c.supplier_code || '').trim() || '(chưa chọn NCC)')

  // ---- bao-CR-319 P5: công nợ + thanh toán chi phí lô hàng ----
  // Công nợ mỗi dòng chi phí do backend sinh khi đơn đã duyệt (sync_import_cost_payables) và
  // trả về ngay trên dòng (payable_id / paid_amount / remaining) — số ĐÃ LƯU, sửa bảng chưa Lưu
  // thì "còn lại" của dòng vẫn là số cũ. Cụm tổng theo NCC cũng lấy từ backend cho khỏi lệch.
  const costSummary: any = po.import_cost_summary || null
  const costPayReady = !isNew && PO_PAYABLE_STATUSES.includes(po.status) && can('payment_request', 'create')
  const costPaidTotal = Number(costSummary?.paid_total) || 0
  const costRemainingTotal = Math.max(costTotal - costPaidTotal, 0)
  const costPct = (n: number) => (orderBaseTotal > 0 ? `${(n / orderBaseTotal * 100).toFixed(1)}% so với tiền hàng` : '')
  const costPayable = (c: any) => costPayReady && Number(c.payable_id) > 0 && (Number(c.remaining) || 0) > 0.01
  const costPayableIds = importCosts.filter(costPayable).map((c: any) => Number(c.payable_id))
  const toggleCostSel = (payableId: number, on: boolean) =>
    setCostSel((s) => on ? Array.from(new Set([...s, payableId])) : s.filter((x) => x !== payableId))
  // Đưa id khoản nợ sang màn lập phiếu; backend tự tách mỗi NCC một phiếu (create_requests)
  const goCreatePayment = (payableIds: number[]) => {
    if (payableIds.length === 0) { toast.error('Chưa chọn khoản chi phí nào còn phải chi'); return }
    navigate(`/payment-requests/new?payables=${payableIds.join(',')}`)
  }

  // ---- deliveries within an item ----
  const setDelivery = (ii: number, di: number, patch: any) =>
    setPo((s: any) => ({
      ...s, items: s.items.map((it: any, idx: number) => idx !== ii ? it : {
        ...it, deliveries: it.deliveries.map((d: any, j: number) => j === di ? { ...d, ...patch } : d),
      }),
    }))
  const addDelivery = (ii: number) =>
    setPo((s: any) => ({
      ...s, items: s.items.map((it: any, idx: number) => idx !== ii ? it : {
        // Cam kết giao + Số ngày QĐ mặc định theo NGÀY QĐ CÓ HÀNG của phân loại; chỉ là GIÁ TRỊ
        // KHỞI TẠO, NSTM sửa lại theo cam kết thật của NCC được (backend không ép đồng bộ lại).
        ...it, deliveries: [...(it.deliveries || []), {
          ...emptyDelivery, delivery_no: (it.deliveries?.length || 0) + 1,
          warehouse_code: it.warehouse_code, ship_unit: it.unit,
          promised_date: qdDate(it), std_days: stdDaysOf(groupMap, it.item_group),
          regulated_date: qdDate(it),
        }],
      }),
    }))
  const delDelivery = (ii: number, di: number) =>
    setPo((s: any) => ({
      ...s, items: s.items.map((it: any, idx: number) => idx !== ii ? it : {
        ...it, deliveries: it.deliveries.filter((_: any, j: number) => j !== di),
      }),
    }))

  // Chọn SP → điền luôn các trường lấy từ danh mục, gồm "Xuất xứ / TSKT / chất liệu"
  // (spec) lấy từ Thông số kỹ thuật của sản phẩm; vẫn sửa tay lại được sau khi điền.
  const applyProduct = (i: number, p: any) => {
    if (!p) {
      setItem(i, { product_code: '', product_name: '', invoice_name: '', item_group: '', spec: '', fg_code: '', fg_name: '' })
      return
    }
    const currentIt = items[i] || {}
    const autoExp = !currentIt.expected_date ? regulatedDate(groupMap, p.item_group || '', po.order_date || '') : currentIt.expected_date
    setItem(i, {
      product_code: p.code, product_name: p.name, invoice_name: p.invoice_name || '',
      unit: p.unit || '', item_group: p.item_group || '', spec: p.specs || '',
      fg_code: p.hh_code || '', fg_name: p.hh_name || '',
      ...(autoExp ? { expected_date: autoExp } : {}),
    })
  }
  // Chọn 1 lần mua trước từ popup lịch sử → CHỈ điền vào state dòng hàng, KHÔNG tự lưu.
  // Không đụng NCC ở header: người dùng chủ động tham chiếu giá của bất kỳ NCC nào.
  // Ngoài giá, điền luôn phần "Chi tiết dòng" của lần mua đó; ô nào lịch sử để trống thì
  // GIỮ NGUYÊN giá trị đang có (đã điền từ danh mục SP hoặc người dùng tự gõ), không xóa trắng.
  const applyHistory = (i: number, h: HistoryPick) => {
    const patch: any = { unit: h.unit, qty_order: h.qty_order, price: h.price, vat: h.vat }
    const detail: Record<string, string> = {
      invoice_name: h.invoice_name, item_group: h.item_group, spec: h.spec,
      fg_code: h.fg_code, fg_name: h.fg_name, warehouse_code: h.warehouse_code, note: h.note,
    }
    Object.entries(detail).forEach(([k, v]) => { if ((v || '').trim()) patch[k] = v })
    setItem(i, patch)
    toast.success('Đã điền giá + thông tin chi tiết dòng từ lịch sử — bấm Lưu để ghi nhận')
  }

  const onPickSupplier = (code: string) => {
    const s = goodsSuppliers.find((x) => x.code === code)
    setPo((st: any) => ({
      ...st, supplier_code: code, supplier_name: s ? s.name : '',
      vat_rate: s ? (Number(s.vat) || st.vat_rate) : st.vat_rate,
      payment_terms: s ? (s.payment_terms || st.payment_terms) : st.payment_terms,
      // bao-CR-321 — điều khoản in đi theo NCC; NCC chưa khai thì giữ giá trị đang có trên đơn
      inspection_days: s ? (Number(s.inspection_days) || st.inspection_days) : st.inspection_days,
      return_days: s ? (Number(s.return_days) || st.return_days) : st.return_days,
      invoice_deadline: s ? (s.invoice_deadline || st.invoice_deadline) : st.invoice_deadline,
    }))
  }
  const onPickCarrier = (ii: number, di: number, val: string) => {
    // 3 trạng thái: '' = chưa chọn (name rỗng); '__self__' = tự vận chuyển (đánh dấu name); còn lại = NCC thật
    if (val === '__self__') { setDelivery(ii, di, { carrier_code: '', carrier_name: 'NCC tự vận chuyển' }); return }
    const c = carriers.find((x) => x.code === val)
    setDelivery(ii, di, { carrier_code: val, carrier_name: c ? c.name : '' })
  }

  // Tạo ĐMH từ YCMH: NCC ở YCMH là TEXT (đề xuất) → tự khớp với danh mục NCC (theo MST hoặc tên) để chọn sẵn dropdown
  useEffect(() => {
    if (!isNew || suppliers.length === 0 || po.supplier_code) return
    const fromPr = (location.state as any)?.fromPr
    if (!fromPr) return
    const goods = suppliers.filter((s) => s.supplier_type !== 'transport')
    const tax = (fromPr.supplier_tax_code || '').trim()
    const name = (fromPr.supplier_name || '').trim().toLowerCase()
    const match = (tax && goods.find((s) => (s.tax_code || '').trim() === tax))
      || (name && goods.find((s) => (s.name || '').trim().toLowerCase() === name))
    if (match) onPickSupplier(match.code)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isNew, suppliers, po.supplier_code])
  const onPickPr = (code: string) => {
    const pr = prList.find((p) => p.code === code)
    setPo((s: any) => ({ ...s, pr_code: code, ...(pr ? { department: pr.department || s.department, company_id: pr.company_id || s.company_id } : {}) }))
  }

  // Sau khi lưu: upload tệp đã chọn cho các lần giao MỚI (chưa có id). Map theo vị trí vì
  // backend giữ nguyên thứ tự deliveries (sort id asc, lần giao mới append cuối).
  async function uploadPendingDeliveryFiles(sentItems: any[], fresh: any) {
    for (let ii = 0; ii < sentItems.length; ii++) {
      const dels = sentItems[ii].deliveries || []
      for (let di = 0; di < dels.length; di++) {
        const pf: FileList | undefined = dels[di]._pendingFiles
        const newId = fresh?.items?.[ii]?.deliveries?.[di]?.id
        if (pf && pf.length && newId) {
          const fd = new FormData()
          fd.append('entity', 'delivery'); fd.append('entity_id', String(newId)); fd.append('purchase_order_id', String(id))
          Array.from(pf).forEach((f) => fd.append('files', f))
          await api.post('/api/attachments', fd)
        }
      }
    }
  }

  async function save() {
    const sentItems = items.filter((it: any) => it.product_name || it.product_code)
    // bao-CR-308: ĐMH ĐƯỢC PHÉP trùng mã (mua theo bộ chứng từ: cùng mã, khác lô / khác Tên
    // trên hóa đơn) — đồng bộ về YCMH cộng GỘP theo mã nên số vẫn đúng. Chỉ HỎI XÁC NHẬN
    // để chặn gõ nhầm mã; YCMH bên kia vẫn chặn cứng như cũ.
    if (dupCodes.length) {
      const ok = await askConfirm({
        title: 'Mã hàng trùng trên đơn',
        danger: false,
        confirmText: 'Vẫn lưu',
        cancelText: 'Quay lại sửa',
        message: `Các mã sau xuất hiện trên NHIỀU dòng: ${dupCodes.join(', ')}.\n\n`
          + 'Nếu cố ý tách dòng theo bộ chứng từ (cùng mã nhưng khác lô / khác Tên trên hóa đơn '
          + '/ số hóa đơn) thì bấm Vẫn lưu — tiến độ trên YCMH vẫn cộng gộp đúng theo mã.\n\n'
          + 'Nếu chỉ là gõ nhầm mã thì bấm Quay lại sửa.',
      })
      if (!ok) return
    }
    // Ràng buộc nhập liệu (để công nợ sinh đúng): có SL nhận thì phải có Ngày nhận; có cước thì phải chọn Đơn vị VC
    for (const it of sentItems) {
      for (const d of (it.deliveries || [])) {
        if ((Number(d.received_qty) || 0) > 0 && !(d.received_date || '').trim()) {
          toast.error(`Sản phẩm "${it.product_name}": lần giao có SL nhận thì phải nhập Ngày nhận`); return
        }
        if ((Number(d.shipping_amount) || 0) > 0 && !(d.carrier_code || '').trim() && !(d.carrier_name || '').trim()) {
          toast.error(`Sản phẩm "${it.product_name}": lần giao có cước thì phải chọn Đơn vị vận chuyển (hoặc chọn "NCC tự vận chuyển")`); return
        }
      }
    }
    // Dự kiến có hàng lệch với YCMH: hệ thống KHÔNG tự sửa ngược lên YCMH (đổi ngày ở đó là
    // việc của NSTM và phải kèm lý do) — chỉ báo popup cho người đang sửa đơn biết mà đối chiếu.
    const diffs = sentItems.filter((it: any) => {
      const cur = (it.expected_date || '').trim()
      const pr = (it.pr_expected_date || '').trim()
      return cur && pr && cur !== pr
    })
    if (diffs.length) {
      const dmy = (s: string) => { const [y, m, d] = s.split('-'); return `${d}/${m}/${y}` }
      const ok = await askConfirm({
        title: 'Lệch ngày dự kiến có hàng',
        danger: false,
        confirmText: 'Vẫn lưu',
        cancelText: 'Quay lại sửa',
        message: `Các dòng sau đang có ngày dự kiến khác với yêu cầu mua hàng ${po.pr_code}:\n`
          + diffs.map((it: any) => `• ${it.product_name || it.product_code}: YCMH ${dmy(it.pr_expected_date)} → đơn này ${dmy(it.expected_date)}`).join('\n')
          + '\n\nNgày trên YCMH sẽ KHÔNG tự đổi theo. Nếu cần đổi, vào phiếu YCMH sửa (phải kèm lý do).',
      })
      if (!ok) return
    }
    // Nhập tay: tổng các dòng phải bằng số quy đổi của khoản — backend cũng chặn (400), báo
    // sớm ở đây để người dùng khỏi mất công gửi.
    for (const c of importCosts) {
      if (!isManualCost(c)) continue
      const label = (c.description || '').trim() || COST_TYPE_LABEL(c.cost_type)
      if (manualEntered(c) <= 0) {
        toast.error(`Khoản "${label}" chọn Nhập tay nhưng chưa nhập số tiền dòng nào ở bảng Chi phí theo dòng hàng`); return
      }
      if (Math.abs(manualDiff(c)) > MANUAL_ALLOC_TOLERANCE) {
        toast.error(`Khoản "${label}": tổng nhập tay ${fmtVND(manualEntered(c))} phải bằng ${fmtVND(costBase(c))} (lệch ${fmtVND(manualDiff(c))})`); return
      }
    }
    const body: any = {
      misa_code: po.misa_code, pr_code: po.pr_code, survey_code: po.survey_code,
      company_id: Number(po.company_id) || 0, supplier_code: po.supplier_code, supplier_name: po.supplier_name,
      department: po.department, nspt: po.nspt, order_date: po.order_date,
      vat_rate: Number(po.vat_rate) || 0, payment_terms: po.payment_terms, is_urgent: po.is_urgent, note: po.note,
      // bao-CR-319 — loại đơn + tiền tệ + tờ khai. Thiếu mấy khóa này thì người dùng chọn
      // "Nhập khẩu" trên màn hình xong lưu lại vẫn ra đơn trong nước.
      order_type: Number(po.order_type) || ORDER_TYPE_DOMESTIC,
      currency: (po.currency || '').trim() || DEFAULT_CURRENCY,
      exchange_rate: Number(po.exchange_rate) || 1,
      customs_decl_no: po.customs_decl_no || '', customs_decl_date: po.customs_decl_date || '',
      // bao-CR-321 — điều khoản in
      inspection_days: Number(po.inspection_days) || 0, return_days: Number(po.return_days) || 0,
      invoice_deadline: (po.invoice_deadline || '').trim(),
      import_costs: importCosts.map((c: any) => ({
        id: c.id, cost_type: Number(c.cost_type) || 99, description: c.description || '',
        supplier_code: c.supplier_code || '', supplier_name: c.supplier_name || '',
        currency: c.currency || '', exchange_rate: Number(c.exchange_rate) || 0,
        amount: Number(c.amount) || 0, vat: Number(c.vat) || 0,
        allocation_method: Number(c.allocation_method) || ALLOC_BY_VALUE,
        allocation_target: c.allocation_target || '',
        manual_allocation: isManualCost(c) ? (c.manual_allocation || {}) : {},
        invoice_no: c.invoice_no || '',
        invoice_date: c.invoice_date || '', payment_due_date: c.payment_due_date || '',
        note: c.note || '',
      })),
      items: sentItems.map((it: any) => ({
        id: it.id, product_code: it.product_code, product_name: it.product_name, invoice_name: it.invoice_name,
        item_group: it.item_group, spec: it.spec, fg_code: it.fg_code, fg_name: it.fg_name, invoice_no: it.invoice_no,
        invoice_date: it.invoice_date || '', document_delivery_date: it.document_delivery_date || '',
        supplier_ready: !!it.supplier_ready,
        required_date: it.required_date, expected_date: it.expected_date || '',
        unit: it.unit, qty_request: Number(it.qty_request) || 0,
        qty_order: Number(it.qty_order) || 0,
        price: Number(it.price) || 0, vat: Number(it.vat) || 0, warehouse_code: it.warehouse_code, note: it.note,
        // Tiền tệ theo dòng + khối lượng/quy cách (bao-CR-319). Để trống đồng tiền / tỷ giá
        // là cố ý — backend chép xuống từ đơn.
        currency: it.currency || '', exchange_rate: Number(it.exchange_rate) || 0,
        weight_kg: Number(it.weight_kg) || 0, dimension: it.dimension || '',
        deliveries: (it.deliveries || []).map((d: any) => ({
          id: d.id, delivery_no: Number(d.delivery_no) || 1, warehouse_code: d.warehouse_code,
          carrier_code: d.carrier_code, carrier_name: d.carrier_name, ship_qty: Number(d.ship_qty) || 0,
          ship_unit: d.ship_unit, received_qty: Number(d.received_qty) || 0, promised_date: d.promised_date,
          expected_date: d.expected_date, received_date: d.received_date, std_days: Number(d.std_days) || 0,
          invoice_no: d.invoice_no, shipping_unit_price: Number(d.shipping_unit_price) || 0,
          shipping_amount: Number(d.shipping_amount) || 0, qc_result: d.qc_result,
          extra_request: d.extra_request, progress_note: d.progress_note,
        })),
      })),
    }
    try {
      if (isNew) { const r = await api.post(API, body); navigate(`/purchase-orders/${r.data.data.id}`) }
      else {
        const r = await api.patch(`${API}/${id}`, body)
        await uploadPendingDeliveryFiles(sentItems, r.data.data)
        toast.success('Đã lưu thành công'); loadAll()
      }
    } catch { /* interceptor đã toast lỗi */ }
  }

  async function action(path: string, payload: any = {}) {
    try { await api.post(`${API}/${id}/${path}`, payload); loadAll() }
    catch { /* interceptor đã toast lỗi */ }
  }

  // Tạo yêu cầu thanh toán từ ĐMH: lấy các khoản nợ HÀNG chưa trả đủ của đơn → chọn hóa đơn → tạo YCTT
  async function openPayModal() {
    try {
      // Lấy CẢ 2 luồng (hàng + vận chuyển), chỉ khoản chưa trả đủ
      const r = await api.get('/api/payables', { params: { po_code: po.code, year: 'all', page_size: 500 } })
      const list = (r.data.data.items || []).filter((p: any) => (Number(p.remaining) || 0) > 0.01)
      if (list.length === 0) {
        // Chưa có công nợ từ nhận hàng -> chuyển thẳng sang màn tạo YCTT với số tiền bằng tổng tiền PO
        const orderAmount = Number(po.order_total || po.total) || 0
        navigate('/payment-requests/new', {
          state: {
            supplier_code: po.supplier_code,
            company_id: po.company_id,
            source_type: 'goods',
            rows: [{
              id: 0,
              supplier_code: po.supplier_code,
              supplier_name: po.supplier_name,
              source_type: 'goods',
              po_code: po.code,
              invoice_no: po.misa_code || '',
              invoice_date: '',
              total: orderAmount,
              paid_amount: 0,
              remaining: orderAmount,
              amount: orderAmount,
            }],
          },
        })
        return
      }
      setPayables(list)
      setPaySel(list.filter((p: any) => p.source_type === 'goods').map((p: any) => p.id))   // mặc định CHỈ tick NCC sản xuất; vận chuyển / chi phí tự chọn thêm
      // Mở tab đầu tiên có khoản nợ, theo thứ tự hàng → vận chuyển → chi phí lô hàng
      setPayTab(PAY_TABS.map(([k]) => k).find((k) => list.some((p: any) => p.source_type === k)) || 'goods')
      setPayModal(true)
    } catch { /* interceptor đã toast lỗi */ }
  }
  // CR-025: chuyển sang màn "Tạo yêu cầu thanh toán" (dữ liệu đi kèm URL/state), chưa ghi DB.
  function createPaymentRequest() {
    const picked = payables.filter((p) => paySel.includes(p.id))
    if (picked.length === 0) { toast.error('Chưa chọn hóa đơn nào'); return }
    setPayModal(false)
    navigate(`/payment-requests/new?payables=${picked.map((p) => p.id).join(',')}`, { state: { rows: picked } })
  }

  // Cập nhật trạng thái tiến độ 1 dòng (Hủy/Tạm ngưng cần lý do); backend gate điều kiện + toast cột thiếu
  async function setProgress(item: any, status: string) {
    if (status === (item.progress_status || 'Chưa đặt hàng')) return
    let reason = ''
    if (status === 'Tạm ngưng' || status === 'Hủy đơn') {
      const r = await askPrompt({ title: status, message: `Lý do ${status.toLowerCase()}:`, confirmText: status })
      if (r === null || !r.trim()) return
      reason = r.trim()
    }
    try { await api.post(`${API}/${id}/items/${item.id}/progress`, { status, reason }); toast.success('Đã cập nhật trạng thái'); loadAll() }
    catch { /* interceptor đã toast lỗi (kèm cột còn thiếu) */ }
  }
  async function resumeProgress(item: any) {
    try { await api.post(`${API}/${id}/items/${item.id}/progress`, { status: '__resume__' }); toast.success('Đã tiếp tục đơn'); loadAll() }
    catch { /* interceptor đã toast lỗi */ }
  }
  // Trạng thái hồ sơ chứng từ (Task 10b) — cập nhật tay, cho phép CẢ khi đơn đã Hoàn thành.
  async function setDocStatus(value: string) {
    try { await api.patch(`${API}/${id}/document-status`, { document_status: value }); toast.success('Đã cập nhật hồ sơ chứng từ'); loadAll() }
    catch { /* interceptor đã toast lỗi */ }
  }

  // Đổi tiến độ 1 dòng theo máy trạng thái (chỉ qua các endpoint riêng, không qua form Lưu thường)
  async function loadDeliveryAtt(deliveryId: number) {
    const r = await api.get('/api/attachments', { params: { entity: 'delivery', entity_id: deliveryId } })
    setAttByDelivery((s) => ({ ...s, [deliveryId]: r.data.data }))
  }
  async function uploadDeliveryAtt(deliveryId: number, fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'delivery'); fd.append('entity_id', String(deliveryId)); fd.append('purchase_order_id', String(id))
    Array.from(fl).forEach((f) => fd.append('files', f))
    await api.post('/api/attachments', fd); loadDeliveryAtt(deliveryId)
  }

  function openDetail(i: number) {
    setEditingItemIdx(i)
    ;(items[i].deliveries || []).forEach((d: any) => { if (d.id) loadDeliveryAtt(d.id) })
  }

  // inline cell helpers for item table
  const txt = (i: number, k: string, w: number | string = 120) => (
    <input className="cell-input" style={{ width: w }} value={items[i][k] ?? ''} disabled={!headerEditable || lineLocked(items[i])} onChange={(e) => setItem(i, { [k]: e.target.value })} />
  )
  // Ô chữ dài (tên hàng…): xuống dòng + cao theo nội dung để đọc đủ, không cắt cụt
  const txtWrap = (i: number, k: string, w: number | string = '100%', lockOnReceived = false) => (
    <TextAreaAuto
      className="cell-input cell-textarea"
      style={{ width: w }}
      title={lockOnReceived && lineReceived(items[i]) ? PRODUCT_LOCK_HINT : undefined}
      value={items[i][k] ?? ''}
      disabled={!headerEditable || lineLocked(items[i]) || (lockOnReceived && lineReceived(items[i]))}
      onChange={(v) => setItem(i, { [k]: v })}
    />
  )
  const num = (i: number, k: string, w = 90) => {
    const dis = !headerEditable || lineLocked(items[i])
    if (k === 'price') {
      return (
        <CurrencyInput
          style={{ width: w }}
          value={items[i][k] ?? 0}
          disabled={dis}
          onChange={(val: number) => setItem(i, { [k]: val })}
        />
      )
    }
    return (
      <NumberInput decimals className="cell-input" style={{ width: w }} value={items[i][k] ?? 0} disabled={dis} onChange={(v: number) => setItem(i, { [k]: v })} />
    )
  }

  const title = isNew ? 'Tạo Đơn mua hàng' : `Đơn mua hàng ${po.code || ''}`
  const isLogShown = !isNew && logs.length > 0

  if (notFound) return <NotFound backTo="/purchase-orders" message="Không tìm thấy đơn mua hàng này hoặc bạn không có quyền truy cập." />

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/purchase-orders')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>{title}</h2>
        {!isNew && poBadge(po.status)}
        <span style={{ flex: 1 }} />
        {/* Tạo yêu cầu thanh toán: khi đơn đã duyệt */}
        {!isNew && ['approved', 'partial', 'received', 'completed'].includes(po.status) && can('payment_request', 'create')
          /* && (Number(po.unpaid_total) || 0) > 0.01 */ && (
          <button className="btn secondary" onClick={openPayModal}><i className="ti ti-receipt" />Tạo yêu cầu thanh toán</button>
        )}
        {/* ── Nhóm tiện ích + destructive (trái) ── */}
        {!isNew && can('purchase_order', 'print') && (
          <div style={{ position: 'relative' }}>
            <button className="btn ghost" onClick={() => setPrintOpen((o) => !o)}><i className="ti ti-printer" />In<i className="ti ti-chevron-down" style={{ fontSize: 14, marginLeft: 2 }} /></button>
            {printOpen && (
              <>
                <div onClick={() => setPrintOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 50 }} />
                <div style={{ position: 'absolute', top: '100%', right: 0, marginTop: 4, background: '#fff', border: '1px solid var(--border)', borderRadius: 8, boxShadow: '0 10px 30px rgba(27,37,89,.15)', zIndex: 51, minWidth: 190, whiteSpace: 'nowrap', overflow: 'hidden' }}>
                  <button className="btn ghost" style={{ display: 'flex', width: '100%', justifyContent: 'flex-start', border: 'none', borderRadius: 0 }} onClick={() => { window.open(`/print/purchase-order/${id}`, '_blank'); setPrintOpen(false) }}><i className="ti ti-printer" />In Đơn đặt hàng</button>
                  <button className="btn ghost" style={{ display: 'flex', width: '100%', justifyContent: 'flex-start', border: 'none', borderRadius: 0 }} onClick={() => { window.open(`/print/purchase-order-mh/${id}`, '_blank'); setPrintOpen(false) }}><i className="ti ti-file-invoice" />In Đơn mua hàng</button>
                  {/* bao-CR-319 P4: bản in riêng cho đơn nhập khẩu — 4 khối hàng hóa / chi phí /
                      phải trả theo NCC / chi phí chia về dòng hàng. Hai bản in thường giữ nguyên. */}
                  {isImport && (
                    <button className="btn ghost" style={{ display: 'flex', width: '100%', justifyContent: 'flex-start', border: 'none', borderRadius: 0 }} onClick={() => { window.open(`/print/purchase-order-import/${id}`, '_blank'); setPrintOpen(false) }}><i className="ti ti-ship" />In Đơn nhập khẩu</button>
                  )}
                  {/* bao-CR-314: chỉ hiện khi đơn có gắn YCMH. Bản in chỉ gồm những dòng hàng
                      có trên đơn này — không cần quyền đọc YCMH vì cổng là quyền in ĐƠN. */}
                  {(po.pr_code || '').trim() && (
                    <button className="btn ghost" style={{ display: 'flex', width: '100%', justifyContent: 'flex-start', border: 'none', borderRadius: 0 }} onClick={() => { window.open(`/print/purchase-request-from-po/${id}`, '_blank'); setPrintOpen(false) }}><i className="ti ti-file-text" />In Phiếu yêu cầu</button>
                  )}
                </div>
              </>
            )}
          </div>
        )}
        {!isNew && ['approved', 'partial', 'received'].includes(po.status) && can('purchase_order', 'cancel') && !items.some((it: any) => it.progress_status === 'Hoàn thành') && (
          <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={async () => { const r = await askPrompt({ title: 'Hủy đơn', message: 'Lý do hủy đơn (bắt buộc — khóa đơn, không sửa lại được):', confirmText: 'Hủy đơn' }); if (r !== null) { if (!r.trim()) { toast.error('Vui lòng nhập lý do hủy'); return } action('cancel', { reason: r }) } }}><i className="ti ti-ban" />Hủy</button>
        )}
        {!isNew && canDelete && can('purchase_order', 'delete') && (
          <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={async () => { if (await askConfirm({ message: 'Xóa đơn mua hàng này?' })) { await api.delete(`${API}/${id}`); navigate('/purchase-orders') } }}><i className="ti ti-trash" />Xóa đơn</button>
        )}
        {!isNew && <span style={{ width: 1, alignSelf: 'stretch', background: 'var(--border)', margin: '2px 4px' }} />}
        {/* ── Nhóm workflow + Lưu (phải) ── */}
        {!isNew && ['draft', 'rejected'].includes(po.status) && can('purchase_order', 'write') && (
          <button
            className="btn secondary"
            style={submitBlockReason ? { opacity: 0.75, cursor: 'pointer' } : undefined}
            title={submitBlockReason || undefined}
            onClick={() => {
              if (submitBlockReason) {
                toast.error(submitBlockReason)
                return
              }
              action('submit')
            }}
          >
            <i className="ti ti-send" />Gửi duyệt
          </button>
        )}
        {!isNew && po.status === 'submitted' && can('purchase_order', 'approve') && (
          <>
            <button className="btn" onClick={() => action('approve')}><i className="ti ti-check" />Duyệt</button>
            <button className="btn ghost" style={{ color: '#d97706', borderColor: '#fcd34d' }} onClick={async () => { const r = await askPrompt({ title: 'Trả về', message: 'Lý do trả về (để người tạo sửa & gửi duyệt lại):', confirmText: 'Trả về' }); if (r !== null) action('return', { reason: r }) }}><i className="ti ti-corner-up-left" />Trả về</button>
            <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={async () => { const r = await askPrompt({ title: 'Từ chối đơn', message: 'Lý do từ chối (khóa đơn, không sửa lại được):', confirmText: 'Từ chối' }); if (r !== null) action('reject', { reason: r }) }}><i className="ti ti-ban" />Từ chối</button>
          </>
        )}
        {/* CR-108: đơn đã duyệt bị khóa nội dung — muốn sửa thì người DUYỆT hạ đơn về Nháp,
            sửa rồi gửi duyệt lại. Ẩn khi đã nhận hàng (backend cũng chặn): hàng đã vào kho
            và đã sinh công nợ thì không hạ đơn xuống được nữa. */}
        {!isNew && approved && can('purchase_order', 'approve') && !items.some((it: any) => Number(it.qty_received || 0) > 0) && (
          <button className="btn ghost" style={{ color: '#d97706', borderColor: '#fcd34d' }}
            onClick={async () => {
              const r = await askPrompt({ title: 'Hủy duyệt', message: 'Lý do hủy duyệt (đơn về Nháp để sửa, sau đó phải gửi duyệt lại):', confirmText: 'Hủy duyệt' })
              if (r === null) return
              if (!r.trim()) { toast.error('Vui lòng nhập lý do hủy duyệt'); return }
              action('unapprove', { reason: r.trim() })
            }}><i className="ti ti-lock-open" />Hủy duyệt</button>
        )}
        {!isNew && ['received', 'partial'].includes(po.status) && can('purchase_order', 'write') && (
          <button className="btn" onClick={async () => {
            // Đơn NK: backend chặn khi còn chi phí lô hàng chưa trả — nhắc trước để khỏi bấm rồi ăn lỗi
            const importHint = isImport && Number(po.import_cost_summary?.remaining_total || 0) > 0.01
              ? ` Đơn nhập khẩu còn ${fmtVND(po.import_cost_summary.remaining_total)} chi phí lô hàng chưa chi — hệ thống sẽ không cho hoàn thành.`
              : ''
            const message = (po.status === 'partial'
              ? 'Đơn mới nhận MỘT PHẦN. Xác nhận HOÀN THÀNH (chốt đơn dù còn thiếu)? Sau khi hoàn thành sẽ khóa, không chỉnh sửa được nữa.'
              : 'Xác nhận HOÀN THÀNH đơn mua hàng này? Sau khi hoàn thành sẽ khóa, không chỉnh sửa được nữa.') + importHint
            if (await askConfirm({ message, confirmText: 'Hoàn thành', danger: false })) action('complete')
          }}><i className="ti ti-circle-check" />Hoàn thành</button>
        )}
        {!isNew && po.status === 'completed' && can('purchase_order', 'write') && (
          <button className="btn ghost" onClick={async () => { if (await askConfirm({ message: 'Mở lại đơn đã hoàn thành để xử lý tiếp (nhập Số HĐ, tạo yêu cầu thanh toán, cập nhật tiến độ)? Đơn trở về trạng thái theo tiến độ nhận hàng.', confirmText: 'Mở lại' })) action('reopen') }}><i className="ti ti-lock-open" />Mở lại</button>
        )}
        {(headerEditable || deliveryEditable) && can('purchase_order', isNew ? 'create' : 'write') && (
          <button className="btn" onClick={save} style={{ height: 40, padding: '0 22px', fontSize: 14.5, fontWeight: 700 }}><i className="ti ti-device-floppy" />{isNew ? 'Tạo' : 'Lưu'}</button>
        )}
      </div>

      <div className={isLogShown ? 'detail-grid' : ''}>
        <div style={{ minWidth: 0 }}>
          {/* Thông tin chung */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title">Thông tin chung</h3>
            <div className="form-grid">
              <div className="form-row"><label>Mã PO</label><input value={po.code || ''} disabled placeholder="Tự sinh khi tạo" /></div>
              <div className="form-row">
                <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>Mã PYC nguồn
                  {(() => {
                    const prId = prList.find((p) => p.code === po.pr_code)?.id
                    return prId ? (
                      <i className="ti ti-external-link clickable" title="Mở phiếu yêu cầu mua hàng"
                        style={{ color: 'var(--teal)' }} onClick={() => navigate(`/purchase-requests/${prId}`)} />
                    ) : null
                  })()}
                </label>
                <input list="po-pyc-list" placeholder="Nhập/chọn mã PYC…" value={po.pr_code || ''} disabled={!headerEditable} onChange={(e) => onPickPr(e.target.value)} />
                <datalist id="po-pyc-list">{prList.map((p) => <option key={p.id} value={p.code}>{p.purpose || ''}</option>)}</datalist>
              </div>
              {/* Mã đơn MISA: kế toán đối chiếu số trên phần mềm MISA nên thường điền/sửa SAU khi
                  đơn đã duyệt. Mở ô này cả khi đơn đã duyệt (backend cũng cho, xem
                  ORDER_FIELDS_EDITABLE_AFTER_APPROVAL ở purchase_order/service.py). */}
              <div className="form-row"><label>Mã đơn MISA</label><input value={po.misa_code || ''} placeholder="(nếu có)" disabled={!headerEditable && !afterApproveEditable} onChange={(e) => setH('misa_code', e.target.value)} /></div>
              <div className="form-row"><label>Công ty nhận HĐ <span style={{ color: 'var(--red)' }}>*</span></label>
                <SearchSelect value={po.company_id ? String(po.company_id) : ''} disabled={!headerEditable} placeholder="Chọn/tìm công ty…"
                  options={companies.map((c) => ({ value: String(c.id), label: c.name }))}
                  onChange={(v) => setH('company_id', Number(v) || 0)} />
              </div>
              <div className="form-row"><label>Nhà cung cấp bán hàng <span style={{ color: 'var(--red)' }}>*</span></label>
                <SearchSelect value={po.supplier_code || ''} disabled={!headerEditable} placeholder="Chọn/tìm NCC…"
                  options={goodsSuppliers.map((s) => ({ value: s.code, label: `${s.code} — ${s.name}` }))}
                  onChange={(v) => onPickSupplier(v)} />
              </div>
              <div className="form-row"><label>Ngày đặt hàng</label><DateInput value={po.order_date || ''} disabled={!headerEditable} onChange={(v) => setH('order_date', v)} /></div>
              {/* bao-CR-319 — Loại đơn. Đổi sang Nhập khẩu là mở thêm cụm tờ khai hải quan
                  và cột tiền tệ ở bảng dòng hàng. */}
              <div className="form-row"><label>Loại đơn</label>
                <select value={String(po.order_type || ORDER_TYPE_DOMESTIC)} disabled={!headerEditable}
                  onChange={(e) => {
                    const v = Number(e.target.value) || ORDER_TYPE_DOMESTIC
                    // Chuyển về đơn trong nước thì trả loại tiền về VNĐ luôn, không để lại
                    // tỷ giá cũ nằm im rồi nhân sai tiền ở lần lưu sau. Bảng chi phí nhập
                    // khẩu cũng dọn theo — giữ lại là bảng bị ẩn mà tiền vẫn nằm trong DB.
                    setPo((s: any) => v === ORDER_TYPE_DOMESTIC
                      ? { ...s, order_type: v, currency: DEFAULT_CURRENCY, exchange_rate: 1, import_costs: [] }
                      // Đổi sang nhập khẩu là VAT dòng hàng về 0 NGAY trên màn hình, để số
                      // người dùng nhìn thấy khớp với số backend sẽ lưu (xem _save_items).
                      : { ...s, order_type: v, items: (s.items || []).map((it: any) => ({ ...it, vat: 0 })) })
                  }}>
                  {ORDER_TYPE_OPTS.map(([v, label]) => <option key={v} value={String(v)}>{label}</option>)}
                </select>
              </div>
              {isImport && (
                <div className="form-row"><label>Đồng tiền đơn hàng</label>
                  <input list="po-currency-list" value={po.currency || ''} disabled={!headerEditable}
                    placeholder={DEFAULT_CURRENCY}
                    onChange={(e) => setH('currency', e.target.value.toUpperCase())} />
                  <datalist id="po-currency-list">{CURRENCY_OPTS.map((c) => <option key={c} value={c} />)}</datalist>
                </div>
              )}
              {isImport && poCurrency !== DEFAULT_CURRENCY && (
                <div className="form-row"><label>Tỷ giá <span style={{ color: 'var(--muted)', fontWeight: 400 }}>(1 {poCurrency} = ? đ)</span></label>
                  <NumberInput value={po.exchange_rate ?? 1} disabled={!headerEditable} maxDecimals={6}
                    onChange={(v: any) => setH('exchange_rate', v)} />
                </div>
              )}
              {isImport && (
                <div className="form-row"><label>Số tờ khai hải quan</label>
                  <input value={po.customs_decl_no || ''} placeholder="(nhập sau khi thông quan)"
                    disabled={!headerEditable && !afterApproveEditable}
                    onChange={(e) => setH('customs_decl_no', e.target.value)} />
                </div>
              )}
              {isImport && (
                <div className="form-row"><label>Ngày tờ khai</label>
                  <DateInput value={po.customs_decl_date || ''} disabled={!headerEditable && !afterApproveEditable}
                    onChange={(v) => setH('customs_decl_date', v)} />
                </div>
              )}
              <div className="form-row"><label>NSPT phụ trách</label>
                <SearchSelect value={po.nspt || ''} options={employeeOptions}
                  onChange={(v) => setH('nspt', v)} disabled={!headerEditable || !canPickNspt}
                  placeholder={canPickNspt ? 'Chọn nhân sự phụ trách' : ''} />
              </div>
              <div className="form-row"><label>Hình thức thanh toán NCC</label><SearchSelect value={po.payment_terms || ''} options={PAYMENT_TERMS_OPTIONS} disabled={!headerEditable} placeholder="Chọn hình thức thanh toán…" onChange={(v) => setH('payment_terms', v)} /></div>
              {/* bao-CR-321 — điều khoản in (mục 2 + mục 5 bản in). Tự chép từ NCC khi chọn, sửa riêng
                  từng đơn lúc còn nháp; khóa sau duyệt như hình thức thanh toán. Trống = mặc định cũ. */}
              <div className="form-row"><label>Số ngày kiểm tra hàng (bản in)</label>
                <input type="number" min="0" max="365" value={po.inspection_days || ''} disabled={!headerEditable} placeholder="Trống = 15 ngày"
                  onChange={(e) => setH('inspection_days', e.target.value === '' ? 0 : Number(e.target.value))} />
              </div>
              <div className="form-row"><label>Số ngày thu hồi / đổi trả (bản in)</label>
                <input type="number" min="0" max="365" value={po.return_days || ''} disabled={!headerEditable} placeholder="Trống = 07 ngày"
                  onChange={(e) => setH('return_days', e.target.value === '' ? 0 : Number(e.target.value))} />
              </div>
              <div className="form-row"><label>Thời gian nhận hóa đơn (bản in)</label>
                <input value={po.invoice_deadline || ''} maxLength={255} disabled={!headerEditable} placeholder="Trống = Chậm nhất 24h kể từ khi nhận hàng"
                  onChange={(e) => setH('invoice_deadline', e.target.value)} />
              </div>
              <div className="form-row"><label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                <input type="checkbox" checked={!!po.is_urgent} disabled={!headerEditable} onChange={(e) => setH('is_urgent', e.target.checked)} style={{ width: 18, height: 18 }} /> Đơn gấp
              </label></div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Ghi chú</label><textarea value={po.note || ''} disabled={!headerEditable} onChange={(e) => setH('note', e.target.value)} /></div>
            </div>
          </div>

          {/* Dòng hàng */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
              <h3 className="sec-title" style={{ margin: 0, border: 'none', padding: 0 }}>Dòng hàng</h3>
              {headerEditable && (
                <div style={{ display: 'flex', gap: 8 }}>
                  <button className="btn ghost" onClick={() => addItems(1)} style={{ height: 32, fontSize: 13 }}><i className="ti ti-plus" />Thêm dòng</button>
                  <button className="btn ghost" onClick={async () => { const n = await askPrompt({ message: 'Thêm bao nhiêu dòng?', defaultValue: '3' }); if (n !== null) addItems(Math.max(1, parseInt(n || '0') || 0)) }} style={{ height: 32, fontSize: 13 }}><i className="ti ti-rows" />Thêm nhiều</button>
                </div>
              )}
            </div>
            {/* CR-095: nêu trước dòng nào còn thiếu ô nào, thay vì để người lập bấm Gửi
                duyệt rồi mới nhận lỗi. Chỉ hiện lúc còn sửa được — đơn đã trình/đã duyệt
                mà kêu thiếu thì không có đường sửa, chỉ làm rối. */}
            {headerEditable && lineIssues.length > 0 && (
              <div style={{ marginBottom: 12, padding: '8px 12px', borderRadius: 8, background: '#fffbeb',
                border: '1px solid #fcd34d', color: '#92400e', fontSize: 12.5 }}>
                <div style={{ fontWeight: 600, marginBottom: 2 }}>
                  <i className="ti ti-alert-triangle" /> Còn thiếu thông tin bắt buộc — chưa gửi duyệt được
                </div>
                {lineIssues.map((x: any) => (
                  <div key={x.i}>Dòng {x.i} ({x.code}): {x.missing.join(', ')}</div>
                ))}
                <div style={{ marginTop: 2, opacity: .85 }}>Bấm <i className="ti ti-pencil" /> ở cột Hành động để mở Chi tiết dòng và điền.</div>
              </div>
            )}
            {/* CR-108: nói rõ vì sao bảng bị khóa và mở lại bằng cách nào — nếu không,
                người dùng tưởng hỏng màn hình rồi gọi hỗ trợ. */}
            {afterApproveEditable && (
              <div style={{ marginBottom: 12, padding: '8px 12px', borderRadius: 8, background: '#eff6ff',
                border: '1px solid #bfdbfe', color: '#1e40af', fontSize: 12.5 }}>
                <i className="ti ti-lock" /> Đơn đã duyệt — nội dung đã duyệt bị khóa. Mã đơn MISA vẫn sửa được ở phần Thông tin chung.
                Mở <i className="ti ti-pencil" /> Chi tiết dòng
                để sửa Tên trên hóa đơn, Ngày dự kiến có hàng, Kho nhận, Ghi chú, Ngày giao chứng từ cho KT và các lần giao hàng.
                {can('purchase_order', 'approve') && ' Cần đổi mã hàng / số lượng / đơn giá thì bấm "Hủy duyệt" rồi gửi duyệt lại.'}
              </div>
            )}
            <div className="items-scroll">
              <table className="items-table" style={{ minWidth: (showCurrency ? 1475 : 1345) - (isImport ? 189 : 0) }}>
                <thead>
                  <tr>
                    <th style={{ width: 36 }}>#</th>
                    <th style={{ width: 215 }}>Mã hàng</th>
                    <th style={{ minWidth: 265 }}>Tên hàng <span style={{ color: 'var(--red)' }}>*</span></th>
                    <th style={{ width: 90 }}>ĐVT</th>
                    <th style={{ width: 90 }}>SL đặt</th>
                    <th style={{ width: 105 }}>Đơn giá</th>
                    {/* bao-CR-319 — chỉ hiện khi đơn có ngoại tệ, đơn trong nước giữ nguyên bảng cũ */}
                    {showCurrency && <th style={{ width: 130 }}>Tiền tệ / Tỷ giá</th>}
                    {/* bao-CR-319: đơn NHẬP KHẨU ẩn VAT dòng hàng (luôn 0, thuế khai ở bảng Chi phí lô hàng) —
                        khách yêu cầu 09/09 để bảng khỏi thừa hai cột vô nghĩa */}
                    {!isImport && <th style={{ width: 64 }}>VAT%</th>}
                    {!isImport && <th style={{ width: 125 }}>Đơn giá (Sau VAT)</th>}
                    <th style={{ width: 150, background: '#fff3cd' }}>Thành tiền đơn hàng</th>
                    <th style={{ width: 150 }}>Tiến độ giao</th>
                    <th style={{ width: 170 }}>Trạng thái</th>
                    <th style={{ width: 120, textAlign: 'center' }}>Hành động</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((it: any, i: number) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      {/* bao-CR-308: trùng mã được phép (tách dòng theo bộ chứng từ) — chỉ tô vàng
                          cảnh báo cho dễ soát gõ nhầm, khi lưu sẽ hỏi xác nhận */}
                      <td
                        style={dupCodes.includes((it.product_code || '').trim())
                          ? { minWidth: 215, background: '#fef3c7', boxShadow: 'inset 3px 0 0 #f59e0b' } : { minWidth: 215 }}
                        title={dupCodes.includes((it.product_code || '').trim())
                          ? 'Mã hàng này đang có ở dòng khác — nếu cố ý tách dòng theo bộ chứng từ thì vẫn lưu được'
                          : (lineReceived(it) ? PRODUCT_LOCK_HINT : undefined)}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            {/* CR-108: không cho chỉnh thì hiện chữ + nút copy — ô react-select
                                bị disabled không bôi đen được, người dùng không lấy mã ra tra cứu được. */}
                            {(!headerEditable || lineLocked(it) || lineReceived(it))
                              ? <CopyText value={it.product_code} title={it.product_name || undefined} />
                              : <ProductPicker compact code={it.product_code} name={it.product_name} onPick={(prod) => applyProduct(i, prod)} />}
                          </div>
                          {/* Tham chiếu giá đã mua trước đó — hiện ngay khi đã chọn mã hàng.
                              KHÔNG khóa theo quyền sửa: đơn đang chờ duyệt (CR-073 khóa sửa)
                              chính là lúc người duyệt cần đối chiếu giá cũ nhất. Dòng không
                              sửa được thì popup mở ở chế độ chỉ xem, không điền giá. */}
                          {it.product_code && (
                            <button className="icon-btn" style={{ flexShrink: 0 }}
                              title={historyReadOnly(it)
                                ? 'Lịch sử mua hàng gần nhất của mã hàng này (chỉ xem)'
                                : 'Lịch sử mua hàng gần nhất của mã hàng này'}
                              onClick={() => setHistoryIdx(i)}>
                              <i className="ti ti-history" style={{ fontSize: 16, color: 'var(--muted)' }} />
                            </button>
                          )}
                        </div>
                      </td>
                      <td>{txtWrap(i, 'product_name', '100%', true)}</td>
                      <td>
                        <select className="cell-input" style={{ width: 80 }} title={lineReceived(it) ? PRODUCT_LOCK_HINT : undefined} value={it.unit ?? ''} disabled={!headerEditable || lineLocked(it) || lineReceived(it)} onChange={(e) => setItem(i, { unit: e.target.value })}>
                          <option value="">—</option>{units.map((u) => <option key={u} value={u}>{u}</option>)}
                        </select>
                      </td>
                      <td>{num(i, 'qty_order', 80)}</td>
                      <td>{num(i, 'price', 95)}</td>
                      {showCurrency && (
                        <td style={{ textAlign: 'center', fontSize: 12 }}>
                          <div style={{ fontWeight: 600 }}>{lineCurrency(it)}</div>
                          {lineCurrency(it) !== DEFAULT_CURRENCY && (
                            <div style={{ color: 'var(--muted)' }} title="Tỷ giá quy đổi của dòng — sửa ở Chi tiết dòng">
                              × {fmtPrice(lineRate(it))}
                            </div>
                          )}
                        </td>
                      )}
                      {!isImport && <td style={{ textAlign: 'center' }}>{(Number(it.vat) || 0)}%</td>}
                      {/* bao-CR-307: đơn giá đã gồm VAT, làm tròn 2 số lẻ — 166.666,67 × 1,08 ra 180.000 chứ không phải 180.000,0036 */}
                      {!isImport && <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmtPrice(Math.round((Number(it.price) || 0) * (1 + (Number(it.vat) || 0) / 100) * 100) / 100)}</td>}
                      <td style={{ textAlign: 'right', fontWeight: 600, background: '#fff8e6' }}>{fmtVND(orderAmount(it))}</td>
                      <td style={{ textAlign: 'center', fontSize: 12 }}>
                        <div style={{ color: 'var(--muted)' }}>
                          {fmt(it.qty_received || 0)}/{fmt(it.qty_order || 0)}
                          {it.is_short_delivery && (
                            <span className="badge" style={{ marginLeft: 4, background: '#fef3c7', color: '#b45309', fontSize: 10, padding: '1px 5px' }} title="Tổng SL đã nhận nhỏ hơn SL đặt">Giao thiếu</span>
                          )}
                        </div>
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        {progressEditable && it.id && !['Hủy đơn', 'Hoàn thành'].includes(it.progress_status) ? (
                          it.progress_status === 'Tạm ngưng' ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'center' }}>
                              <span className="badge" style={{ background: PG_COLOR['Tạm ngưng'] + '22', color: PG_COLOR['Tạm ngưng'] }}>Tạm ngưng</span>
                              <button className="btn ghost" style={{ height: 26, fontSize: 11, padding: '0 8px' }} onClick={() => resumeProgress(it)}><i className="ti ti-player-play" />Tiếp tục</button>
                            </div>
                          ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'center' }}>
                              <span className="badge" title="Trạng thái tự động theo dữ liệu" style={{ background: (PG_COLOR[it.progress_status] || '#94a3b8') + '22', color: PG_COLOR[it.progress_status] || '#64748b' }}>{it.progress_status || 'Chưa đặt hàng'}</span>
                              <div style={{ display: 'flex', gap: 4 }}>
                                <button className="btn ghost" style={{ height: 24, fontSize: 11, padding: '0 6px' }} onClick={() => setProgress(it, 'Tạm ngưng')}><i className="ti ti-player-pause" />Tạm ngưng</button>
                                <button className="btn ghost" style={{ height: 24, fontSize: 11, padding: '0 6px', color: 'var(--red)' }} onClick={() => setProgress(it, 'Hủy đơn')}>Hủy</button>
                              </div>
                            </div>
                          )
                        ) : (
                          <span className="badge" title={!it.id ? 'Lưu đơn để cập nhật trạng thái cho dòng mới' : undefined} style={{ background: (PG_COLOR[it.progress_status] || '#94a3b8') + '22', color: PG_COLOR[it.progress_status] || '#64748b' }}>{it.progress_status || 'Chưa đặt hàng'}</span>
                        )}
                        {it.pause_reason && ['Tạm ngưng', 'Hủy đơn'].includes(it.progress_status) && (
                          <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 2 }} title={it.pause_reason}>Lý do: {it.pause_reason}</div>
                        )}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <div style={{ display: 'inline-flex', gap: 6 }}>
                          <button className="icon-btn" title={`Chi tiết & giao hàng (${it.deliveries?.length || 0} lần)`} onClick={() => openDetail(i)}>
                            <i className="ti ti-edit" style={{ fontSize: 16, color: 'var(--teal)' }} />
                          </button>
                          {headerEditable && (
                            <button className="icon-btn" title="Nhân bản dòng" onClick={() => dupItem(i)}>
                              <i className="ti ti-copy" style={{ fontSize: 16, color: 'var(--muted)' }} />
                            </button>
                          )}
                          {headerEditable && !lineLocked(it) && (
                            <button className="icon-btn" title="Xóa dòng" onClick={async () => { if (await askConfirm({ message: 'Xóa dòng này?' })) delItem(i) }}>
                              <i className="ti ti-trash" style={{ fontSize: 16, color: 'var(--red)' }} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                  {items.length === 0 && <tr><td colSpan={showCurrency ? 13 : 12} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Chưa có dòng nào</td></tr>}
                </tbody>
              </table>
            </div>
            {/* Panel tổng tiền: label trái / số phải thẳng cột, chỉ nhấn 1 dòng Tổng cộng */}
            <div style={{ marginTop: 14, display: 'flex', justifyContent: 'flex-end' }}>
              <div style={{ minWidth: 320, fontSize: 13.5 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 24, padding: '3px 0' }}>
                  <span style={{ color: 'var(--muted)' }}>Giá trị đặt hàng (trước thuế)</span>
                  <span style={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{fmtAmt(orderBeforeTax)}{showCurrency ? ` ${poCurrency}` : ''}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 24, padding: '3px 0' }}>
                  <span style={{ color: 'var(--muted)' }}>Tổng tiền thuế</span>
                  <span style={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{fmtAmt(orderTax)}{showCurrency ? ` ${poCurrency}` : ''}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 24, alignItems: 'baseline', borderTop: '1px solid var(--border)', marginTop: 6, paddingTop: 8, fontSize: 15.5, color: 'var(--navy)' }}>
                  <span style={{ fontWeight: 600 }}>Tổng cộng (sau thuế)</span>
                  <span style={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{fmtAmt(orderTotal)}{showCurrency ? ` ${poCurrency}` : ''}</span>
                </div>
                {/* bao-CR-319: đơn ngoại tệ phải nói rõ con số VNĐ — công nợ, yêu cầu thanh
                    toán và mọi báo cáo đều chạy trên số quy đổi này. */}
                {showCurrency && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', gap: 24, padding: '3px 0', color: 'var(--navy)' }}>
                    <span style={{ fontWeight: 600 }}>Quy đổi (VNĐ)</span>
                    <span style={{ fontWeight: 700, fontVariantNumeric: 'tabular-nums' }}>{fmtVND(orderBaseTotal)} đ</span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: 24, marginTop: 8, fontSize: 13.5, color: 'var(--muted)' }}>
                  <span>Tổng cước vận chuyển (riêng)</span>
                  <span style={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{fmtVND(shippingTotal)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* bao-CR-319 P3 — Chi phí lô hàng nhập khẩu. Bảng PHẲNG: mỗi dòng một khoản chi,
              mỗi khoản một nhà cung cấp riêng (hãng tàu, đơn vị khai thuê, kho bãi, và
              "Ngân sách nhà nước" cho các khoản thuế) — không lấy theo NCC của đơn. */}
          {isImport && (
            <div className="card" style={{ padding: 18, marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
                <h3 className="sec-title" style={{ margin: 0, border: 'none', padding: 0 }}>Chi phí lô hàng nhập khẩu</h3>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {/* P5: tick các dòng còn phải chi rồi lập YCTT — nhiều NCC thì backend tự tách phiếu */}
                  {costPayReady && costPayableIds.length > 0 && (
                    <button className="btn secondary" disabled={costSel.length === 0} onClick={() => goCreatePayment(costSel)} style={{ height: 32, fontSize: 13 }}>
                      <i className="ti ti-receipt" />Tạo YCTT{costSel.length ? ` (${costSel.length} dòng đã tick)` : ''}
                    </button>
                  )}
                  {costEditable && (
                    <button className="btn ghost" onClick={addCost} style={{ height: 32, fontSize: 13 }}><i className="ti ti-plus" />Thêm chi phí</button>
                  )}
                </div>
              </div>
              <div style={{ marginBottom: 12, padding: '8px 12px', borderRadius: 8, background: '#eff6ff',
                border: '1px solid #bfdbfe', color: '#1e40af', fontSize: 12.5 }}>
                <i className="ti ti-info-circle" /> VAT ở dòng hàng của đơn nhập khẩu luôn bằng 0 — thuế GTGT hàng nhập nộp ngân sách
                nhà nước theo tờ khai, khai thành một dòng ở bảng này. Chi phí vẫn thêm/sửa được sau khi đơn đã duyệt
                (hóa đơn cước, tờ khai thuế, phí lưu bãi đều có sau).
              </div>
              <div className="items-scroll">
                <table className="items-table" style={{ minWidth: costPayReady ? 2460 : 2420 }}>
                  <thead>
                    <tr>
                      {/* P5: cột tick chỉ có khi đơn đã duyệt (mới có công nợ để trả) */}
                      {costPayReady && (
                        <th style={{ width: 36, textAlign: 'center' }}>
                          <input type="checkbox" title="Tick mọi dòng còn phải chi" disabled={costPayableIds.length === 0}
                            checked={costPayableIds.length > 0 && costPayableIds.every((id) => costSel.includes(id))}
                            onChange={(e) => setCostSel(e.target.checked ? costPayableIds : [])} />
                        </th>
                      )}
                      <th style={{ width: 36 }}>#</th>
                      <th style={{ width: 185 }}>Loại chi phí</th>
                      <th style={{ minWidth: 320 }}>Diễn giải</th>
                      {/* Cách chia đứng ngay sau diễn giải để khỏi phải cuộn ngang mới thấy */}
                      <th style={{ width: 160 }}>Cách phân bổ</th>
                      <th style={{ width: 155 }}>Mã hàng chỉ định</th>
                      <th style={{ width: 230 }}>Nhà cung cấp</th>
                      <th style={{ width: 95 }}>Tiền tệ</th>
                      <th style={{ width: 110 }}>Tỷ giá</th>
                      <th style={{ width: 130 }}>Số tiền (trước thuế)</th>
                      <th style={{ width: 70 }}>VAT%</th>
                      <th style={{ width: 145, background: '#fff3cd' }}>Quy đổi (VNĐ)</th>
                      <th style={{ width: 120, textAlign: 'right' }}>Đã chi</th>
                      <th style={{ width: 120, textAlign: 'right' }}>Còn lại</th>
                      <th style={{ width: 110 }}>Số hóa đơn</th>
                      <th style={{ width: 130 }}>Ngày hóa đơn</th>
                      <th style={{ width: 130 }}>Hạn thanh toán</th>
                      <th style={{ width: 150 }}>Ghi chú</th>
                      <th style={{ width: 90, textAlign: 'center' }}>Hành động</th>
                    </tr>
                  </thead>
                  <tbody>
                    {importCosts.map((c: any, i: number) => (
                      <tr key={i}>
                        {costPayReady && (
                          <td style={{ textAlign: 'center' }}>
                            {costPayable(c)
                              ? <input type="checkbox" checked={costSel.includes(Number(c.payable_id))} onChange={(e) => toggleCostSel(Number(c.payable_id), e.target.checked)} />
                              : <span title={Number(c.payable_id) > 0 ? 'Đã chi đủ' : 'Chưa thành công nợ (dòng mới chưa Lưu, chưa chọn NCC hoặc số tiền 0)'} style={{ color: 'var(--muted)' }}>—</span>}
                          </td>
                        )}
                        <td>{i + 1}</td>
                        <td>
                          <select className="cell-input" value={String(Number(c.cost_type) || 99)} disabled={!costEditable}
                            onChange={(e) => {
                              const v = Number(e.target.value) || 99
                              // Khoản nộp nhà nước thì điền sẵn NCC "Ngân sách nhà nước" —
                              // chỉ khi ô NCC còn trống, không đè lựa chọn của người dùng.
                              const patch: any = { cost_type: v }
                              if (IMPORT_COST_TAX_TYPES.includes(v) && !(c.supplier_code || '').trim()) {
                                patch.supplier_code = STATE_BUDGET_SUPPLIER_CODE
                                patch.supplier_name = STATE_BUDGET_SUPPLIER_NAME
                              }
                              setCost(i, patch)
                            }}>
                            {IMPORT_COST_TYPE_OPTS.map(([v, label]) => <option key={v} value={String(v)}>{label}</option>)}
                          </select>
                        </td>
                        {/* Diễn giải xuống dòng + cao theo nội dung (như Tên hàng) để đọc đủ, không cắt cụt */}
                        <td><TextAreaAuto className="cell-input cell-textarea" style={{ width: '100%' }} value={c.description || ''} disabled={!costEditable}
                          placeholder="VD: Cước biển Thượng Hải – Cát Lái" onChange={(v) => setCost(i, { description: v })} /></td>
                        <td>
                          <select className="cell-input" value={String(Number(c.allocation_method) || ALLOC_BY_VALUE)} disabled={!costEditable}
                            onChange={(e) => switchAllocationMethod(i, c, Number(e.target.value) || ALLOC_BY_VALUE)}>
                            {ALLOCATION_OPTS.map(([v, label]) => <option key={v} value={String(v)}>{label}</option>)}
                          </select>
                        </td>
                        <td>
                          {isManualCost(c) ? (
                            isNew
                              ? <span style={{ fontSize: 11.5, color: '#b45309' }}>Lưu đơn trước rồi gõ số ở bảng Chi phí theo dòng hàng</span>
                              : <span style={{ fontSize: 11.5, color: Math.abs(manualDiff(c)) > MANUAL_ALLOC_TOLERANCE ? '#b91c1c' : '#15803d' }}>
                                  {manualEntered(c) > 0
                                    ? (Math.abs(manualDiff(c)) > MANUAL_ALLOC_TOLERANCE ? `Lệch ${fmtVND(manualDiff(c))}` : 'Đã khớp tổng')
                                    : 'Gõ số ở bảng Chi phí theo dòng hàng'}
                                </span>
                          ) : Number(c.allocation_method) === ALLOC_BY_PRODUCT ? (
                            <select className="cell-input" value={c.allocation_target || ''} disabled={!costEditable}
                              onChange={(e) => setCost(i, { allocation_target: e.target.value })}>
                              <option value="">— chọn mã hàng —</option>
                              {items.filter((it: any) => (it.product_code || '').trim())
                                .map((it: any, k: number) => <option key={k} value={it.product_code}>{it.product_code}</option>)}
                            </select>
                          ) : <span style={{ color: 'var(--muted)' }}>—</span>}
                        </td>
                        <td>
                          <SearchSelect variant="table" wrap value={c.supplier_code || ''} disabled={!costEditable} placeholder="Chọn/tìm NCC…"
                            options={suppliers.map((s) => ({ value: s.code, label: `${s.code} — ${s.name}` }))}
                            onChange={(v) => {
                              const s = suppliers.find((x) => x.code === v)
                              setCost(i, { supplier_code: v, supplier_name: s ? s.name : '' })
                            }} />
                        </td>
                        <td>
                          <select className="cell-input" value={costCurrency(c)} disabled={!costEditable}
                            onChange={(e) => {
                              const cur = e.target.value
                              // Về VNĐ là tỷ giá 1; đổi sang ngoại tệ thì xóa tỷ giá cũ để
                              // costRate() lấy lại mặc định thay vì giữ số của loại tiền trước.
                              setCost(i, { currency: cur, exchange_rate: cur === DEFAULT_CURRENCY ? 1 : 0 })
                            }}>
                            {Array.from(new Set([...CURRENCY_OPTS, costCurrency(c)])).map((cur) => <option key={cur} value={cur}>{cur}</option>)}
                          </select>
                        </td>
                        <td>
                          {costCurrency(c) === DEFAULT_CURRENCY
                            ? <span style={{ color: 'var(--muted)' }}>—</span>
                            : <NumberInput className="cell-input" value={c.exchange_rate || costRate(c)} maxDecimals={6} disabled={!costEditable}
                              onChange={(v: any) => setCost(i, { exchange_rate: v })} />}
                        </td>
                        <td><CurrencyInput value={c.amount ?? 0} disabled={!costEditable} onChange={(v: number) => setCost(i, { amount: v })} /></td>
                        <td><NumberInput className="cell-input" value={c.vat ?? 0} max={VAT_MAX} maxDecimals={VAT_DECIMALS} disabled={!costEditable}
                          onChange={(v: any) => setCost(i, { vat: v })} /></td>
                        <td style={{ textAlign: 'right', fontWeight: 600, background: '#fff8e6' }}>{fmtVND(costBase(c))}</td>
                        {/* P5: số đã chi / còn lại lấy từ công nợ ĐÃ LƯU của dòng; dòng chưa thành nợ thì còn lại = quy đổi hiện tại */}
                        <td style={{ textAlign: 'right', color: 'var(--green)' }}>{Number(c.payable_id) > 0 ? fmtVND(c.paid_amount) : '—'}</td>
                        <td style={{ textAlign: 'right', fontWeight: 600, color: Number(c.payable_id) > 0 && (Number(c.remaining) || 0) > 0.01 ? 'var(--red)' : 'var(--muted)' }}>
                          {Number(c.payable_id) > 0 ? fmtVND(c.remaining) : fmtVND(costBase(c))}
                        </td>
                        <td><input className="cell-input" value={c.invoice_no || ''} disabled={!costEditable} onChange={(e) => setCost(i, { invoice_no: e.target.value })} /></td>
                        <td><DateInput className="cell-input" style={{ width: 110 }} value={c.invoice_date || ''} disabled={!costEditable} onChange={(v) => setCost(i, { invoice_date: v })} /></td>
                        <td><DateInput className="cell-input" style={{ width: 110 }} value={c.payment_due_date || ''} disabled={!costEditable} onChange={(v) => setCost(i, { payment_due_date: v })} /></td>
                        <td><TextAreaAuto className="cell-input cell-textarea" style={{ width: '100%' }} value={c.note || ''} disabled={!costEditable} onChange={(v) => setCost(i, { note: v })} /></td>
                        <td style={{ textAlign: 'center' }}>
                          <div style={{ display: 'inline-flex', gap: 6 }}>
                            {/* Cây bút mở popup xem/sửa đủ ô của một khoản — bảng rộng 2.400px khó soát từng dòng */}
                            <button className="icon-btn" title="Chi tiết khoản chi phí" onClick={() => setEditingCostIdx(i)}>
                              <i className="ti ti-edit" style={{ fontSize: 16, color: 'var(--teal)' }} />
                            </button>
                            {costEditable && (
                              <button className="icon-btn" title="Xóa dòng chi phí"
                                onClick={async () => { if (await askConfirm({ message: 'Xóa dòng chi phí này?' })) delCost(i) }}>
                                <i className="ti ti-trash" style={{ fontSize: 16, color: 'var(--red)' }} />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {importCosts.length === 0 && <tr><td colSpan={costPayReady ? 19 : 18} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Chưa khai chi phí nào cho lô hàng này</td></tr>}
                  </tbody>
                </table>
              </div>

              {/* Các con số hay bị hỏi nhất khi soát một lô nhập: tiền hàng, tiền chi phí (kèm % so
                  tiền hàng), đã chi / còn phải chi (P5, chỉ khi đơn đã duyệt) và tổng giá trị lô về tới kho. */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 12, marginTop: 16 }}>
                {[
                  ['Tiền hàng (quy đổi)', orderBaseTotal, 'var(--navy)', ''],
                  ['Tổng chi phí nhập khẩu', costTotal, '#d97706', costPct(costTotal)],
                  ...(costPayReady || costPaidTotal > 0 ? [
                    ['Đã chi', costPaidTotal, 'var(--green)', costPct(costPaidTotal)],
                    ['Còn phải chi', costRemainingTotal, 'var(--red)', costPct(costRemainingTotal)],
                  ] : []),
                  ['Tổng giá trị lô hàng', landedTotal, 'var(--teal)', ''],
                ].map(([label, value, color, hint]: any) => (
                  <div key={label} style={{ border: '1px solid var(--border)', borderRadius: 10, padding: '12px 14px' }}>
                    <div style={{ fontSize: 12.5, color: 'var(--muted)', marginBottom: 4 }}>{label}</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color, fontVariantNumeric: 'tabular-nums' }}>{fmtVND(value)} đ</div>
                    {hint && <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 2 }}>{hint}</div>}
                  </div>
                ))}
              </div>

              {/* P5: khối THANH TOÁN theo nhà cung cấp — mỗi NCC một dòng tổng · đã chi · còn lại
                  + nút lập YCTT riêng (một phiếu chỉ một NCC). Số từ backend (import_cost_summary),
                  là dữ liệu ĐÃ LƯU; sửa bảng xong phải Lưu thì khối này mới đổi. */}
              {costPayReady && (costSummary?.by_supplier || []).length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 6 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--navy)' }}>Thanh toán chi phí theo nhà cung cấp</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)' }}>Mỗi yêu cầu thanh toán chỉ một nhà cung cấp — bấm nút ở dòng NCC để lập phiếu cho các khoản còn phải chi của NCC đó.</div>
                  </div>
                  <div className="items-scroll">
                    <table className="items-table" style={{ width: '100%', minWidth: 760 }}>
                      <thead><tr>
                        <th>Nhà cung cấp</th><th style={{ width: 70, textAlign: 'center' }}>Số khoản</th>
                        <th style={{ width: 140, textAlign: 'right' }}>Phải trả</th><th style={{ width: 140, textAlign: 'right' }}>Đã chi</th>
                        <th style={{ width: 140, textAlign: 'right' }}>Còn lại</th><th style={{ width: 150, textAlign: 'center' }}></th>
                      </tr></thead>
                      <tbody>
                        {(costSummary.by_supplier as any[]).map((r) => {
                          const ids: number[] = r.unpaid_payable_ids || []
                          return (
                            <tr key={r.supplier_code || r.supplier_name || '_'}>
                              <td>{(r.supplier_name || '').trim() || (r.supplier_code || '').trim() || <span style={{ color: 'var(--muted)' }}>(chưa chọn NCC — chưa thành công nợ)</span>}</td>
                              <td style={{ textAlign: 'center' }}>{r.count}</td>
                              <td style={{ textAlign: 'right' }}>{fmtVND(r.base_amount)}</td>
                              <td style={{ textAlign: 'right', color: 'var(--green)' }}>{fmtVND(r.paid_amount)}</td>
                              <td style={{ textAlign: 'right', fontWeight: 600, color: (Number(r.remaining) || 0) > 0.01 ? 'var(--red)' : 'var(--muted)' }}>{fmtVND(r.remaining)}</td>
                              <td style={{ textAlign: 'center' }}>
                                {ids.length > 0
                                  ? <button className="btn secondary" style={{ height: 28, fontSize: 12.5 }} onClick={() => goCreatePayment(ids)}><i className="ti ti-receipt" />Tạo YCTT</button>
                                  : <span className="badge ok">Đã chi đủ</span>}
                              </td>
                            </tr>
                          )
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
              {importCosts.length > 0 && (
                // Dồn các cụm tổng về mép phải, mỗi cụm rộng cố định để nhãn và số nằm sát nhau
                // (trước dùng grid auto-fit: chỉ còn một cụm là nó dàn hết bề ngang, nhãn một bên số một bên)
                <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'flex-end', gap: 32, marginTop: 16 }}>
                  {/* Đã có bảng thanh toán theo NCC ở trên thì thôi lặp lại cụm "Theo nhà cung cấp" */}
                  {[['Theo loại chi phí', costByType], ...(costPayReady ? [] : [['Theo nhà cung cấp', costBySupplier]])].map(([title, rows]: any) => (
                    <div key={title} style={{ width: 380, maxWidth: '100%' }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--navy)', marginBottom: 6 }}>{title}</div>
                      {rows.map((r: any) => (
                        <div key={r.label} style={{ display: 'flex', justifyContent: 'space-between', gap: 16, padding: '3px 0', fontSize: 13 }}>
                          <span style={{ color: 'var(--muted)' }}>{r.label} <span style={{ opacity: .7 }}>({r.count})</span></span>
                          <span style={{ fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>{fmtVND(r.total)} đ</span>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* bao-CR-319 P4 — Chi phí theo dòng hàng. Lồng NGƯỢC theo ý đại ca: dòng hàng là CHA,
              mở ra thấy từng khoản được phân bổ + cách chia + tỷ lệ; cuối là dòng tổng toàn đơn.
              Số do backend chia (allocate_import_costs) từ dữ liệu ĐÃ LƯU — không tính lại ở đây
              để màn hình, bản in và YCTT sau này cùng một con số. Riêng khoản chọn "Nhập tay" thì
              dòng con là ô gõ số tiền, có hiệu lực khi bấm Lưu của đơn. */}
          {isImport && !isNew && allocation && (
            <div className="card" style={{ padding: 18, marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, marginBottom: 10, flexWrap: 'wrap' }}>
                <h3 className="sec-title" style={{ margin: 0, border: 'none', padding: 0 }}>Chi phí theo dòng hàng</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>
                    Số chia lấy từ dữ liệu đã lưu, không ghi vào kho. Khoản chọn "Nhập tay" thì gõ số tiền từng dòng ở đây; sửa xong bấm Lưu mới có hiệu lực.
                  </div>
                  {allocation.lines?.length > 0 && (
                    <button type="button" className="btn ghost" style={{ padding: '3px 10px', fontSize: 12 }}
                      onClick={() => setAllocOpen(allocOpen.size >= allocation.lines.length
                        ? new Set()
                        : new Set(allocation.lines.map((ln: any, k: number) => Number(ln.item_id) || -(k + 1))))}>
                      {allocOpen.size >= allocation.lines.length ? 'Thu gọn' : 'Mở tất cả'}
                    </button>
                  )}
                </div>
              </div>
              {manualCostIndexes.length > 0 && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginBottom: 10 }}>
                  {manualCostIndexes.map((k) => {
                    const c = importCosts[k]
                    const ok = manualEntered(c) > 0 && Math.abs(manualDiff(c)) <= MANUAL_ALLOC_TOLERANCE
                    return (
                      <div key={k} style={{ background: ok ? '#f0fdf4' : '#fef2f2', border: `1px solid ${ok ? '#86efac' : '#fca5a5'}`,
                        borderRadius: 8, padding: '6px 12px', fontSize: 12.5, color: ok ? '#166534' : '#991b1b' }}>
                        Nhập tay khoản "{(c.description || '').trim() || COST_TYPE_LABEL(c.cost_type)}": đã nhập {fmtVND(manualEntered(c))} / {fmtVND(costBase(c))}
                        {ok ? ' — đã khớp tổng' : manualEntered(c) > 0 ? ` — lệch ${fmtVND(manualDiff(c))}, phải bằng nhau mới Lưu được` : ' — chưa nhập số tiền dòng nào'}
                      </div>
                    )
                  })}
                </div>
              )}
              {allocation.warnings?.length > 0 && (
                <div style={{ background: '#fff7ed', border: '1px solid #fdba74', borderRadius: 8, padding: '8px 12px', fontSize: 12.5, color: '#9a3412', marginBottom: 10 }}>
                  {allocation.warnings.map((w: string, i: number) => <div key={i}>{w}</div>)}
                </div>
              )}
              <div style={{ overflowX: 'auto' }}>
                <table className="table" style={{ minWidth: 820 }}>
                  <thead>
                    <tr>
                      <th style={{ width: 32 }} />
                      <th>Mã hàng</th><th>Tên hàng</th>
                      <th style={{ textAlign: 'right' }}>SL đặt</th>
                      <th style={{ textAlign: 'right' }}>KL (kg)</th>
                      <th style={{ textAlign: 'right' }}>Tiền hàng (quy đổi)</th>
                      <th style={{ textAlign: 'right' }}>Chi phí phân bổ</th>
                      <th style={{ textAlign: 'right' }}>Tổng giá trị</th>
                      <th style={{ textAlign: 'right' }}>Tỷ lệ chi phí</th>
                    </tr>
                  </thead>
                  <tbody>
                    {allocation.lines.map((ln: any, i: number) => {
                      const key = Number(ln.item_id) || -(i + 1)
                      const open = allocOpen.has(key)
                      const toggle = () => setAllocOpen((s) => { const n = new Set(s); n.has(key) ? n.delete(key) : n.add(key); return n })
                      return (
                        <Fragment key={key}>
                          <tr onClick={toggle} style={{ cursor: 'pointer' }}>
                            <td style={{ textAlign: 'center', color: 'var(--muted)' }}><i className={`ti ti-chevron-${open ? 'down' : 'right'}`} /></td>
                            <td style={{ fontWeight: 600 }}>{ln.product_code}</td>
                            <td>{ln.product_name}</td>
                            <td style={{ textAlign: 'right' }}>{fmtPrice(ln.qty_order)} {ln.unit}</td>
                            <td style={{ textAlign: 'right' }}>{ln.weight_kg ? fmtPrice(ln.weight_kg) : '-'}</td>
                            <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{fmtVND(ln.goods_base)}</td>
                            <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums', color: '#d97706', fontWeight: 600 }}>{fmtVND(ln.cost_base)}</td>
                            <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{fmtVND(ln.landed_base)}</td>
                            <td style={{ textAlign: 'right', color: 'var(--muted)' }}>{ln.goods_base > 0 ? `${(ln.cost_base / ln.goods_base * 100).toFixed(1)}%` : '-'}</td>
                          </tr>
                          {open && (
                            <tr>
                              <td />
                              <td colSpan={8} style={{ padding: '4px 0 10px' }}>
                                {(() => {
                                  // Khoản đang chọn "Nhập tay" trên bảng chi phí (kể cả chưa Lưu) hiện ô gõ số
                                  // thay cho số đã chia; khoản còn lại lấy nguyên số backend đã chia.
                                  const manualIds = new Set(manualCostIndexes.map((k) => Number(importCosts[k]?.id) || 0).filter((x) => x > 0))
                                  const savedRows = (ln.costs || []).filter((c: any) => !manualIds.has(Number(c.cost_id)))
                                  if (savedRows.length === 0 && manualCostIndexes.length === 0) {
                                    return <div style={{ fontSize: 12.5, color: 'var(--muted)', padding: '4px 8px' }}>Dòng này không được phân bổ khoản chi phí nào.</div>
                                  }
                                  return (
                                    <table className="table" style={{ background: '#fafbfd', fontSize: 12.5 }}>
                                      <thead>
                                        <tr>
                                          <th>Loại chi phí</th><th>Diễn giải</th><th>Nhà cung cấp</th>
                                          <th>Cách chia</th>
                                          <th style={{ textAlign: 'right' }}>Tỷ lệ</th>
                                          <th style={{ textAlign: 'right', width: 150 }}>Số tiền (đ)</th>
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {savedRows.map((c: any, j: number) => (
                                          <tr key={j}>
                                            <td>{c.cost_type_label}</td>
                                            <td>{c.description}</td>
                                            <td>{c.supplier_name || c.supplier_code}</td>
                                            <td>
                                              {c.effective_method === c.allocation_method
                                                ? c.allocation_method_label
                                                : <>{c.effective_method_label} <span style={{ color: '#b45309' }}>(chọn {String(c.allocation_method_label || '').toLowerCase()}, thiếu cơ sở)</span></>}
                                            </td>
                                            <td style={{ textAlign: 'right' }}>{(Number(c.ratio) * 100).toFixed(2)}%</td>
                                            <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums', fontWeight: 600 }}>{fmtVND(c.base_amount)}</td>
                                          </tr>
                                        ))}
                                        {manualCostIndexes.map((k) => {
                                          const c = importCosts[k]
                                          const raw = c.manual_allocation?.[String(ln.item_id)]
                                          const val = Number(raw) || 0
                                          const base = costBase(c)
                                          return (
                                            <tr key={`m${k}`} style={{ background: '#fffbeb' }}>
                                              <td>{COST_TYPE_LABEL(c.cost_type)}</td>
                                              <td>{c.description}</td>
                                              <td>{c.supplier_name || c.supplier_code}</td>
                                              <td>Nhập tay</td>
                                              <td style={{ textAlign: 'right' }}>{base > 0 && val > 0 ? `${(val / base * 100).toFixed(2)}%` : '-'}</td>
                                              <td style={{ textAlign: 'right' }}>
                                                <input type="number" min={0} step={1} className="cell-input" disabled={!costEditable} placeholder="0"
                                                  style={{ textAlign: 'right', width: 140, fontWeight: 600 }}
                                                  value={raw === undefined || raw === null ? '' : String(raw)}
                                                  onClick={(e) => e.stopPropagation()}
                                                  onChange={(e) => setManualAmount(k, ln.item_id, e.target.value)} />
                                              </td>
                                            </tr>
                                          )
                                        })}
                                      </tbody>
                                    </table>
                                  )
                                })()}
                              </td>
                            </tr>
                          )}
                        </Fragment>
                      )
                    })}
                    {allocation.lines.length === 0 && (
                      <tr><td colSpan={9} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Đơn chưa có dòng hàng</td></tr>
                    )}
                  </tbody>
                  <tfoot>
                    <tr style={{ fontWeight: 700 }}>
                      <td colSpan={5} style={{ textAlign: 'right' }}>Tổng toàn đơn</td>
                      <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{fmtVND(allocation.goods_base_total)}</td>
                      <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums', color: '#d97706' }}>{fmtVND(allocation.cost_total)}</td>
                      <td style={{ textAlign: 'right', fontVariantNumeric: 'tabular-nums', color: 'var(--teal)' }}>{fmtVND(allocation.landed_total)}</td>
                      <td style={{ textAlign: 'right', color: 'var(--muted)' }}>{allocation.goods_base_total > 0 ? `${(allocation.cost_total / allocation.goods_base_total * 100).toFixed(1)}%` : '-'}</td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            </div>
          )}

          {/* Chứng từ chung — CR-108 khóa NỘI DUNG đơn đã duyệt, nhưng chứng từ vẫn phải gắn
              được SAU khi duyệt (đó mới là lúc có hóa đơn/biên bản), nên `editable` ở đây giữ
              nguyên phạm vi cũ chứ không đi theo headerEditable. */}
          {!isNew && (
            <DocumentAttachmentSection
              entity="purchase_order"
              entityId={Number(id)}
              files={files}
              editable={headerEditable || afterApproveEditable}
              isNew={isNew}
              showDocumentStatus={true}
              documentStatus={po.document_status || 'chưa có chứng từ'}
              onDocumentStatusChange={setDocStatus}
              showChainDetailButton={true}
              onRefresh={loadAll}
            />
          )}

          {po.approve_note && <div className="card" style={{ padding: 14, marginBottom: 16 }}><b>Ghi chú duyệt:</b> {po.approve_note}</div>}

          {/* CR-029: trao đổi trong đơn — chỉ có khi đơn đã lưu (cần id) */}
          {!isNew && <CommentThread entity="purchase_order" entityId={Number(id)} />}
        </div>

        {isLogShown && (
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title"><i className="ti ti-history" /> Lịch sử thao tác</h3>
            <AuditTimeline logs={logs} />
          </div>
        )}
      </div>

      {/* Popup upload chứng từ theo loại */}
      {docModal && (
        <DocumentUploadModal
          entity="purchase_order" entityId={Number(id)} purchaseOrderId={Number(id)}
          onClose={() => setDocModal(false)} onDone={loadAll}
        />
      )}

      {/* Popup tham chiếu giá đã mua trước đó của 1 dòng — chọn xong chỉ FILL, không lưu */}
      {historyIdx !== null && items[historyIdx] && (
        <PurchaseHistoryPickerModal
          productCode={items[historyIdx].product_code}
          productName={items[historyIdx].product_name}
          onPick={(h) => applyHistory(historyIdx, h)}
          readOnly={historyReadOnly(items[historyIdx])}
          onClose={() => setHistoryIdx(null)}
        />
      )}

      {/* Popup giao hàng nhiều lần của 1 dòng */}
      {editingItemIdx !== null && items[editingItemIdx] && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 12 }}>
          <div className="modal-card" style={{ width: 1100, maxWidth: '96vw', background: '#fff', borderRadius: 12, boxShadow: '0 20px 25px -5px rgba(0,0,0,.15)', display: 'flex', flexDirection: 'column', maxHeight: '92vh', overflow: 'hidden' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 16, color: 'var(--navy)' }}>Chi tiết dòng: {items[editingItemIdx].product_name || items[editingItemIdx].product_code}</h3>
                <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2 }}>
                  SL đặt {fmt(items[editingItemIdx].qty_order)} · Đã nhận {fmt(items[editingItemIdx].qty_received || 0)} · Còn lại {fmt((Number(items[editingItemIdx].qty_order) || 0) - (Number(items[editingItemIdx].qty_received) || 0))}
                  {items[editingItemIdx].is_short_delivery && (
                    <span className="badge" style={{ marginLeft: 6, background: '#fef3c7', color: '#b45309', fontSize: 10, padding: '1px 5px' }}>Giao thiếu</span>
                  )}
                </div>
              </div>
              <button className="icon-btn" onClick={() => setEditingItemIdx(null)}><i className="ti ti-x" style={{ fontSize: 18 }} /></button>
            </div>

            <div style={{ padding: '16px 18px', overflowY: 'auto', flex: 1, minWidth: 0, maxWidth: '100%' }}>
              {/* Thông tin sản phẩm (gồm VAT) */}
              <h4 style={{ margin: '0 0 10px', fontSize: 14, color: 'var(--navy)' }}>Thông tin sản phẩm</h4>
              {(() => {
                const ii = editingItemIdx
                const it = items[ii]
                const de = !headerEditable || lineLocked(it)
                // Ô còn sửa được sau khi duyệt (CR-108) — khóa theo `deSau` chứ không theo `de`.
                const deSau = de && !(afterApproveEditable && !lineLocked(it))
                return (
                  <div className="form-grid" style={{ marginBottom: 18 }}>
                    <div className="form-row" title={lineReceived(it) ? PRODUCT_LOCK_HINT : undefined}>
                      <label>Mã hàng (VTBB/NL)<Req /></label>
                      {(de || lineReceived(it))
                        ? <CopyText value={it.product_code} title={it.product_name || undefined} />
                        : <ProductPicker code={it.product_code} name={it.product_name} onPick={(prod) => applyProduct(ii, prod)} />}
                      {lineReceived(it) && <span style={{ fontSize: 12, color: 'var(--muted)' }}><i className="ti ti-lock" /> Đã nhận hàng — khóa mã hàng / tên hàng / ĐVT</span>}
                    </div>
                    <div className="form-row">
                      <label>Phân loại<Req /></label>
                      <SearchSelect value={canonGroup(it.item_group)} options={groupOptions(it.item_group)} disabled={de}
                        placeholder="Chọn/tìm phân loại…" onChange={(v) => setItem(ii, { item_group: v })} />
                    </div>
                    <div className="form-row" style={{ gridColumn: '1 / -1' }} title={lineReceived(it) ? PRODUCT_LOCK_HINT : undefined}><label>Tên hàng<Req /></label><TextAreaAuto style={POPUP_TEXT} value={it.product_name || ''} disabled={de || lineReceived(it)} onChange={(v) => setItem(ii, { product_name: v })} /></div>
                    <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Tên trên hóa đơn<Req /></label><TextAreaAuto style={POPUP_TEXT} value={it.invoice_name || ''} disabled={deSau} onChange={(v) => setItem(ii, { invoice_name: v })} /></div>
                    <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Xuất xứ / TSKT / chất liệu</label><TextAreaAuto style={POPUP_TEXT} value={it.spec || ''} disabled={de} onChange={(v) => setItem(ii, { spec: v })} /></div>
                    <div className="form-row"><label>Mã HH (thành phẩm)</label><input value={it.fg_code || ''} placeholder="Tự gắn khi chọn SP" disabled={de} onChange={(e) => setItem(ii, { fg_code: e.target.value })} /></div>
                    <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Tên HH (thành phẩm)</label><TextAreaAuto style={POPUP_TEXT} value={it.fg_name || ''} placeholder="Tự gắn khi chọn SP" disabled={de} onChange={(v) => setItem(ii, { fg_name: v })} /></div>
                    <div className="form-row"><label title="Có ngày này → dòng chuyển 'Đã gửi ĐMH cho KT'">Ngày giao chứng từ cho KT</label><DateInput value={it.document_delivery_date || ''} disabled={deSau} onChange={(v) => setItem(ii, { document_delivery_date: v })} /></div>
                    <div className="form-row">
                      <label>Trạng thái tiến độ</label>
                      <div>
                        {progressEditable && it.id && !['Hủy đơn', 'Hoàn thành'].includes(it.progress_status) ? (
                          it.progress_status === 'Tạm ngưng' ? (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-start' }}>
                              <span className="badge" style={{ background: PG_COLOR['Tạm ngưng'] + '22', color: PG_COLOR['Tạm ngưng'] }}>Tạm ngưng</span>
                              <button className="btn ghost" style={{ height: 26, fontSize: 11, padding: '0 8px' }} onClick={() => resumeProgress(it)}><i className="ti ti-player-play" />Tiếp tục</button>
                            </div>
                          ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-start' }}>
                              <span className="badge" title="Trạng thái tự động theo dữ liệu" style={{ background: (PG_COLOR[it.progress_status] || '#94a3b8') + '22', color: PG_COLOR[it.progress_status] || '#64748b' }}>{it.progress_status || 'Chưa đặt hàng'}</span>
                              <div style={{ display: 'flex', gap: 4 }}>
                                <button className="btn ghost" style={{ height: 24, fontSize: 11, padding: '0 6px' }} onClick={() => setProgress(it, 'Tạm ngưng')}><i className="ti ti-player-pause" />Tạm ngưng</button>
                                <button className="btn ghost" style={{ height: 24, fontSize: 11, padding: '0 6px', color: 'var(--red)' }} onClick={() => setProgress(it, 'Hủy đơn')}>Hủy</button>
                              </div>
                            </div>
                          )
                        ) : (
                          <span className="badge" title={!it.id ? 'Lưu đơn để cập nhật trạng thái cho dòng mới' : undefined} style={{ background: (PG_COLOR[it.progress_status] || '#94a3b8') + '22', color: PG_COLOR[it.progress_status] || '#64748b' }}>{it.progress_status || 'Chưa đặt hàng'}</span>
                        )}
                        {it.pause_reason && ['Tạm ngưng', 'Hủy đơn'].includes(it.progress_status) && (
                          <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>Lý do: {it.pause_reason}</div>
                        )}
                      </div>
                    </div>
                    <div className="form-row"><label>Ngày yêu cầu có hàng<Req /></label><DateInput value={it.required_date || ''} disabled={de} onChange={(v) => setItem(ii, { required_date: v })} /></div>
                    {/* Dự kiến có hàng: để trống thì khi lưu backend tự chép từ dòng YCMH nguồn.
                        Sửa ở đây KHÔNG ghi đè ngày đang có trên YCMH — chỉ báo chuông cho NSTM phụ trách dòng. */}
                    <div className="form-row"><label>Ngày dự kiến có hàng<Req /></label><DateInput value={it.expected_date || ''} disabled={deSau} onChange={(v) => setItem(ii, { expected_date: v })} /></div>
                    <div className="form-row"><label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}><input type="checkbox" checked={!!it.supplier_ready} disabled={de} onChange={(e) => setItem(ii, { supplier_ready: e.target.checked })} style={{ width: 16, height: 16 }} /> NCC có sẵn hàng</label></div>
                    <div className="form-row"><label>ĐVT<Req /></label>
                      <SearchSelect value={it.unit ?? ''} options={units} disabled={de} placeholder="Chọn/tìm ĐVT…" onChange={(v) => setItem(ii, { unit: v })} />
                    </div>
                    {/* bao-CR-319: khối lượng là căn cứ chia chi phí lô hàng theo cân nặng ở
                        phase sau — nhập ngay từ bây giờ thì lúc bật phân bổ khỏi phải gõ lại. */}
                    {isImport && (
                      <div className="form-row"><label>Khối lượng (kg)</label><NumberInput decimals value={it.weight_kg ?? 0} maxDecimals={3} disabled={deSau} placeholder="Dùng để chia chi phí theo khối lượng" onChange={(v) => setItem(ii, { weight_kg: v })} /></div>
                    )}
                    {isImport && (
                      <div className="form-row"><label>Quy cách / kích thước</label><input value={it.dimension || ''} disabled={deSau} placeholder="VD: 40x30x25 cm" onChange={(e) => setItem(ii, { dimension: e.target.value })} /></div>
                    )}
                    <div className="form-row"><label>Kho nhận mặc định<Req /></label>
                      <SearchSelect value={it.warehouse_code ?? ''} disabled={deSau} placeholder="Chọn/tìm kho…"
                        options={warehouses.map((w) => ({ value: w.code, label: `${w.code} — ${w.name}` }))}
                        onChange={(v) => setItem(ii, { warehouse_code: v })} />
                    </div>
                    <div className="form-row"><label>SL yêu cầu<Req /></label><NumberInput decimals value={it.qty_request} disabled={de} onChange={(v) => setItem(ii, { qty_request: v })} /></div>
                    <div className="form-row"><label>SL đặt NCC<Req /></label><NumberInput decimals value={it.qty_order} disabled={de} onChange={(v) => setItem(ii, { qty_order: v })} /></div>
                    <div className="form-row"><label>Đơn giá<Req /></label><CurrencyInput className="" value={it.price ?? 0} disabled={de} onChange={(val: number) => setItem(ii, { price: val })} /></div>
                    {/* bao-CR-319: một đơn nhập khẩu vẫn có thể lẫn dòng trả bằng tiền Việt
                        (phí nội địa), nên đồng tiền + tỷ giá đặt ở TỪNG DÒNG chứ không chỉ ở đơn. */}
                    {showCurrency && (
                      <div className="form-row">
                        <label>Đồng tiền</label>
                        <select value={lineCurrency(it)} disabled={de}
                          onChange={(e) => {
                            const cur = e.target.value
                            setItem(ii, cur === DEFAULT_CURRENCY
                              ? { currency: cur, exchange_rate: 1 }
                              : { currency: cur })
                          }}>
                          {Array.from(new Set([...CURRENCY_OPTS, lineCurrency(it)])).map((c) => (
                            <option key={c} value={c}>{c}</option>
                          ))}
                        </select>
                      </div>
                    )}
                    {showCurrency && lineCurrency(it) !== DEFAULT_CURRENCY && (
                      <div className="form-row">
                        <label>Tỷ giá<Req /></label>
                        <NumberInput value={it.exchange_rate ?? 0} maxDecimals={6} disabled={de}
                          placeholder={`1 ${lineCurrency(it)} = ? VNĐ`}
                          onChange={(v) => setItem(ii, { exchange_rate: v })} />
                      </div>
                    )}
                    {showCurrency && (
                      <div className="form-row"><label>Thành tiền quy đổi (VNĐ)</label><input value={fmtVND(orderAmount(it) * lineRate(it))} disabled /></div>
                    )}
                    {/* bao-CR-319 P3 — đơn NHẬP KHẨU khóa VAT dòng hàng về 0. Thuế GTGT hàng
                        nhập nộp ngân sách nhà nước theo tờ khai và đã khai thành một dòng ở
                        bảng Chi phí lô hàng; gõ thêm ở đây là cộng thuế hai lần VÀ ghi khoản
                        thuế đó thành nợ của chính NCC nước ngoài. Backend cũng ép 0. */}
                    {!isImport && (
                      <div className="form-row"><label>VAT (%)</label><NumberInput value={it.vat} max={VAT_MAX} maxDecimals={VAT_DECIMALS} disabled={de} placeholder="Nhập % VAT (0 – 99,99)" onChange={(v) => setItem(ii, { vat: v })} /></div>
                    )}
                    {!isImport && (
                      <div className="form-row"><label>Đơn giá (Sau VAT)</label><input value={fmtPrice(Math.round((Number(it.price) || 0) * (1 + (Number(it.vat) || 0) / 100) * 100) / 100)} disabled style={{ fontWeight: 600 }} /></div>
                    )}
                    <div className="form-row"><label>Tổng tiền đặt hàng{showCurrency ? ` (${lineCurrency(it)})` : ''}</label><input value={fmtAmt(it.order_total ?? orderAmount(it))} disabled /></div>
                    <div className="form-row"><label>Tổng tiền hàng (đã nhận)</label><input value={fmtVND(it.goods_total || 0)} disabled /></div>
                    <div className="form-row"><label>Tổng đã trả</label><input value={fmtVND(it.paid_total || 0)} disabled style={{ color: 'var(--green)', fontWeight: 600 }} /></div>
                    <div className="form-row"><label>Còn lại</label><input value={fmtVND(it.remaining_total || 0)} disabled style={{ color: (it.remaining_total || 0) > 0 ? 'var(--red)' : 'var(--muted)', fontWeight: 600 }} /></div>
                    <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Ghi chú</label><input value={it.note || ''} disabled={deSau} onChange={(e) => setItem(ii, { note: e.target.value })} /></div>
                  </div>
                )
              })()}

              <h4 style={{ margin: '0 0 10px', fontSize: 14, color: 'var(--navy)', borderTop: '1px solid var(--border)', paddingTop: 14 }}>Giao hàng (nhiều lần)</h4>
              {isNew && <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 10 }}>Lưu đơn (Tạo) trước rồi mới thêm lần giao.</div>}
              {!isNew && !deliveryEditable && <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 10 }}>Chỉ thêm/sửa lần giao khi đơn đã được duyệt.</div>}
              {lineLocked(items[editingItemIdx]) && <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 10 }}>Dòng đã {items[editingItemIdx].progress_status === 'Hủy đơn' ? 'hủy' : 'hoàn thành'} — không sửa được lần giao.</div>}
              {deliveryEditable && !lineLocked(items[editingItemIdx]) && (
                <button className="btn ghost" style={{ height: 30, fontSize: 13, marginBottom: 10 }} onClick={() => addDelivery(editingItemIdx)}><i className="ti ti-plus" />Thêm lần giao</button>
              )}
              <div className="items-scroll">
                <table className="items-table" style={{ minWidth: 2800 }}>
                  <thead>
                    <tr>
                      <th style={{ width: 44 }}>Lần</th>
                      <th style={{ width: 130 }}>Kho nhận</th>
                      <th style={{ width: 150 }}>Đơn vị vận chuyển</th>
                      <th style={{ width: 80 }}>SL gửi</th>
                      <th style={{ width: 90 }}>ĐVT VC</th>
                      <th style={{ width: 80 }}>SL đặt</th>
                      <th style={{ width: 90 }}>SL nhận</th>
                      <th style={{ width: 100 }}>Đơn giá</th>
                      {!isImport && <th style={{ width: 64 }}>VAT%</th>}
                      <th style={{ width: 130, background: '#fff3cd' }}>Thành tiền (nhận)</th>
                      <th style={{ width: 130 }}>Số hóa đơn</th>
                      <th style={{ width: 110 }}>Ngày hóa đơn</th>
                      <th style={{ width: 110 }}>Đã trả</th>
                      <th style={{ width: 110 }}>Còn lại</th>
                      <th style={{ width: 110 }}>Cam kết giao</th>
                      <th style={{ width: 110 }}>Ngày nhận</th>
                      <th style={{ width: 70 }}>Số ngày QĐ</th>
                      <th style={{ width: 105, whiteSpace: 'nowrap' }}>Ngày QĐ</th>
                      <th style={{ width: 70 }}>Trễ CK</th>
                      <th style={{ width: 70 }}>Trễ QĐ</th>
                      <th style={{ width: 80 }}>Trễ QĐ-KD</th>
                      <th style={{ width: 110 }}>Trạng thái giao</th>
                      <th style={{ width: 100 }}>Đơn giá VC</th>
                      <th style={{ width: 110 }}>Thành tiền VC</th>
                      <th style={{ width: 150 }}>Yêu cầu khác</th>
                      <th style={{ width: 140 }}>Phiếu giao</th>
                      {deliveryEditable && !lineLocked(items[editingItemIdx]) && <th style={{ width: 40 }} />}
                    </tr>
                  </thead>
                  <tbody>
                    {(items[editingItemIdx].deliveries || []).map((d: any, di: number) => {
                      const ii = editingItemIdx
                      const dis = !deliveryEditable || lineLocked(items[ii])
                      return (
                        <tr key={di}>
                          <td><NumberInput className="cell-input" style={{ width: 44 }} value={d.delivery_no} disabled={dis} onChange={(v) => setDelivery(ii, di, { delivery_no: v })} /></td>
                          <td>
                            <select className="cell-input" style={{ width: 120 }} value={d.warehouse_code ?? ''} disabled={dis} onChange={(e) => setDelivery(ii, di, { warehouse_code: e.target.value })} title="Kho nhận">
                              <option value="">—</option>{warehouses.map((w) => <option key={w.id} value={w.code}>{w.code}</option>)}
                            </select>
                          </td>
                          <td>
                            <select className="cell-input" style={{ width: 150 }} value={d.carrier_code || (d.carrier_name ? '__self__' : '')} disabled={dis} onChange={(e) => onPickCarrier(ii, di, e.target.value)}>
                              <option value="">— Chọn đơn vị VC —</option>
                              <option value="__self__">NCC tự vận chuyển</option>
                              {carriers.filter((c) => (c.name || '').trim().toLowerCase() !== 'ncc tự vận chuyển')
                                .map((c) => <option key={c.id} value={c.code}>{c.name}</option>)}
                            </select>
                          </td>
                          <td><NumberInput decimals className="cell-input" style={{ width: 72 }} value={d.ship_qty} disabled={dis} onChange={(v) => setDelivery(ii, di, { ship_qty: v })} /></td>
                          <td>
                            <select className="cell-input" style={{ width: 80 }} value={d.ship_unit ?? ''} disabled={dis} onChange={(e) => setDelivery(ii, di, { ship_unit: e.target.value })}>
                              <option value="">—</option>{SHIP_UNITS.map((su) => <option key={su} value={su}>{su}</option>)}
                            </select>
                          </td>
                          <td style={{ textAlign: 'right', color: 'var(--muted)' }}>{fmt(items[ii].qty_order)}</td>
                          <td><NumberInput decimals className="cell-input" style={{ width: 80 }} value={d.received_qty} disabled={dis} onChange={(v) => setDelivery(ii, di, { received_qty: v })} /></td>
                          <td style={{ textAlign: 'right', color: 'var(--muted)' }}>{fmtPrice(items[ii].price)}</td>
                          {!isImport && <td style={{ textAlign: 'center', color: 'var(--muted)' }}>{Number(items[ii].vat) || 0}%</td>}
                          <td style={{ textAlign: 'right', fontWeight: 600, background: '#fff8e6' }}>{fmtVND((Number(d.received_qty) || 0) * (Number(items[ii].price) || 0) * (1 + (Number(items[ii].vat) || 0) / 100))}</td>
                          <td><input className="cell-input" style={{ width: 120 }} value={d.invoice_no || ''} placeholder="Số HĐ đợt này" disabled={dis} onChange={(e) => { const v = e.target.value; setDelivery(ii, di, { invoice_no: v, ...(v && !(d.invoice_date || '').trim() ? { invoice_date: new Date().toISOString().slice(0, 10) } : {}) }) }} /></td>
                          <td><DateInput className="cell-input" style={{ width: 110 }} value={d.invoice_date || ''} disabled={dis} onChange={(v) => setDelivery(ii, di, { invoice_date: v })} /></td>
                          <td style={{ textAlign: 'right', color: 'var(--green)', fontWeight: 600 }}>{d.id ? fmtVND(d.paid || 0) : '—'}</td>
                          <td style={{ textAlign: 'right', color: (Number(d.remaining) || 0) > 0 ? 'var(--red)' : 'var(--muted)', fontWeight: 600 }}>{d.id ? fmtVND(d.remaining || 0) : '—'}</td>
                          <td><DateInput className="cell-input" style={{ width: 110 }} value={d.promised_date ?? ''} disabled={dis} onChange={(v) => setDelivery(ii, di, { promised_date: v })} /></td>
                          <td><DateInput className="cell-input" style={{ width: 110 }} value={d.received_date ?? ''} disabled={dis} onChange={(v) => setDelivery(ii, di, { received_date: v })} /></td>
                          <td><NumberInput className="cell-input" style={{ width: 60 }} value={d.std_days} disabled={dis} onChange={(v) => setDelivery(ii, di, { std_days: v })} /></td>
                          <td style={{ textAlign: 'center', color: 'var(--muted)', whiteSpace: 'nowrap' }}>{d.regulated_date ? fmtDateStr(d.regulated_date) : '—'}</td>
                          <td style={{ textAlign: 'center', color: (d.diff_promise < 0 ? 'var(--red)' : 'var(--muted)'), fontWeight: d.diff_promise < 0 ? 600 : 400 }}>{d.received_date ? (d.diff_promise ?? 0) : '—'}</td>
                          <td style={{ textAlign: 'center', color: (d.diff_regulated < 0 ? 'var(--red)' : 'var(--muted)'), fontWeight: d.diff_regulated < 0 ? 600 : 400 }}>{d.received_date ? (d.diff_regulated ?? 0) : '—'}</td>
                          <td style={{ textAlign: 'center', color: (d.diff_required < 0 ? 'var(--red)' : 'var(--muted)') }}>{items[ii].required_date ? (d.diff_required ?? 0) : '—'}</td>
                          <td style={{ textAlign: 'center', fontSize: 12 }}>{d.status ? <span className={'badge ' + (d.status === 'Đã nhận' ? 'ok' : d.status === 'Lỗi' ? 'err' : 'warn')}>{d.status}</span> : '—'}</td>
                          <td>
                            <CurrencyInput
                              style={{ width: 100 }}
                              value={d.shipping_unit_price ?? 0}
                              disabled={dis}
                              onChange={(val: number) => setDelivery(ii, di, { shipping_unit_price: val, shipping_amount: val * (Number(d.ship_qty) || 0) })}
                            />
                          </td>
                          <td>
                            <CurrencyInput
                              style={{ width: 110 }}
                              value={d.shipping_amount ?? 0}
                              disabled={dis}
                              onChange={(val: number) => setDelivery(ii, di, { shipping_amount: val })}
                            />
                          </td>
                          <td><input className="cell-input" style={{ width: 140 }} value={d.extra_request ?? ''} disabled={dis} onChange={(e) => setDelivery(ii, di, { extra_request: e.target.value })} /></td>
                          <td style={{ fontSize: 12 }}>
                            {d.id ? (
                              <div>
                                {deliveryAttachEditable && <>
                                  <input type="file" id={`datt-${d.id}`} style={{ display: 'none' }} onChange={(e) => uploadDeliveryAtt(d.id, e.target.files)} />
                                  <label htmlFor={`datt-${d.id}`} className="btn ghost" style={{ cursor: 'pointer', height: 26, fontSize: 11, padding: '0 8px' }}><i className="ti ti-upload" /> Tải</label>
                                </>}
                                {(attByDelivery[d.id] || []).map((f) => (
                                  <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 3 }}>
                                    <a href={f.url} target="_blank" style={{ color: 'var(--teal)', textDecoration: 'underline', maxWidth: 90, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.filename}</a>
                                    {deliveryAttachEditable && <button className="icon-btn" onClick={async () => { await api.delete(`/api/attachments/${f.id}`); loadDeliveryAtt(d.id) }}><i className="ti ti-x" style={{ color: 'var(--red)', fontSize: 13 }} /></button>}
                                  </div>
                                ))}
                              </div>
                            ) : (
                              !dis ? (
                                <div>
                                  <input type="file" multiple id={`ndatt-${ii}-${di}`} style={{ display: 'none' }} onChange={(e) => setDelivery(ii, di, { _pendingFiles: e.target.files })} />
                                  <label htmlFor={`ndatt-${ii}-${di}`} className="btn ghost" style={{ cursor: 'pointer', height: 26, fontSize: 11, padding: '0 8px' }}><i className="ti ti-upload" /> Chọn tệp</label>
                                  {d._pendingFiles && d._pendingFiles.length > 0 && (
                                    <div style={{ fontSize: 11, marginTop: 3, color: 'var(--muted)' }}>
                                      {Array.from(d._pendingFiles as FileList).map((f) => f.name).join(', ')} <span style={{ color: 'var(--amber, #d97706)' }}>(tải khi Lưu)</span>
                                    </div>
                                  )}
                                </div>
                              ) : <span style={{ color: '#999' }}>Lưu để đính kèm</span>
                            )}
                          </td>
                          {!dis && (
                            <td style={{ textAlign: 'center' }}><button className="icon-btn" onClick={() => delDelivery(ii, di)}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button></td>
                          )}
                        </tr>
                      )
                    })}
                    {(items[editingItemIdx].deliveries || []).length === 0 && <tr><td colSpan={26} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Chưa có lần giao nào</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <button className="btn ghost" style={{ height: 36, fontSize: 13 }} onClick={() => setEditingItemIdx(null)}>Đóng</button>
              {(headerEditable || deliveryEditable) && !lineLocked(items[editingItemIdx]) && <button className="btn" style={{ height: 36, fontSize: 13 }} onClick={() => { setEditingItemIdx(null); save() }}>Lưu đơn</button>}
            </div>
          </div>
        </div>
      )}

      {/* Popup chọn hóa đơn để tạo Yêu cầu thanh toán */}
      {/* bao-CR-319 — Popup chi tiết MỘT khoản chi phí nhập khẩu. Cùng state với bảng
          (setCost), nên sửa ở đây hay ở bảng đều là một, và vẫn phải bấm Lưu của đơn. */}
      {editingCostIdx !== null && importCosts[editingCostIdx] && (() => {
        const ci = editingCostIdx
        const c = importCosts[ci]
        const de = !costEditable
        const hasPayable = Number(c.payable_id) > 0
        return (
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 12 }} onClick={() => setEditingCostIdx(null)}>
            <div className="modal-card" style={{ width: 860, maxWidth: '96vw', background: '#fff', borderRadius: 12, boxShadow: '0 20px 25px -5px rgba(0,0,0,.15)', display: 'flex', flexDirection: 'column', maxHeight: '92vh', overflow: 'hidden' }} onClick={(e) => e.stopPropagation()}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
                <div>
                  <h3 style={{ margin: 0, fontSize: 16, color: 'var(--navy)' }}>Chi tiết chi phí #{ci + 1}: {COST_TYPE_LABEL(c.cost_type)}</h3>
                  <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2 }}>
                    Quy đổi {fmtVND(costBase(c))}
                    {hasPayable
                      ? <> · Đã chi <span style={{ color: 'var(--green)' }}>{fmtVND(c.paid_amount)}</span> · Còn lại <span style={{ color: (Number(c.remaining) || 0) > 0.01 ? 'var(--red)' : 'var(--muted)' }}>{fmtVND(c.remaining)}</span></>
                      : <> · Chưa thành công nợ{isNew || !c.id ? ' (dòng mới, Lưu đơn trước)' : PO_PAYABLE_STATUSES.includes(po.status) ? ' (chưa chọn NCC hoặc số tiền 0)' : ' (đơn chưa duyệt)'}</>}
                  </div>
                </div>
                <button className="icon-btn" onClick={() => setEditingCostIdx(null)}><i className="ti ti-x" style={{ fontSize: 18 }} /></button>
              </div>

              <div style={{ padding: '16px 18px', overflowY: 'auto', flex: 1, minWidth: 0, maxWidth: '100%' }}>
                <h4 style={{ margin: '0 0 10px', fontSize: 14, color: 'var(--navy)' }}>Khoản chi phí</h4>
                <div className="form-grid" style={{ marginBottom: 18 }}>
                  <div className="form-row">
                    <label>Loại chi phí</label>
                    <select value={String(Number(c.cost_type) || 99)} disabled={de}
                      onChange={(e) => {
                        const v = Number(e.target.value) || 99
                        const patch: any = { cost_type: v }
                        if (IMPORT_COST_TAX_TYPES.includes(v) && !(c.supplier_code || '').trim()) {
                          patch.supplier_code = STATE_BUDGET_SUPPLIER_CODE
                          patch.supplier_name = STATE_BUDGET_SUPPLIER_NAME
                        }
                        setCost(ci, patch)
                      }}>
                      {IMPORT_COST_TYPE_OPTS.map(([v, label]) => <option key={v} value={String(v)}>{label}</option>)}
                    </select>
                  </div>
                  <div className="form-row">
                    <label>Nhà cung cấp</label>
                    <SearchSelect value={c.supplier_code || ''} disabled={de} placeholder="Chọn/tìm NCC…"
                      options={suppliers.map((s) => ({ value: s.code, label: `${s.code} — ${s.name}` }))}
                      onChange={(v) => {
                        const s = suppliers.find((x) => x.code === v)
                        setCost(ci, { supplier_code: v, supplier_name: s ? s.name : '' })
                      }} />
                  </div>
                  <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                    <label>Diễn giải</label>
                    <TextAreaAuto style={POPUP_TEXT} value={c.description || ''} disabled={de} placeholder="VD: Cước biển Thượng Hải – Cát Lái, 1x20DC" onChange={(v) => setCost(ci, { description: v })} />
                  </div>
                  <div className="form-row">
                    <label>Tiền tệ</label>
                    <select value={costCurrency(c)} disabled={de}
                      onChange={(e) => {
                        const cur = e.target.value
                        setCost(ci, { currency: cur, exchange_rate: cur === DEFAULT_CURRENCY ? 1 : 0 })
                      }}>
                      {Array.from(new Set([...CURRENCY_OPTS, costCurrency(c)])).map((cur) => <option key={cur} value={cur}>{cur}</option>)}
                    </select>
                  </div>
                  <div className="form-row">
                    <label>Tỷ giá</label>
                    {costCurrency(c) === DEFAULT_CURRENCY
                      ? <CopyText value="1" />
                      : <NumberInput value={c.exchange_rate || costRate(c)} maxDecimals={6} disabled={de} onChange={(v: any) => setCost(ci, { exchange_rate: v })} />}
                  </div>
                  <div className="form-row"><label>Số tiền (trước thuế, {costCurrency(c)})</label><CurrencyInput className="" value={c.amount ?? 0} disabled={de} onChange={(v: number) => setCost(ci, { amount: v })} /></div>
                  <div className="form-row"><label>VAT %</label><NumberInput value={c.vat ?? 0} max={VAT_MAX} maxDecimals={VAT_DECIMALS} disabled={de} onChange={(v: any) => setCost(ci, { vat: v })} /></div>
                  <div className="form-row"><label>Quy đổi (VNĐ, đã gồm VAT)</label><CopyText value={fmtVND(costBase(c))} /></div>
                  <div className="form-row">
                    <label>Cách phân bổ</label>
                    <select value={String(Number(c.allocation_method) || ALLOC_BY_VALUE)} disabled={de}
                      onChange={(e) => switchAllocationMethod(ci, c, Number(e.target.value) || ALLOC_BY_VALUE)}>
                      {ALLOCATION_OPTS.map(([v, label]) => <option key={v} value={String(v)}>{label}</option>)}
                    </select>
                  </div>
                  {Number(c.allocation_method) === ALLOC_BY_PRODUCT && (
                    <div className="form-row">
                      <label>Mã hàng chỉ định</label>
                      <select value={c.allocation_target || ''} disabled={de} onChange={(e) => setCost(ci, { allocation_target: e.target.value })}>
                        <option value="">— chọn mã hàng —</option>
                        {items.filter((it: any) => (it.product_code || '').trim())
                          .map((it: any, k: number) => <option key={k} value={it.product_code}>{it.product_code}</option>)}
                      </select>
                    </div>
                  )}
                  {isManualCost(c) && (
                    <div className="form-row">
                      <label>Nhập tay</label>
                      <div style={{ fontSize: 12.5, color: Math.abs(manualDiff(c)) > MANUAL_ALLOC_TOLERANCE ? '#b91c1c' : '#15803d', paddingTop: 6 }}>
                        {manualEntered(c) > 0
                          ? `Đã nhập ${fmtVND(manualEntered(c))} / ${fmtVND(costBase(c))}${Math.abs(manualDiff(c)) > MANUAL_ALLOC_TOLERANCE ? ` — lệch ${fmtVND(manualDiff(c))}` : ' — đã khớp tổng'}`
                          : 'Gõ số tiền từng dòng ở bảng Chi phí theo dòng hàng'}
                      </div>
                    </div>
                  )}
                </div>

                <h4 style={{ margin: '0 0 10px', fontSize: 14, color: 'var(--navy)' }}>Hóa đơn và thanh toán</h4>
                <div className="form-grid">
                  <div className="form-row"><label>Số hóa đơn</label><input value={c.invoice_no || ''} disabled={de} onChange={(e) => setCost(ci, { invoice_no: e.target.value })} /></div>
                  <div className="form-row"><label>Ngày hóa đơn</label><DateInput value={c.invoice_date || ''} disabled={de} onChange={(v) => setCost(ci, { invoice_date: v })} /></div>
                  <div className="form-row"><label>Hạn thanh toán</label><DateInput value={c.payment_due_date || ''} disabled={de} onChange={(v) => setCost(ci, { payment_due_date: v })} /></div>
                  {hasPayable && (
                    <div className="form-row"><label>Công nợ</label><CopyText value={`Đã chi ${fmtVND(c.paid_amount)} · Còn lại ${fmtVND(c.remaining)}`} /></div>
                  )}
                  <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                    <label>Ghi chú</label>
                    <TextAreaAuto style={POPUP_TEXT} value={c.note || ''} disabled={de} onChange={(v) => setCost(ci, { note: v })} />
                  </div>
                </div>
              </div>

              <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 12.5, color: 'var(--muted)' }}>{de ? 'Đơn đang khóa sửa chi phí.' : 'Sửa xong đóng lại rồi bấm Lưu của đơn mới có hiệu lực.'}</span>
                <button className="btn ghost" onClick={() => setEditingCostIdx(null)}>Đóng</button>
              </div>
            </div>
          </div>
        )
      })()}

      {payModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 12 }} onClick={() => setPayModal(false)}>
          <div className="modal-card" style={{ width: 780, maxWidth: '96vw', background: '#fff', borderRadius: 12, boxShadow: '0 20px 25px -5px rgba(0,0,0,.15)', display: 'flex', flexDirection: 'column', maxHeight: '90vh', overflow: 'hidden' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
              <h3 style={{ margin: 0, fontSize: 16, color: 'var(--navy)' }}>Tạo yêu cầu thanh toán — chọn hóa đơn</h3>
              <button className="icon-btn" onClick={() => setPayModal(false)}><i className="ti ti-x" style={{ fontSize: 18 }} /></button>
            </div>
            {/* Tab: NCC sản xuất (hàng) · NCC vận chuyển · Chi phí lô hàng (P5, chỉ đơn nhập khẩu mới có dòng) */}
            <div style={{ display: 'flex', gap: 6, padding: '10px 18px 0', borderBottom: '1px solid var(--border)' }}>
              {PAY_TABS.filter(([k]) => k !== 'import_cost' || payables.some((p) => p.source_type === 'import_cost')).map(([k, lbl]) => {
                const n = payables.filter((p) => p.source_type === k).length
                return (
                  <button key={k} onClick={() => setPayTab(k)} style={{ border: 'none', background: 'none', padding: '8px 12px', cursor: 'pointer', fontSize: 13.5, fontWeight: payTab === k ? 700 : 500, color: payTab === k ? 'var(--teal)' : 'var(--muted)', borderBottom: payTab === k ? '2px solid var(--teal)' : '2px solid transparent', whiteSpace: 'nowrap' }}>{lbl}{n ? ` (${n})` : ''}</button>
                )
              })}
            </div>
            <div style={{ padding: '12px 18px', overflowY: 'auto', flex: 1 }}>
              {(() => {
                const rows = payables.filter((p) => p.source_type === payTab)
                const rowIds = rows.map((p) => p.id)
                const allSel = rows.length > 0 && rowIds.every((id) => paySel.includes(id))
                return (<>
                  <div style={{ fontSize: 12.5, color: 'var(--muted)', marginBottom: 8 }}>
                    {payTab === 'import_cost'
                      ? <>Công nợ chi phí lô hàng chưa chi đủ của đơn <b>{po.code}</b> — mỗi dòng chi phí là 1 khoản; tick nhiều NCC thì hệ thống tự tách mỗi NCC một phiếu.</>
                      : <>{payTab === 'goods' ? 'Công nợ hàng (NCC sản xuất)' : 'Công nợ vận chuyển'} chưa trả đủ của đơn <b>{po.code}</b> — mỗi lần nhận là 1 dòng (cùng số HĐ có thể nhiều dòng). Bỏ tick nếu chưa thanh toán.</>}
                  </div>
                  <table className="items-table" style={{ width: '100%' }}>
                    <thead><tr>
                      <th style={{ width: 36, textAlign: 'center' }}><input type="checkbox" checked={allSel} onChange={(e) => setPaySel((s) => e.target.checked ? Array.from(new Set([...s, ...rowIds])) : s.filter((x) => !rowIds.includes(x)))} /></th>
                      <th>{payTab === 'goods' ? 'Nhà cung cấp' : payTab === 'shipping' ? 'Đơn vị vận chuyển' : 'Nhà cung cấp / cơ quan thu'}</th>
                      <th>Số hóa đơn</th><th>Ngày phát sinh</th>
                      <th style={{ textAlign: 'right' }}>Phải trả</th><th style={{ textAlign: 'right' }}>Đã trả</th><th style={{ textAlign: 'right' }}>Còn lại</th>
                    </tr></thead>
                    <tbody>
                      {rows.map((p) => (
                        <tr key={p.id}>
                          <td style={{ textAlign: 'center' }}><input type="checkbox" checked={paySel.includes(p.id)} onChange={(e) => setPaySel((s) => e.target.checked ? [...s, p.id] : s.filter((x) => x !== p.id))} /></td>
                          <td>{p.supplier_name || p.supplier_code || '—'}</td>
                          <td>{p.invoice_no || '—'}</td><td>{p.incur_date}</td>
                          <td style={{ textAlign: 'right' }}>{fmtVND(p.total)}</td>
                          <td style={{ textAlign: 'right', color: 'var(--green)' }}>{fmtVND(p.paid_amount)}</td>
                          <td style={{ textAlign: 'right', color: 'var(--red)', fontWeight: 600 }}>{fmtVND(p.remaining)}</td>
                        </tr>
                      ))}
                      {rows.length === 0 && <tr><td colSpan={7} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Không có khoản nợ nào cần thanh toán</td></tr>}
                    </tbody>
                  </table>
                </>)
              })()}
            </div>
            <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 13.5, color: 'var(--navy)' }}>Đã chọn {paySel.length} khoản · Tổng đề nghị: <b>{fmtVND(payables.filter((p) => paySel.includes(p.id)).reduce((s, p) => s + (Number(p.remaining) || 0), 0))}</b></span>
              <div style={{ display: 'flex', gap: 8 }}>
                <button className="btn ghost" onClick={() => setPayModal(false)}>Đóng</button>
                <button className="btn" disabled={paySel.length === 0} onClick={createPaymentRequest}><i className="ti ti-receipt" />Tạo yêu cầu thanh toán</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
