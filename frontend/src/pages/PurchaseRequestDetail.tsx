import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { fmtDateTime, fmtDate } from '../utils/datetime'
import { toast } from '../components/toast'
import { askConfirm, askPrompt } from '../components/confirm'
import { useAuth } from '../auth/AuthContext'
import { prBadge, poBadge } from '../config/cruds'
import ProductPicker from '../components/ProductPicker'
import PurchaseHistoryPickerModal, { HistoryPick } from '../components/PurchaseHistoryPickerModal'
import SearchSelect from '../components/SearchSelect'
import NumberInput from '../components/NumberInput'
import { VAT_MAX, VAT_DECIMALS } from '../utils/vat'
import DateInput from '../components/DateInput'
import TextAreaAuto from '../components/TextAreaAuto'
import ConfirmModal from '../components/ConfirmModal'
import PromptModal from '../components/PromptModal'
import NotFound from '../components/NotFound'
import DocumentUploadModal from '../components/DocumentUploadModal'
import DocumentAttachmentSection from '../components/DocumentAttachmentSection'
import AttachmentGallery from '../components/AttachmentGallery'
import CompareLightbox from '../components/CompareLightbox'
import CommentThread from '../components/CommentThread'
import AuditTimeline from '../components/AuditTimeline'
import { fmtSize, fileIcon } from '../utils/file-type'
import { regulatedDate, stdDaysMap, stdDaysOf } from '../utils/lead-time'
import { newDupCodes } from '../utils/lines'
import { prLineStatusLabel } from '../utils/statusLabels'

const API = '/api/purchase-requests'
const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
// Hiển thị số: để TRỐNG nếu chưa nhập (0/rỗng) để tránh hiểu lầm "đã nhập = 0"
const fmtBlank = (n: any) => { const v = Number(n || 0); return v ? v.toLocaleString('vi-VN') : '' }
// ĐƠN GIÁ cho lẻ tới 4 chữ số (vd 1.668,182 đ/cái); TIỀN thì làm tròn về đồng vì đơn giá lẻ
// kéo theo thành tiền có đuôi lẻ (4.760.000,08) mà kế toán chỉ ghi nhận tới đồng.
const PRICE_DECIMALS = 4
const fmtPriceBlank = (n: any) => { const v = Number(n || 0); return v ? v.toLocaleString('vi-VN', { maximumFractionDigits: PRICE_DECIMALS }) : '' }
const fmtVND = (n: any) => Math.round(Number(n) || 0).toLocaleString('vi-VN')
const fmtVNDBlank = (n: any) => { const v = Math.round(Number(n) || 0); return v ? v.toLocaleString('vi-VN') : '' }
// CR-074: "Chưa tạo đơn mua hàng" = chưa ai lập ĐMH cho dòng này;
// "Chưa đặt hàng" = đã có ĐMH (kể cả đơn còn Nháp) nhưng chưa bấm đặt hàng.
// B-06: cột `line_status` lưu MÃ; nhãn lấy ở `statusLabels.ts`, ở đây chỉ còn bảng màu.
const LS_NO_PO = 'no_po'
const LS_CANCELLED = 'cancelled'
const LS_COLOR: Record<string, string> = {
  no_po: '#94a3b8', not_ordered: '#d97706', ordered: '#00AEEF',
  received: '#0d9488', completed: '#16a34a', cancelled: '#b91c1c',
}
const emptyItem = {
  product_code: '', product_name: '', item_group: '', group_desc: '', qty: 0, unit: '',
  price: 0, vat_pct: 8, warehouse: '', required_date: '', assignee: '', line_status: LS_NO_PO, progress_note: '', note: '',
  qty_ordered: 0, qty_received: 0,
}
// Hằng số dùng chung cho dòng CHƯA có ảnh chờ: phải là CÙNG một mảng qua mọi lần render,
// vì AttachmentGallery theo dõi `pendingFiles` theo tham chiếu — viết `|| []` tại chỗ sẽ
// tạo mảng mới mỗi render và làm effect chạy lặp vô hạn.
const KHONG_CO_FILE: File[] = []
// Thành tiền dòng GỒM VAT (Task 4)
const lineAmount = (it: any) => (Number(it.qty) || 0) * (Number(it.price) || 0) * (1 + (Number(it.vat_pct) || 0) / 100)

// Số ngày giữa 2 mốc "YYYY-MM-DD" (a − b); null nếu thiếu/không hợp lệ
function daysBetween(a: string, b: string): number | null {
  if (!a || !b) return null
  const da = new Date(a + 'T00:00:00').getTime(), db = new Date(b + 'T00:00:00').getTime()
  if (isNaN(da) || isNaN(db)) return null
  return Math.round((da - db) / 86400000)
}

// Đơn gấp = có ≥1 dòng mà thời gian chuẩn bị (ngày cần hàng − ngày tiếp nhận phiếu) NHỎ HƠN số ngày
// QĐ của phân loại VTBB/NL — mốc dài nhất (không sẵn hàng), xem utils/lead-time.ts.
// CR-082: thiếu ĐÚNG MỘT ngày cũng là gấp (không có dung sai); dòng Hủy đơn hoặc chưa nhập ngày
// cần hàng thì bỏ qua. Khớp urgent_reasons() bên backend — backend mới là nơi chốt cờ lúc lưu.
// Trả về danh sách dòng vi phạm để nói rõ cho người dùng vì sao phiếu bị đánh dấu gấp.
function urgentLinesPR(items: any[], baseDate: string, stdMap: Record<string, number>): string[] {
  if (!baseDate) return []
  const out: string[] = []
  for (const it of items || []) {
    if (it.line_status === LS_CANCELLED) continue
    const std = stdDaysOf(stdMap, it.item_group)
    if (std <= 0) continue
    const lead = daysBetween(it.required_date, baseDate)
    if (lead === null || lead >= std) continue
    out.push(`${it.product_name || it.product_code || 'Dòng hàng'}: cần sau ${lead} ngày, `
      + `phân loại "${it.item_group || 'chưa chọn'}" quy định ${std} ngày`)
  }
  return out
}

export default function PurchaseRequestDetail() {
  const { id } = useParams()
  const isNew = id === 'new'
  const { user, can } = useAuth()
  const navigate = useNavigate()

  const [pr, setPr] = useState<any>({
    code: '', requester: '', requester_position: '', department: '', head_of_dept: '', head_of_dept_id: 0,
    purpose: '', company_id: 0, request_date: new Date().toISOString().slice(0, 10),
    need_date: '', is_urgent: false, note: '', status: 'draft', items: [],
    show_code_on_print: true, suggested_supplier: '', suggested_supplier_tax_code: '', suggested_supplier_contact: '',
    quote_filename: '', quote_file_url: '',
    // Task 4: NCC 2 cụm — req (bộ phận đề xuất) · pur (khảo sát/thu mua)
    supplier_req: { name: '', tax_code: '', contact: '' },
    supplier_pur: { name: '', tax_code: '', contact: '' },
    supplier_from_survey: false, can_edit_supplier_pur: false,
  })
  /** CR-071 — ứng viên đứng tên TBP trên phiếu (rỗng → ô về dạng chữ khóa như cũ). */
  const [deptHeads, setDeptHeads] = useState<any[]>([])
  const [companies, setCompanies] = useState<any[]>([])
  const [itemGroups, setItemGroups] = useState<any[]>([])
  const [groups, setGroups] = useState<string[]>([])
  const [units, setUnits] = useState<string[]>([])
  const [warehouses, setWarehouses] = useState<{ code: string; name: string }[]>([])
  const [employees, setEmployees] = useState<any[]>([])
  const [departments, setDepartments] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [docModal, setDocModal] = useState(false)
  const [docTypeLabels, setDocTypeLabels] = useState<Record<string, string>>({})
  const [editIdx, setEditIdx] = useState<number | null>(null)   // dòng đang mở popup chi tiết
  const [historyIdx, setHistoryIdx] = useState<number | null>(null)   // dòng đang mở popup lịch sử mua hàng
  const [origExp, setOrigExp] = useState('')   // giá trị 'thời gian dự kiến có hàng' lúc mở popup (để bắt lý do khi đổi)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [promptAction, setPromptAction] = useState<{type: 'reject'|'return'|'cancel', title: string, message: string, placeholder?: string} | null>(null)
  const [confirmAction, setConfirmAction] = useState<{type: 'complete'|'cancel_draft'|'copy'|'dispatch', title: string, message: string, confirmText?: string} | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [pos, setPos] = useState<any[] | null>(null)   // ĐMH tạo từ phiếu này (cùng mã PYC); null = chưa tải/không quyền → ẩn khối
  const [orderedMap, setOrderedMap] = useState<Record<string, number>>({})   // SL đã đặt theo mã hàng (gộp mọi ĐMH cùng PYC)
  const [poExceed, setPoExceed] = useState<{ msg: string; normal: any[]; all: any[] } | null>(null)   // popup cảnh báo đặt vượt
  const [showPoModal, setShowPoModal] = useState(false)   // popup danh sách ĐMH liên quan
  const [origImgs, setOrigImgs] = useState<any[]>([])        // ảnh GỐC của SP (từ catalog) trong popup chi tiết
  const [compareImgs, setCompareImgs] = useState<any[]>([])  // ảnh ĐỐI CHIẾU của dòng trong popup chi tiết
  const [compareOpen, setCompareOpen] = useState(false)      // mở lightbox chia đôi gốc | đối chiếu

  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items)).catch(() => {})
    api.get('/api/item-groups', { params: { page_size: 500 } }).then((r) => { setItemGroups(r.data.data.items); setGroups(r.data.data.items.map((x: any) => x.name)) }).catch(() => {})
    api.get('/api/units', { params: { page_size: 200 } }).then((r) => setUnits(r.data.data.items.map((x: any) => x.name))).catch(() => {})
    api.get('/api/warehouses', { params: { page_size: 200 } }).then((r) => setWarehouses(r.data.data.items.map((x: any) => ({ code: x.code, name: x.name })))).catch(() => {})
    api.get('/api/employees', { params: { page_size: 1000 } }).then((r) => setEmployees(r.data.data.items)).catch(() => {})
    api.get('/api/departments', { params: { page_size: 500 } }).then((r) => setDepartments(r.data.data.items)).catch(() => {})
  }, [])

  async function loadAll() {
    try {
      const r = await api.get(`${API}/${id}`)
      setPr(r.data.data)
      savedCodes.current = (r.data.data.items || []).map((it: any) => it.product_code || '')
    } catch (ex: any) {
      if ([403, 404].includes(ex?.response?.status)) { setNotFound(true); return }
      throw ex
    }
    api.get('/api/audit-logs', { params: { entity: 'purchase_request', entity_id: id } }).then((x) => setLogs(x.data.data)).catch(() => {})
    api.get('/api/attachments', { params: { entity: 'purchase_request', entity_id: id } }).then((x) => setFiles(x.data.data)).catch(() => {})
  }
  useEffect(() => { if (!isNew) { setNotFound(false); loadAll() } }, [id])
  // Chụp lại giá trị 'thời gian dự kiến có hàng' gốc khi MỞ popup dòng (để so khi lưu → bắt lý do nếu đổi)
  useEffect(() => {
    if (editIdx != null) setOrigExp(((pr.items || [])[editIdx]?.expected_date || '').trim())
    // reset ảnh của cụm khi đổi/đóng dòng (gallery sẽ tự nạp lại & báo qua onImages)
    setOrigImgs([]); setCompareImgs([]); setCompareOpen(false)
  }, [editIdx])

  // nhãn loại chứng từ để hiện badge cạnh file (đồng bộ đơn mua hàng)
  useEffect(() => {
    api.get('/api/attachments/doc-types')
      .then((x) => setDocTypeLabels(Object.fromEntries((x.data.data || []).map((t: any) => [t.value, t.label]))))
      .catch(() => {})
  }, [])

  // Tải danh sách ĐMH tạo từ phiếu này (lọc theo mã PYC). Lỗi/không quyền xem ĐMH → ẩn khối.
  useEffect(() => {
    if (isNew || !pr.code) { setPos(null); return }
    api.get('/api/purchase-orders', { params: { pr_code: pr.code, page_size: 200 }, _silent: true } as any)
      .then((r) => setPos((r.data.data.items || []).slice().sort((a: any, b: any) => b.id - a.id)))
      .catch(() => setPos(null))
    // SL đã đặt theo mã hàng → prefill 'còn thiếu' + cảnh báo đặt vượt khi tạo ĐMH
    api.get(`${API}/${id}/order-progress`, { _silent: true } as any)
      .then((r) => setOrderedMap(r.data.data.ordered || {}))
      .catch(() => setOrderedMap({}))
  }, [isNew, pr.code])

  useEffect(() => {
    if (!isNew || !user || pr.requester) return
    if (employees.length > 0) {
      const matchEmp = employees.find(e => e.email === user.email || e.full_name === user.full_name)
      if (matchEmp) { handleRequesterChange(matchEmp.full_name, true); return }
    }
    // Không có quyền xem DS nhân sự → điền theo tài khoản đăng nhập
    if (isStaff) {
      setPr((s: any) => ({
        ...s, requester: (user as any).full_name || '', requester_id: (user as any).employee_id || 0,
        department: (user as any).department_name || s.department,
        company_id: (user as any).company_id || s.company_id,
      }))
    }
  }, [isNew, employees, user])

  // Tự điền Trưởng bộ phận theo phòng ban (người yêu cầu không xem được DS nhân sự → hỏi server)
  useEffect(() => {
    if (!isNew || !pr.department || pr.head_of_dept) return
    api.get(`${API}/meta/dept-head`, { params: { department: pr.department } })
      .then((r) => { const h = r.data.data.head_of_dept; if (h) setH('head_of_dept', h) })
      .catch(() => {})
  }, [isNew, pr.department])

  // CR-071 — DS người có thể đứng tên TBP trên phiếu. Phòng nào cũng có thể có phó phòng /
  // quyền trưởng phòng cùng ký, mà ô này trước đây khóa cứng theo `Department.manager_id` nên
  // in ra sai tên. Ô CHỈ để lưu + in: chọn ai KHÔNG đổi quyền duyệt của bất kỳ ai.
  // Tra theo TÊN PHÒNG chứ không theo id phiếu, để màn tạo mới (chưa có id) cũng chọn được.
  useEffect(() => {
    if (!pr.department) { setDeptHeads([]); return }
    api.get(`${API}/meta/dept-head-candidates`, {
      params: { department: pr.department, company_id: Number(pr.company_id) || 0 },
    })
      .then((r) => setDeptHeads(r.data.data.items || []))
      .catch(() => setDeptHeads([]))
  }, [pr.department, pr.company_id])

  const editable = isNew || pr.status === 'draft' || pr.status === 'rejected'
  const isStaff = !can('purchase_request', 'approve') && !can('purchase_request', 'delete')
  const prLocked = ['cancelled', 'completed', 'done'].includes(pr.status)   // đã từ chối/hoàn thành → khóa thao tác
  const canAssignPurchaser = can('purchase_request', 'approve') && !prLocked   // phân bổ NSTM (chặn khi phiếu đã kết thúc)
  const canManage = can('purchase_request', 'cancel')             // admin/quản lý: hủy/trả/hoàn thành
  // Nút "Tạo ĐMH" chỉ hiện cho phòng thu mua / quản lý / admin (và có quyền tạo ĐMH)
  const isPurchaserDept = ((user as any)?.department_name || '').toLowerCase().includes('thu mua')
  const canCreatePO = can('purchase_order', 'create') && (isPurchaserDept || canManage || canAssignPurchaser)
  // CR-034: các trạng thái "làm việc được" (tạo ĐMH / hoàn thành phiếu). Bình thường phải qua
  // bước duyệt điều phối; nếu công tắc điều phối bị TẮT thì "Đã duyệt" cũng làm việc được
  // (phiếu cũ còn kẹt ở đó từ lúc công tắc còn bật).
  const workableStatuses = pr.dispatch_enabled === false
    ? ['approved', 'dispatched', 'processing'] : ['dispatched', 'processing']
  // Còn dòng nào chưa đặt hàng → vẫn cho tạo ĐMH (không ẩn khi mới hoàn thành 1 dòng).
  // CR-074: phải tính CẢ hai nhãn "chưa động tới", nếu không thì vừa lập đơn Nháp là nút
  // "Tạo ĐMH" biến mất, trong khi dòng đó vẫn có thể cần thêm đơn cho NCC khác.
  const hasUnorderedItem = (pr.items || []).some((it: any) => [LS_NO_PO, 'not_ordered'].includes(it.line_status || LS_NO_PO))
  // Chỉ cho Hoàn thành phiếu khi MỌI dòng đã ở điểm cuối (Hoàn thành/Hủy đơn)
  const allItemsDone = (pr.items || []).length > 0 && (pr.items || []).every((it: any) => ['completed', LS_CANCELLED].includes(it.line_status || LS_NO_PO))
  // Cột/trường "NSTM phụ trách" chỉ cho phía thu mua (is_purchaser = có quyền xử lý khảo sát).
  // Ẩn hoàn toàn với người yêu cầu (NSYC/employee) & trưởng bộ phận của họ (dept_head).
  const showAssigneeCol = can('survey_request', 'process')
  // Trạng thái dòng chỉ cho NSTM phụ trách chính dòng đó hoặc admin/quản lý
  const isAssignee = (it: any) => !!it.assignee && it.assignee === (user as any)?.emp_code
  const canLineStatus = (it: any) => canAssignPurchaser || canManage || isAssignee(it)
  const canEditNote = (it: any) => editable || canLineStatus(it)

  // NSTM = nhân sự phòng thu mua; hiển thị TÊN, lưu MÃ NV
  const purDeptIds = departments.filter(d => (d.name || '').toLowerCase().includes('thu mua')).map(d => d.id)
  const purchaserOptions = employees
    .filter(e => purDeptIds.includes(e.department_id) || (e.department_name || '').toLowerCase().includes('thu mua'))
    .map(e => ({ value: e.code, label: e.full_name }))
  const empName = (code: string) => employees.find(e => e.code === code)?.full_name || code
  const companyOptions = companies.map(c => ({ value: String(c.id), label: c.name }))
  const employeeOptions = employees.map(e => ({ value: e.full_name, label: e.full_name }))
  const warehouseOptions = warehouses.map(w => ({ value: w.name, label: `${w.code} - ${w.name}` }))
  // Nhãn hiển thị "MÃ - Tên" cho kho đã lưu (giá trị lưu vẫn là name); fallback name nếu không tìm thấy
  const whLabel = (name: string) => { const w = warehouses.find(w => w.name === name); return w ? `${w.code} - ${w.name}` : name }

  // Số ngày QĐ theo tên phân loại (mốc dài nhất, thiếu thì 15 ngày — khớp backend)
  const stdMap = useMemo(() => stdDaysMap(itemGroups), [itemGroups])
  // Ngày QĐ có hàng của 1 dòng = Ngày tiếp nhận phiếu + số ngày QĐ của phân loại
  const qdDate = (itemGroup: string) => regulatedDate(stdMap, itemGroup || '', pr.request_date || '')
  // CR-082 — các dòng khiến phiếu thành Đơn gấp (rỗng = không dòng nào vi phạm).
  const urgentLines = useMemo(() => urgentLinesPR(pr.items || [], pr.request_date || '', stdMap),
    [pr.items, pr.request_date, stdMap])
  // Tự tính lại cờ Đơn gấp khi dữ liệu nguồn (ngày tiếp nhận / dòng hàng) đổi. CR-082: chỉ BẬT,
  // KHÔNG bao giờ tự tắt — chiều tắt nằm ở effect bên dưới (CR-133).
  const recalcUrgent = (next: any) => {
    if (Object.keys(stdMap).length === 0 || next.is_urgent) return next
    return urgentLinesPR(next.items || [], next.request_date, stdMap).length
      ? { ...next, is_urgent: true } : next
  }
  // CR-133 — chiều TẮT của cờ Đơn gấp.
  //
  // CR-082 chỉ có chiều BẬT. Ticket 24/08/2026 (PYC22082603): chọn ngày cần hàng sớm hơn quy định
  // thì phiếu bật Đơn gấp kèm dòng chú thích; chọn LẠI cho đúng quy định thì chú thích biến mất
  // nhưng ô tick vẫn còn — phiếu đi tiếp với cờ gấp không còn lý do nào chống lưng.
  //
  // Chỉ được gỡ cờ do CHÍNH LUẬT NÀY bật; người dùng tự tick thì cờ thuộc về họ. Dấu chủ sở hữu
  // để trong ref `urgentAuto`, KHÔNG để trong state `pr`: `loadAll()` gọi `setPr(data)` thay
  // nguyên cục nên mọi khóa phụ gắn vào `pr` đều bị xóa sạch sau mỗi lần nạp lại phiếu.
  // Ref gắn kèm `key` (id phiếu) vì React Router dùng lại đúng một instance khi nhảy giữa hai
  // phiếu — không có key thì cờ của phiếu trước sẽ theo sang phiếu sau.
  //
  // Còn dòng vi phạm ⇒ luật sở hữu cờ (nó cưỡng bức bật, người dùng bỏ tick cũng bị bật lại),
  // nên cứ đánh dấu là của luật. Hết dòng vi phạm ⇒ chỉ gỡ nếu dấu đang thuộc về luật; phiếu mở
  // ra đã gấp sẵn mà không dòng nào vi phạm thì đó là người bật tay, không đụng vào.
  // Chiều tắt cũng chỉ áp cho phiếu còn sửa được: phiếu đã duyệt lưu ô tick thẳng qua API nên bỏ
  // tick ngầm ở client sẽ lệch với server.
  const urgentAuto = useRef<{ key: string; val: boolean }>({ key: '', val: false })
  const urgentDoc = isNew ? 'new' : String(id)
  useEffect(() => {
    if (!editable || Object.keys(stdMap).length === 0) return
    if (urgentAuto.current.key !== urgentDoc) urgentAuto.current = { key: urgentDoc, val: false }
    if (urgentLines.length > 0) {
      urgentAuto.current.val = true
      setPr((s: any) => (s.is_urgent ? s : { ...s, is_urgent: true }))
      return
    }
    if (!urgentAuto.current.val) return
    urgentAuto.current.val = false
    setPr((s: any) => (s.is_urgent ? { ...s, is_urgent: false } : s))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [editable, urgentLines.length, stdMap, urgentDoc])

  const setH = (k: string, v: any) =>
    setPr((s: any) => (k === 'request_date' ? recalcUrgent({ ...s, request_date: v }) : { ...s, [k]: v }))
  // Task 4: set 1 trường trong 1 cụm NCC (supplier_req | supplier_pur)
  const setSup = (cluster: 'supplier_req' | 'supplier_pur', field: string, v: string) =>
    setPr((s: any) => ({ ...s, [cluster]: { ...(s[cluster] || {}), [field]: v } }))
  const items = pr.items || []
  const setItem = (i: number, k: string, v: any) =>
    setPr((s: any) => recalcUrgent({ ...s, items: s.items.map((it: any, idx: number) => idx === i ? { ...it, [k]: v } : it) }))
  /** Chọn Phân loại -> điền luôn "Thời gian dự kiến có hàng" = NGÀY QĐ CÓ HÀNG (Ngày tiếp nhận +
   *  số ngày QĐ của phân loại). CHỈ với dòng CHƯA lưu và ô còn trống: dòng đã lưu mà đổi ngày dự
   *  kiến thì phải qua luật nhập lý do, còn ô người dùng đã tự điền/cố ý xóa trắng thì tôn trọng. */
  const setGroup = (i: number, v: string) =>
    setPr((s: any) => recalcUrgent({
      ...s, items: s.items.map((it: any, idx: number) => idx !== i ? it : {
        ...it, item_group: v, group_desc: groupDesc(v),
        ...(!it.id && !(it.expected_date || '').trim() ? { expected_date: qdDate(v) } : {}),
      }),
    }))
  const addItems = (n = 1) => setPr((s: any) => recalcUrgent({ ...s, items: [...(s.items || []), ...Array.from({ length: n }, () => ({ ...emptyItem }))] }))
  const delItem = (i: number) => setPr((s: any) => recalcUrgent({ ...s, items: s.items.filter((_: any, idx: number) => idx !== i) }))
  const copyItem = (i: number) => setPr((s: any) => {
    // Bỏ id VÀ ảnh chờ: dòng nhân bản là dòng khác, ảnh đối chiếu không đi theo (dòng đã lưu
    // cũng không được copy đính kèm) — giữ lại thì cùng bộ ảnh bị tải lên cho 2 dòng.
    const src = { ...s.items[i] }; delete src.id; delete src._pendingImgs
    const arr = [...s.items]; arr.splice(i + 1, 0, src); return recalcUrgent({ ...s, items: arr })
  })

  // Đổi NSTM phụ trách ngay trên bảng ngoài (chỉ người có quyền duyệt). Phiếu đã lưu -> auto-lưu; phiếu nháp -> theo nút Lưu.
  async function changeAssignee(i: number, val: string) {
    setItem(i, 'assignee', val)
    const it = items[i]
    if (!editable && it.id && canAssignPurchaser) {
      try { await api.patch(`${API}/${id}/assign`, { items: [{ id: it.id, assignee: val || '' }] }); toast.success('Đã cập nhật NSTM phụ trách'); loadAll() }
      catch (ex: any) { toast.error(ex?.response?.data?.error?.message || 'Lỗi cập nhật NSTM'); loadAll() }
    }
  }

  // Task 6: sửa "Thời gian dự kiến có hàng" ngay trên bảng ngoài (nếu có quyền dòng).
  // Phiếu nháp/mới -> chỉ đổi state, lưu theo nút Lưu. Phiếu đã gửi duyệt trở đi ->
  // auto-lưu qua item-status; đổi giá trị ĐÃ CÓ bắt nhập lý do (giống popup chi tiết dòng).
  const inlineExpOrig = useRef('')
  // Mã hàng đang lưu trên server — mốc để chỉ chặn TRÙNG MỚI (xem utils/lines.newDupCodes)
  const savedCodes = useRef<string[]>([])
  const dupCodes = useMemo(() => newDupCodes(items.map((it: any) => it.product_code || ''), savedCodes.current), [items])
  async function commitExpectedDate(i: number) {
    const it = items[i]
    if (editable || !it.id || !canLineStatus(it)) return   // nháp: theo nút Lưu; không quyền: bỏ qua
    const orig = (inlineExpOrig.current || '').trim()
    const newExp = (it.expected_date || '').trim()
    if (newExp === orig) return                            // không đổi
    let reason = ''
    if (orig) {
      const r = await askPrompt({ title: 'Đổi ngày dự kiến có hàng', message: `Đổi từ ${orig} sang ${newExp || '(để trống)'} — nhập lý do (bắt buộc):`, confirmText: 'Lưu' })
      if (r === null) { setItem(i, 'expected_date', orig); return }
      if (!r.trim()) { toast.error('Vui lòng nhập lý do thay đổi'); setItem(i, 'expected_date', orig); return }
      reason = r.trim()
    }
    try {
      await api.patch(`${API}/${id}/item-status`, { items: [{ id: it.id, line_status: it.line_status, progress_note: it.progress_note, note: it.note, expected_date: newExp, expected_date_reason: reason }] })
      toast.success('Đã cập nhật ngày dự kiến'); loadAll()
    } catch { loadAll() }
  }

  // Bật/tắt Đơn gấp. Phiếu còn sửa (nháp/mới) -> cập nhật local, lưu theo nút Lưu. Phiếu đã duyệt -> auto-lưu ngay + đồng bộ ĐMH.
  async function toggleUrgent(v: boolean) {
    // CR-133 — người dùng tự bấm ⇒ cờ thuộc về họ: trả dấu chủ sở hữu về tay người dùng để luật
    // tự động không gỡ tick này.
    urgentAuto.current = { key: urgentDoc, val: false }
    setH('is_urgent', v)
    if (!isNew && !editable && pr.id) {
      try { await api.patch(`${API}/${id}/urgent`, { is_urgent: v }); toast.success('Đã cập nhật Đơn gấp'); loadAll() }
      catch (ex: any) { toast.error(ex?.response?.data?.error?.message || 'Lỗi cập nhật Đơn gấp'); loadAll() }
    }
  }

  const subtotal = items.reduce((s: number, it: any) => s + (Number(it.qty) || 0) * (Number(it.price) || 0), 0)  // tiền hàng chưa VAT
  const totalWithVat = items.reduce((s: number, it: any) => s + lineAmount(it), 0)                                // tổng gồm VAT
  const vatAmount = totalWithVat - subtotal

  const groupDesc = (name: string) => {
    const g = itemGroups.find(x => x.name === name)
    if (!g) return ''
    const p: string[] = []
    if (g.std_days) p.push(`Hàng NCC có sẵn: ${g.std_days} ngày`)
    if (g.std_days_unavail) p.push(`không sẵn: ${g.std_days_unavail} ngày`)
    return p.join(' · ')
  }

  /** Trưởng bộ phận MẶC ĐỊNH lấy theo `Department.manager_id` (nguồn duy nhất) — hỏi server,
   *  không đoán theo chức danh nhân sự cùng phòng. Phòng chưa gán trưởng → để trống.
   *  Đổi phòng thì bỏ luôn người đã chọn tay, không thì phiếu in tên trưởng phòng cũ. */
  const fetchDeptHead = (deptName: string) => {
    if (!deptName) { setPr((s: any) => ({ ...s, head_of_dept: '', head_of_dept_id: 0 })); return }
    api.get(`${API}/meta/dept-head`, { params: { department: deptName } })
      .then((r) => setPr((s: any) => ({
        ...s, head_of_dept: r.data.data.head_of_dept || '', head_of_dept_id: 0,
      })))
      .catch(() => {})
  }

  const handleRequesterChange = (empName: string, isAutoFill = false) => {
    const emp = employees.find(e => e.full_name === empName)
    if (!emp) { setPr((s: any) => ({ ...s, requester: empName, requester_id: 0 })); return }
    const dept = departments.find(d => d.id === emp.department_id)
    const deptName = dept ? dept.name : ''
    const keepDept = isAutoFill && pr.department ? pr.department : ''
    setPr((s: any) => ({
      ...s,
      requester: emp.full_name,
      requester_id: emp.id || 0,
      // Chức vụ = chức danh trong hồ sơ nhân sự. KHÔNG lấy `role_name` — đó là VAI TRÒ dùng
      // phần mềm (vd. "Điều phối"), không phải chức vụ.
      requester_position: isAutoFill && s.requester_position ? s.requester_position : (emp.position || ''),
      department: keepDept || deptName,
      company_id: (isAutoFill && s.company_id) ? s.company_id : (emp.company_id || s.company_id),
    }))
    fetchDeptHead(keepDept || deptName)
  }

  // Chọn SP từ ô tìm kiếm (nhận cả object) → tự điền tên/ĐVT/phân loại
  // Chọn 1 lần mua trước từ popup lịch sử → CHỈ điền vào state dòng, KHÔNG tự lưu.
  // VAT giờ là ô nhập số nên nhận thẳng mọi thuế suất trong lịch sử (CR-058); trước đây phải
  // lọc qua VAT_OPTS vì <select> không có option tương ứng thì rơi về rỗng. Chỉ chặn số rác
  // (âm / ≥ 100 / không phải số) — dòng legacy nhập từ Excel có VAT bẩn thì giữ giá trị cũ.
  const applyHistory = (i: number, h: HistoryPick) => {
    const vatHopLe = Number.isFinite(Number(h.vat)) && Number(h.vat) >= 0 && Number(h.vat) < 100
    setPr((s: any) => recalcUrgent({
      ...s,
      items: s.items.map((it: any, idx: number) => idx === i ? {
        ...it, unit: h.unit || it.unit, qty: h.qty_order, price: h.price,
        vat_pct: vatHopLe ? Number(h.vat) : it.vat_pct,
      } : it),
    }))
    toast.success('Đã điền giá từ lịch sử — bấm Lưu để ghi nhận')
  }

  const applyProduct = (i: number, prod: any) => {
    if (!prod) { setItem(i, 'product_code', ''); return }
    setPr((s: any) => recalcUrgent({
      ...s,
      items: s.items.map((it: any, idx: number) => {
        if (idx !== i) return it
        const grp = prod.item_group || it.item_group
        return {
          ...it, product_code: prod.code, product_name: prod.name,
          unit: prod.unit || it.unit, item_group: grp, group_desc: groupDesc(grp),
          // Phân loại đến từ danh mục SP cũng điền ngày dự kiến như khi chọn tay (xem setGroup)
          ...(!it.id && !(it.expected_date || '').trim() ? { expected_date: qdDate(grp) } : {}),
        }
      }),
    }))
  }

  function validate(forSubmit: boolean): string {
    if (!pr.company_id) return 'Vui lòng chọn Công ty'
    if (!pr.requester) return 'Vui lòng chọn Nhân sự yêu cầu'
    const valid = items.filter((it: any) => it.product_name)
    if (valid.length === 0) return 'Cần ít nhất 1 sản phẩm'
    if (dupCodes.length) return `Mã hàng bị trùng: ${dupCodes.join(', ')}. Mỗi mã chỉ được 1 dòng — gộp số lượng vào một dòng hoặc đổi mã.`
    // Chi tiết bắt buộc (mã hàng/SL/kho/ngày cần hàng) CHỈ khi Gửi duyệt — lưu nháp / đóng popup dòng thì không bắt
    if (forSubmit) {
      for (const it of valid) {
        if (!it.product_code) return `Sản phẩm "${it.product_name}" cần chọn Mã hàng (chọn từ danh mục)`
        if (!(Number(it.qty) > 0)) return `Sản phẩm "${it.product_name}" cần Số lượng > 0`
        if (!it.warehouse) return `Sản phẩm "${it.product_name}" cần chọn Kho nhận`
        if (!it.required_date) return `Sản phẩm "${it.product_name}" cần nhập Ngày cần hàng`
      }
    }
    return ''
  }

  /**
   * Ghép dòng vừa GỬI với dòng SERVER TRẢ VỀ để biết id thật của dòng mới tạo.
   * KHÔNG dựa vào thứ tự: server trả dòng cũ (giữ nguyên id) lẫn dòng mới (id vừa cấp)
   * không theo thứ tự đã gửi. Ưu tiên khớp id, rồi MÃ HÀNG (backend chặn trùng mã trên
   * cùng phiếu nên mã là khóa chắc chắn), cuối cùng mới tới tên — cho dòng chưa có mã.
   */
  function mapLineIds(sent: any[], returned: any[]): (number | null)[] {
    const conLai = [...(returned || [])]
    const ket: (number | null)[] = new Array(sent.length).fill(null)
    const lay = (dk: (r: any) => boolean) => {
      const i = conLai.findIndex(dk)
      return i < 0 ? null : conLai.splice(i, 1)[0]
    }
    sent.forEach((it, i) => { if (it.id) { const r = lay((x) => x.id === it.id); if (r) ket[i] = r.id } })
    sent.forEach((it, i) => {
      if (ket[i] || !it.product_code) return
      const r = lay((x) => (x.product_code || '') === it.product_code)
      if (r) ket[i] = r.id
    })
    sent.forEach((it, i) => {
      if (ket[i]) return
      const r = lay((x) => (x.product_name || '') === (it.product_name || ''))
      if (r) ket[i] = r.id
    })
    return ket
  }

  // Tải ảnh đối chiếu đang giữ ở client lên NGAY SAU khi dòng đã có id thật.
  // Lỗi 1 dòng không được làm hỏng việc lưu phiếu — chỉ báo để người dùng đính kèm lại.
  async function uploadPendingLineImgs(sent: any[], returned: any[]) {
    if (!sent.some((it) => (it._pendingImgs || []).length)) return
    const ids = mapLineIds(sent, returned)
    for (let i = 0; i < sent.length; i++) {
      const fs: File[] = sent[i]._pendingImgs || []
      if (!fs.length || !ids[i]) continue
      const fd = new FormData()
      fd.append('entity', 'purchase_request_line_image')
      fd.append('entity_id', String(ids[i]))
      fs.forEach((f) => fd.append('files', f))
      try { await api.post('/api/attachments', fd) }
      catch { toast.error(`Chưa tải được ảnh đối chiếu của dòng "${sent[i].product_name || i + 1}" — vui lòng đính kèm lại`) }
    }
  }

  async function save(submitAfterSave = false): Promise<boolean> {
    const v = validate(submitAfterSave)
    if (v) { toast.error(v); return false }
    const guiItems = items.filter((it: any) => it.product_name)
    const validNeedDates = guiItems
      .map((it: any) => it.required_date)
      .filter((d: any) => typeof d === 'string' && d.trim() !== '')
    const earliestNeedDate = validNeedDates.length > 0 ? [...validNeedDates].sort()[0] : ''
    const body = {
      company_id: Number(pr.company_id) || 0, requester: pr.requester, requester_id: Number(pr.requester_id) || 0, requester_position: pr.requester_position,
      department: pr.department, head_of_dept: pr.head_of_dept,
      head_of_dept_id: Number(pr.head_of_dept_id) || 0, purpose: pr.purpose,
      request_date: pr.request_date, need_date: earliestNeedDate || pr.need_date || '', is_urgent: pr.is_urgent, note: pr.note,
      show_code_on_print: pr.show_code_on_print,
      quote_filename: pr.quote_filename, quote_file_url: pr.quote_file_url,
      // Task 4: gửi 2 cụm NCC (BE tự chặn cụm 'pur' nếu không có quyền supplier.write)
      supplier_req: { name: pr.supplier_req?.name || '', tax_code: pr.supplier_req?.tax_code || '', contact: pr.supplier_req?.contact || '' },
      supplier_pur: { name: pr.supplier_pur?.name || '', tax_code: pr.supplier_pur?.tax_code || '', contact: pr.supplier_pur?.contact || '' },
      // `_pendingImgs` là File giữ ở client (ảnh đối chiếu của dòng chưa lưu) — không phải
      // dữ liệu phiếu, phải bỏ khỏi body rồi upload riêng sau khi có id dòng.
      items: guiItems.map((it: any) => { const { _pendingImgs, ...rest } = it; return rest }),
    }
    try {
      if (isNew) {
        const r = await api.post(API, body)
        const nid = r.data.data.id
        await uploadPendingLineImgs(guiItems, r.data.data?.items || [])
        if (submitAfterSave) await api.post(`${API}/${nid}/submit`)
        navigate(`/purchase-requests/${nid}`)
      } else {
        const r = await api.patch(`${API}/${id}`, body)
        await uploadPendingLineImgs(guiItems, r.data.data?.items || [])
        if (submitAfterSave) await api.post(`${API}/${id}/submit`)
        toast.success('Đã lưu'); loadAll()
      }
      return true
    } catch { /* interceptor đã toast lỗi */ return false }
  }

  async function action(path: string, payload: any = {}) {
    try {
      const r = await api.post(`${API}/${id}/${path}`, payload)
      // Điều phối: báo luôn kết quả tự động phân bổ — còn dòng nào chưa có người thì phải chọn tay
      if (path === 'dispatch' && r?.data?.message) toast.success(r.data.message)
      loadAll()
    }
    catch { /* interceptor đã toast lỗi */ }
  }

  async function copyDoc() {
    try { const r = await api.post(`${API}/${id}/copy`); navigate(`/purchase-requests/${r.data.data.id}`) }
    catch { /* interceptor đã toast lỗi */ }
  }

  // Điều hướng sang form ĐMH mới với header từ phiếu + danh sách dòng đã tính sẵn
  function goPO(items: any[]) {
    // NSPT = người phụ trách dòng ở YCMH. Lấy từ pr.items (có 'assignee'); items truyền vào
    // đã map lại KHÔNG kèm assignee nên phải dò trên phiếu gốc → hiện sẵn trước khi bấm Tạo.
    const firstAssignee = ((pr.items || []).find((it: any) => it.assignee) || {}).assignee
    const fromPr = {
      pr_code: pr.code,
      company_id: pr.company_id,
      department: pr.department,
      nspt: firstAssignee ? empName(firstAssignee) : '',   // NSPT = người phụ trách dòng ở YCMH (rỗng → ĐMH tự lấy người tạo)
      supplier_name: pr.suggested_supplier || '',
      supplier_code: '',                        // PR chỉ có tên NCC đề xuất, không có mã
      supplier_tax_code: pr.suggested_supplier_tax_code || '',   // để ĐMH tự khớp NCC trong danh mục
      vat_rate: Number(pr.vat_rate) || 0.08,
      is_urgent: !!pr.is_urgent,
      note: pr.note || '',
      items,
    }
    navigate('/purchase-orders/new', { state: { fromPr } })
  }

  // Tạo ĐMH từ phiếu đã duyệt: prefill SL theo 'còn thiếu' (yêu cầu − đã đặt), cảnh báo dòng đã đặt đủ/vượt
  function createPO() {
    const whCode = (name: string) => warehouses.find((w) => w.name === name)?.code || ''
    const mk = (it: any, qty: number) => ({
      product_code: it.product_code, product_name: it.product_name,
      item_group: it.item_group, unit: it.unit,
      required_date: it.required_date || '',   // Ngày cần hàng ở YCMH → Ngày yêu cầu có hàng ở ĐMH
      expected_date: it.expected_date || '',   // Dự kiến có hàng: chép xuống ĐMH (backend cũng tự chép nếu để trống)
      qty_request: qty, qty_order: qty,
      price: Number(it.price) || 0, vat: Number(it.vat_pct) || 0,   // Task 4: VAT theo TỪNG DÒNG PYC
      warehouse_code: whCode(it.warehouse), note: it.note || '',
    })
    const lines = (pr.items || []).filter((it: any) => it.product_name)
    const normal: any[] = [], exceeded: any[] = [], exceededMsg: string[] = []
    for (const it of lines) {
      const req = Number(it.qty) || 0
      const ordered = Number(orderedMap[it.product_code] || 0)
      const remaining = req - ordered
      if (remaining > 0) normal.push(mk(it, remaining))
      else { exceeded.push(mk(it, req)); exceededMsg.push(`${it.product_name} (đã đặt ${fmt(ordered)}/${fmt(req)})`) }
    }
    if (exceeded.length === 0) { goPO(normal); return }
    // Có dòng đã đặt đủ/vượt → cảnh báo, cho chọn mua thêm hay chỉ SP còn thiếu
    setPoExceed({ msg: exceededMsg.join('; '), normal, all: [...normal, ...exceeded] })
  }

  // CR-026: YCMH bị trả lại / từ chối → mở màn tạo Yêu cầu báo giá điền sẵn từ phiếu này.
  // Dữ liệu đi kèm điều hướng (state), KHÔNG tạo bản ghi nào cho tới khi người dùng bấm Lưu.
  // YCBG không có ô mã/tên hàng nên tên hàng được gộp vào "Chi tiết thông số" để khỏi mất thông tin.
  function createSurveyRequest() {
    const lines = (pr.items || [])
      .filter((it: any) => it.product_name)
      .map((it: any) => ({
        received_date: '', result_due_date: '',
        item_group: it.item_group || '',
        requirement_detail: [it.product_name, it.group_desc].filter(Boolean).join(' — '),
        other_requirement: it.note || '',
        request_qty: Number(it.qty) || 0,
        uom: it.unit || '',
        proposed_price: Number(it.price) || 0,
        src_pr_item_id: it.id || 0,   // CR-027: ảnh đối chiếu của dòng này sẽ được kéo sang khi Lưu
      }))
    if (!lines.length) { toast.error('Phiếu không còn dòng sản phẩm nào để khảo sát'); return }
    navigate('/survey-requests/new', {
      state: {
        fromPr: {
          pr_id: Number(id) || 0, pr_code: pr.code,
          company_id: pr.company_id || 0,
          requester: pr.requester || '', requester_id: pr.requester_id || 0,
          requester_position: pr.requester_position || '',
          department: pr.department || '', head_of_dept: pr.head_of_dept || '',
          purpose: pr.purpose || '', note: pr.note || '',
          lines,
        },
      },
    })
  }

  async function handleDelete() {
    try {
      await api.delete(`${API}?ids=${id}`)
      navigate('/purchase-requests')
    } catch { /* interceptor đã toast lỗi */ }
  }

  // Lưu popup chi tiết dòng khi phiếu KHÔNG còn ở trạng thái sửa (đã gửi duyệt trở đi)
  async function savePopupLine(it: any) {
    try {
      if (canLineStatus(it)) {
        // Thời gian dự kiến có hàng: đổi giá trị ĐÃ CÓ phải kèm lý do (rỗng → cập nhật tự do).
        const newExp = (it.expected_date || '').trim()
        let expReason = ''
        if (origExp && newExp !== origExp) {
          const r = await askPrompt({ title: 'Đổi thời gian dự kiến có hàng', message: `Đổi từ ${origExp} sang ${newExp || '(để trống)'} — nhập lý do (bắt buộc):`, confirmText: 'Lưu' })
          if (r === null) return
          if (!r.trim()) { toast.error('Vui lòng nhập lý do thay đổi'); return }
          expReason = r.trim()
        }
        await api.patch(`${API}/${id}/item-status`, { items: [{ id: it.id, line_status: it.line_status, progress_note: it.progress_note, note: it.note, expected_date: it.expected_date || '', expected_date_reason: expReason }] })
      }
      if (canAssignPurchaser)
        await api.patch(`${API}/${id}/assign`, { items: [{ id: it.id, assignee: it.assignee || '' }] })
      toast.success('Đã cập nhật dòng'); setEditIdx(null); loadAll()
    } catch { /* interceptor đã toast lỗi */ }
  }

  const isLogShown = !isNew && logs.length > 0
  const edit = editIdx != null ? items[editIdx] : null

  if (notFound) return <NotFound backTo="/purchase-requests" message="Không tìm thấy phiếu yêu cầu mua hàng này hoặc bạn không có quyền truy cập." />

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/purchase-requests')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>{isNew ? 'Tạo Yêu cầu Thu mua mới' : (pr.code || '')}</h2>
        {!isNew && prBadge(pr.status)}
        <span style={{ flex: 1 }} />
        {/* ── Nhóm tiện ích + destructive (trái) ── */}
        {!isNew && <button className="btn ghost" onClick={() => window.open(`/print/purchase-request/${id}`, '_blank')}><i className="ti ti-printer" />In phiếu</button>}
        {!isNew && pos && pos.length > 0 && <button className="btn ghost" onClick={() => setShowPoModal(true)}><i className="ti ti-shopping-cart" />ĐMH liên quan ({pos.length})</button>}
        {!isNew && can('purchase_request', 'create') && <button className="btn ghost" onClick={() => setConfirmAction({ type: 'copy', title: 'Nhân bản', message: 'Nhân bản phiếu này thành phiếu Nháp mới?', confirmText: 'Nhân bản' })}><i className="ti ti-copy" />Nhân bản</button>}
        {/* CR-026: phiếu bị trả lại / từ chối → chuyển hướng đi khảo sát lại, không phải gõ lại từ đầu.
            Màu (CR-027): phiếu ĐÃ TỪ CHỐI bị khóa, không còn nút workflow nào → đây là việc cần làm tiếp,
            để nút đặc cho nổi. Phiếu BỊ TRẢ LẠI vẫn sửa & "Gửi duyệt" lại được (nút đặc bên phải) nên
            nút này để dạng nhạt hơn, tránh 2 nút chính đá nhau. */}
        {!isNew && ['rejected', 'cancelled'].includes(pr.status) && can('survey_request', 'create') && (
          <button className={pr.status === 'cancelled' ? 'btn' : 'btn secondary'} onClick={createSurveyRequest}>
            <i className="ti ti-clipboard-list" />Tạo yêu cầu báo giá
          </button>
        )}
        {!isNew && ['draft', 'rejected', 'cancelled'].includes(pr.status) && can('purchase_request', 'delete') && (
          <button className="btn ghost err" onClick={() => setConfirmDelete(true)}><i className="ti ti-trash" />Xóa phiếu</button>
        )}
        {!isNew && <span style={{ width: 1, alignSelf: 'stretch', background: 'var(--border)', margin: '2px 4px' }} />}
        {/* ── Nhóm workflow + chính (phải): Duyệt · Trả về · Từ chối cùng nhóm ── */}
        {editable && (
          <button className="btn secondary" onClick={() => save(false)}><i className="ti ti-device-floppy" />Lưu</button>
        )}
        {editable && (
          <button className="btn" onClick={() => save(true)}><i className="ti ti-send" />Gửi duyệt</button>
        )}
        {/* Duyệt bước 1 (trưởng bộ phận). Dùng cờ can_approve của server chứ không dùng can() —
            Admin thu mua cũng có quyền approve nhưng PHẠM VI của họ không duyệt được bước này. */}
        {!isNew && pr.can_approve && (
          <button className="btn" onClick={() => action('approve')}><i className="ti ti-check" />Duyệt</button>
        )}
        {!isNew && (canManage || pr.can_approve) && !['draft', 'rejected', 'cancelled', 'completed', 'done'].includes(pr.status) && (
          <button className="btn ghost" style={{ color: '#d97706', borderColor: '#fcd34d' }} onClick={() => setPromptAction({ type: 'return', title: 'Trả về', message: 'Lý do trả về (để người yêu cầu sửa & gửi duyệt lại):' })}><i className="ti ti-corner-up-left" />Trả về</button>
        )}
        {!isNew && pr.can_approve && (
          <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={() => setPromptAction({ type: 'cancel', title: 'Từ chối phiếu', message: 'Lý do từ chối (khóa phiếu, không sửa lại được):' })}><i className="ti ti-ban" />Từ chối</button>
        )}
        {/* CR-034: duyệt lần 2 phía thu mua (điều phối — tự động phân bổ NSTM). Cờ can_dispatch do
            server tính vì FE không biết PHẠM VI của grant (trưởng phòng cũng có quyền approve). */}
        {!isNew && pr.can_dispatch && (
          <button className="btn" onClick={() => setConfirmAction({ type: 'dispatch', title: 'Duyệt điều phối', message: 'Duyệt và điều phối phiếu này? Hệ thống sẽ tự động phân bổ nhân sự thu mua phụ trách theo phân loại hàng, sau đó mới tạo được đơn mua hàng.', confirmText: 'Duyệt' })}><i className="ti ti-check" />Duyệt</button>
        )}
        {!isNew && canCreatePO && workableStatuses.includes(pr.status) && hasUnorderedItem && (
          <button className="btn" onClick={createPO}><i className="ti ti-shopping-cart" />Tạo đơn mua hàng</button>
        )}
        {!isNew && canManage && workableStatuses.includes(pr.status) && (
          <button className="btn secondary" onClick={() => { if (!allItemsDone) { toast.error('Chưa có sản phẩm đặt hàng hoàn tất — chỉ hoàn thành khi mọi sản phẩm đã Hoàn thành/Hủy.'); return } setConfirmAction({ type: 'complete', title: 'Hoàn thành', message: 'Đánh dấu phiếu HOÀN THÀNH?', confirmText: 'Đồng ý' }) }}><i className="ti ti-checks" />Hoàn thành</button>
        )}
        {/* ── Từ chối (khóa phiếu) ở giai đoạn đã duyệt/đang xử lý ── */}
        {!isNew && canManage && !['draft', 'submitted', 'rejected', 'cancelled', 'completed', 'done'].includes(pr.status) && (
          <>
            <span style={{ width: 1, alignSelf: 'stretch', background: 'var(--border)', margin: '2px 4px' }} />
            <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={() => setPromptAction({ type: 'cancel', title: 'Từ chối phiếu', message: 'Lý do từ chối (khóa phiếu):' })}><i className="ti ti-ban" />Từ chối</button>
          </>
        )}
      </div>

      {/* CR-034: phiếu "Đã duyệt" trông như xong việc nhưng thật ra chưa — nói rõ để khỏi nhầm.
          Công tắc điều phối TẮT thì không còn bước này nên cũng không hiện dòng nào. */}
      {!isNew && pr.status === 'approved' && pr.dispatch_enabled !== false && (
        <div className="card" style={{ padding: '10px 14px', marginBottom: 14, background: '#fffbeb', border: '1px solid #fde68a' }}>
          <div style={{ fontSize: 13, color: '#92400e' }}>
            <i className="ti ti-info-circle" /> <b>Trưởng bộ phận đã duyệt — còn chờ thu mua duyệt lần 2 (điều phối).</b>{' '}
            {pr.can_dispatch
              ? 'Bấm Duyệt để hệ thống tự phân bổ nhân sự thu mua phụ trách; trước đó phiếu chưa tạo được đơn mua hàng.'
              : 'Admin / Quản lý thu mua duyệt lần nữa thì hệ thống mới phân bổ nhân sự phụ trách và mở khóa tạo đơn mua hàng.'}
          </div>
        </div>
      )}

      <PromptModal
        open={!!promptAction}
        title={promptAction?.title}
        message={promptAction?.message || ''}
        placeholder={promptAction?.placeholder}
        confirmText="Xác nhận"
        cancelText="Đóng"
        variant="danger"
        onConfirm={(reason) => {
          if (promptAction && reason !== null) {
            action(promptAction.type, { reason })
          }
          setPromptAction(null)
        }}
        onCancel={() => setPromptAction(null)}
      />

      <ConfirmModal
        open={!!confirmAction}
        title={confirmAction?.title}
        message={confirmAction?.message || ''}
        confirmText={confirmAction?.confirmText || "Xác nhận"}
        cancelText="Đóng"
        variant={confirmAction?.type === 'complete' ? 'info' : 'warn'}
        onConfirm={() => {
          if (confirmAction?.type === 'complete') action('complete')
          if (confirmAction?.type === 'dispatch') action('dispatch')
          if (confirmAction?.type === 'cancel_draft') action('cancel', { reason: '' })
          if (confirmAction?.type === 'copy') copyDoc()
          setConfirmAction(null)
        }}
        onCancel={() => setConfirmAction(null)}
      />

      <ConfirmModal
        open={!!poExceed}
        title="Số lượng đã đặt đủ/vượt"
        message={`Các sản phẩm sau đã đặt đủ hoặc vượt số lượng yêu cầu: ${poExceed?.msg || ''}. Bạn vẫn muốn tạo đơn mua hàng?`}
        confirmText="Vẫn mua thêm"
        cancelText="Chỉ SP còn thiếu"
        variant="info"
        onConfirm={() => { const p = poExceed; setPoExceed(null); if (p) goPO(p.all) }}
        onCancel={() => { const p = poExceed; setPoExceed(null); if (p) { if (p.normal.length) goPO(p.normal); else toast.info('Không còn sản phẩm cần đặt') } }}
        onClose={() => setPoExceed(null)}
      />

      <ConfirmModal
        open={confirmDelete}
        title="Xác nhận xóa"
        message="Bạn có chắc chắn muốn xóa phiếu mua hàng này không?"
        confirmText="Xóa"
        cancelText="Hủy"
        variant="danger"
        onConfirm={() => { setConfirmDelete(false); handleDelete(); }}
        onCancel={() => setConfirmDelete(false)}
      />

      <div className={isLogShown ? 'detail-grid' : ''}>
        <div>


          {/* Thông tin chung */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title">Thông tin chung</h3>
            <div className="form-grid">
              {/* Mã phiếu do hệ thống tự sinh khi lưu → chỉ hiện khi xem chi tiết, ẩn lúc tạo mới */}
              {!isNew && (
                <>
                  <div className="form-row">
                    <label>Mã phiếu yêu cầu</label>
                    <input value={pr.code || ''} disabled />
                  </div>
                  <div className="form-row">
                    <label>Ngày tạo</label>
                    <input value={fmtDateTime(pr.created_at) || '—'} disabled />
                  </div>
                </>
              )}
              <div className="form-row">
                <label>Ngày tiếp nhận <span className="req">*</span></label>
                <DateInput value={pr.request_date || ''} disabled={!editable} onChange={(v) => setH('request_date', v)} />
              </div>
              <div className="form-row">
                <label>Công ty nhận hóa đơn <span className="req">*</span></label>
                <SearchSelect value={String(pr.company_id || '')}
                  onChange={(v) => setH('company_id', Number(v) || 0)} options={companyOptions}
                  disabled={!editable} placeholder="Chọn công ty" />
              </div>
              <div className="form-row">
                <label>Nhân sự YC <span className="req">*</span></label>
                <SearchSelect value={pr.requester || ''}
                  onChange={(v) => handleRequesterChange(v)} options={employeeOptions}
                  disabled={!editable || isStaff} placeholder="Chọn nhân sự" />
              </div>
              <div className="form-row">
                <label>Bộ phận YC <span className="req">*</span></label>
                <input value={pr.department || ''} placeholder="Tự động theo Nhân sự" disabled />
              </div>
              <div className="form-row">
                <label>Chức vụ (Nếu có)</label>
                <input value={pr.requester_position || ''} placeholder="Tự động theo Nhân sự" disabled={!editable} onChange={(e) => setH('requester_position', e.target.value)} />
              </div>
              <div className="form-row">
                <label>Trưởng bộ phận (TBP) / Người liên hệ</label>
                {/* CR-071: phòng có nhiều người ký được (phó phòng, quyền trưởng phòng) thì chọn
                    đúng người để IN. Không đổi quyền duyệt — ai có quyền vẫn duyệt như cũ.
                    Chưa nạp được DS (hoặc phiếu đã khóa) thì giữ nguyên ô chữ cũ. */}
                {editable && deptHeads.length > 0 ? (
                  <select
                    value={pr.head_of_dept_id ? String(pr.head_of_dept_id) : ''}
                    title="Chọn người đứng tên Trưởng bộ phận trên phiếu in"
                    onChange={(e) => {
                      const v = Number(e.target.value) || 0
                      const c = deptHeads.find((x: any) => x.employee_id === v)
                      setPr((s: any) => ({
                        ...s,
                        head_of_dept_id: v,
                        // Bỏ chọn → trả tên về mặc định của phòng, đừng để trống ô in.
                        head_of_dept: c ? c.name : s.head_of_dept,
                      }))
                      if (!v) fetchDeptHead(pr.department)
                    }}
                  >
                    <option value="">{pr.head_of_dept ? `${pr.head_of_dept} (mặc định của phòng)` : '— Chọn —'}</option>
                    {deptHeads.map((c: any) => (
                      <option key={c.employee_id} value={c.employee_id}>
                        {c.name}{c.position ? ` - ${c.position}` : ''}
                      </option>
                    ))}
                  </select>
                ) : (
                  <input value={pr.head_of_dept || ''} placeholder="Tự động theo phòng ban của người yêu cầu" disabled
                    title="Lấy theo Trưởng bộ phận đã gán ở màn hình Phòng ban" />
                )}
              </div>
              <div className="form-row">
                <label>Tùy chọn phiếu</label>
                <div style={{ display: 'flex', gap: 16, alignItems: 'center', minHeight: 40, flexWrap: 'wrap' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', margin: 0, color: 'var(--red)' }}>
                    <input type="checkbox" checked={!!pr.is_urgent} disabled={prLocked} onChange={(e) => toggleUrgent(e.target.checked)} style={{ width: 18, height: 18 }} />
                    Đơn gấp
                  </label>
                  {/* CR-082 — nói rõ vì sao phiếu bị đánh dấu gấp (danh sách dòng vi phạm ở tooltip) */}
                  {urgentLines.length > 0 && (
                    <span style={{ fontSize: 12, color: 'var(--red)' }} title={urgentLines.join('\n')}>
                      Tự động: {urgentLines.length} dòng có ngày cần hàng sớm hơn thời gian quy định của phân loại
                      {editable ? ' — hệ thống đánh dấu Đơn gấp khi lưu' : ''}
                    </span>
                  )}
                </div>
              </div>
              <div className="form-row">
                <label>Mục đích mua hàng <span className="req">*</span></label>
                <textarea placeholder="Nhập mục đích mua hàng/dịch vụ..." style={{ minHeight: 80 }} value={pr.purpose || ''} disabled={!editable} onChange={(e) => setH('purpose', e.target.value)} />
              </div>
              <div className="form-row">
                <label>Nội dung mua hàng</label>
                <textarea placeholder="Nhập nội dung chi tiết..." style={{ minHeight: 80 }} value={pr.note || ''} disabled={!editable} onChange={(e) => setH('note', e.target.value)} />
              </div>
            </div>
          </div>

          {/* Mặt hàng */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 className="sec-title" style={{ margin: 0, borderBottom: 'none', paddingBottom: 0 }}>Danh sách Sản phẩm Yêu cầu</h3>
              {editable && <button className="btn ghost" onClick={() => addItems(1)} style={{ height: 30, padding: '0 10px', fontSize: 13 }}><i className="ti ti-plus" /> Thêm SP</button>}
              {!editable && !isNew && <span style={{ fontSize: 12, color: 'var(--muted)' }}><i className="ti ti-device-floppy" /> Trạng thái tự đồng bộ từ ĐMH · thay đổi phụ trách được lưu tự động</span>}
            </div>
            <div className="items-scroll">
              <table className="items-table" style={{ minWidth: showAssigneeCol ? 1697 : 1537, tableLayout: 'fixed' }}>
                <thead>
                  <tr>
                    <th style={{ width: 34, textAlign: 'center' }}>No.</th>
                    <th style={{ width: 215, textAlign: 'left' }}>Mã hàng *</th>
                    <th style={{ width: 265, textAlign: 'left' }}>Tên sản phẩm *</th>
                    <th style={{ width: 130, textAlign: 'left' }}>Kho nhận</th>
                    <th style={{ width: 140, textAlign: 'left' }}>Phân loại</th>
                    <th style={{ width: 80, textAlign: 'left' }}>ĐVT</th>
                    <th style={{ width: 70, textAlign: 'right' }}>SL</th>
                    <th style={{ width: 100, textAlign: 'right' }}>Đơn giá</th>
                    <th style={{ width: 64, textAlign: 'right' }} title="% VAT theo dòng">VAT%</th>
                    <th style={{ width: 120, textAlign: 'right' }} title="Thành tiền gồm VAT">Thành tiền</th>
                    {/* CR-078: cột đủ chỗ cho nhãn dài nhất "Chưa tạo đơn mua hàng" (CR-074) — hẹp hơn thì pill tràn đè cột Tiến độ */}
                    <th style={{ width: 195, textAlign: 'center' }}>Trạng thái</th>
                    <th style={{ width: 118, textAlign: 'center' }} title="Tiến độ: tổng SL đã nhận / tổng SL đã đặt (đồng bộ từ Đơn mua hàng)">Tiến độ<br /><span style={{ fontWeight: 400, fontSize: 10.5, color: 'var(--muted)' }}>nhận / đặt</span></th>
                    <th style={{ width: 130, textAlign: 'center', whiteSpace: 'normal', lineHeight: 1.3 }} title="Ngày dự kiến có hàng (sửa trực tiếp nếu có quyền, hoặc trong Chi tiết dòng)">Ngày dự kiến<br />có hàng</th>
                    {showAssigneeCol && <th style={{ width: 160, textAlign: 'left' }}>NSTM phụ trách</th>}
                    <th style={{ width: 96, textAlign: 'center' }}>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((it: any, i: number) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td
                        style={dupCodes.includes((it.product_code || '').trim()) ? { background: 'var(--red-bg)', boxShadow: 'inset 3px 0 0 var(--red)' } : undefined}
                        title={dupCodes.includes((it.product_code || '').trim()) ? 'Mã hàng này đã có ở dòng khác — mỗi mã chỉ được 1 dòng' : undefined}
                      >
                        {editable ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <ProductPicker compact code={it.product_code} name={it.product_name} onPick={(prod) => applyProduct(i, prod)} />
                            </div>
                            {/* Tham chiếu giá đã mua trước đó — chỉ hiện khi đã chọn mã hàng */}
                            {it.product_code && (
                              <button className="icon-btn" style={{ flexShrink: 0 }} title="Lịch sử mua hàng gần nhất của mã hàng này" onClick={() => setHistoryIdx(i)}>
                                <i className="ti ti-history" style={{ fontSize: 16, color: 'var(--muted)' }} />
                              </button>
                            )}
                          </div>
                        ) : <span style={{ display: 'block', whiteSpace: 'normal', overflowWrap: 'anywhere' }}>{it.product_code || '—'}</span>}
                      </td>
                      {/* Tên sản phẩm: hiện đủ, dài thì xuống dòng (đọc thiếu dễ hiểu lầm) */}
                      <td title={it.product_name}>
                        {editable ? (
                          <TextAreaAuto className="cell-input cell-textarea" value={it.product_name || ''} placeholder="Nhập tên sản phẩm" onChange={(v) => setItem(i, 'product_name', v)} style={{ width: '100%' }} />
                        ) : <span style={{ display: 'block', whiteSpace: 'normal', overflowWrap: 'anywhere', lineHeight: 1.45 }}>{it.product_name || ''}</span>}
                      </td>
                      <td>
                        {editable ? (
                          <select className="cell-input" value={it.warehouse || ''} onChange={(e) => setItem(i, 'warehouse', e.target.value)} style={{ width: '100%' }}>
                            <option value="">-- Kho --</option>
                            {warehouses.map((w) => <option key={w.name} value={w.name}>{w.code} - {w.name}</option>)}
                          </select>
                        ) : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={whLabel(it.warehouse)}>{it.warehouse ? whLabel(it.warehouse) : ''}</span>}
                      </td>
                      <td>
                        {editable ? (
                          <select className="cell-input" value={it.item_group || ''} onChange={(e) => setGroup(i, e.target.value)} style={{ width: '100%' }}>
                            <option value="">-- Phân loại --</option>
                            {groups.map((g) => <option key={g} value={g}>{g}</option>)}
                          </select>
                        ) : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={it.item_group}>{it.item_group || ''}</span>}
                      </td>
                      <td>
                        {editable ? (
                          <select className="cell-input" value={it.unit || ''} onChange={(e) => setItem(i, 'unit', e.target.value)} style={{ width: '100%' }}>
                            <option value="">-- ĐVT --</option>
                            {units.map((u) => <option key={u} value={u}>{u}</option>)}
                          </select>
                        ) : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={it.unit}>{it.unit || ''}</span>}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {editable ? (
                          <NumberInput decimals value={it.qty} onChange={(v) => setItem(i, 'qty', v)} className="cell-input" style={{ width: '100%', textAlign: 'right' }} placeholder="0" />
                        ) : fmtBlank(it.qty)}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {editable ? (
                          <NumberInput value={it.price} maxDecimals={PRICE_DECIMALS} onChange={(v) => setItem(i, 'price', v)} className="cell-input" style={{ width: '100%', textAlign: 'right' }} placeholder="0" />
                        ) : fmtPriceBlank(it.price)}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {editable ? (
                          <NumberInput value={it.vat_pct ?? 8} max={VAT_MAX} maxDecimals={VAT_DECIMALS} onChange={(v) => setItem(i, 'vat_pct', v)} className="cell-input" style={{ width: '100%', textAlign: 'right' }} placeholder="% VAT" />
                        ) : (it.vat_pct != null ? Number(it.vat_pct) + '%' : '')}
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 500 }} title="Thành tiền gồm VAT">{fmtVNDBlank(lineAmount(it))}</td>
                      <td style={{ textAlign: 'center' }} title="Trạng thái tự đồng bộ từ Đơn mua hàng — không sửa tay">
                        {/* badge wrap: nhãn nào dài quá ô thì XUỐNG DÒNG, không tràn sang cột bên cạnh */}
                        <span className="badge wrap" style={{ background: (LS_COLOR[it.line_status] || '#94a3b8') + '22', color: LS_COLOR[it.line_status] || '#64748b' }}>{prLineStatusLabel(it.line_status || LS_NO_PO)}</span>
                      </td>
                      <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }} title="SL đã nhận / SL đã đặt (đồng bộ từ Đơn mua hàng)">
                        {(Number(it.qty_ordered) || Number(it.qty_received)) ? (
                          <span><b style={{ color: '#0d9488' }}>{fmt(it.qty_received)}</b><span style={{ color: 'var(--muted)' }}> / {fmt(it.qty_ordered)}</span></span>
                        ) : <span style={{ color: 'var(--muted)' }}>—</span>}
                      </td>
                      <td style={{ textAlign: 'center', overflow: 'hidden', whiteSpace: 'nowrap', color: 'var(--muted)' }} title="Thời gian dự kiến có hàng (chỉ NSTM phụ trách/quản lý sửa)">
                        {canLineStatus(it) ? (
                          <DateInput className="cell-input" style={{ width: '100%', boxSizing: 'border-box', minWidth: 0 }} value={it.expected_date || ''}
                            onFocus={() => { inlineExpOrig.current = (it.expected_date || '').trim() }}
                            onChange={(v) => setItem(i, 'expected_date', v)}
                            onBlur={() => commitExpectedDate(i)} />
                        ) : (it.expected_date ? fmtDate(it.expected_date) : '—')}
                      </td>
                      {showAssigneeCol && (
                        <td style={{ overflow: 'hidden' }}>
                          {canAssignPurchaser ? (
                            <select className="cell-input" value={it.assignee || ''} onChange={(e) => changeAssignee(i, e.target.value)} style={{ width: '100%' }}>
                              <option value="">-- Chọn NSTM --</option>
                              {purchaserOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                            </select>
                          ) : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={empName(it.assignee)}>{it.assignee ? empName(it.assignee) : ''}</span>}
                        </td>
                      )}
                      <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                        <button className="icon-btn" title="Chi tiết" onClick={() => setEditIdx(i)}><i className="ti ti-pencil" style={{ color: 'var(--teal)' }} /></button>
                        {editable && <button className="icon-btn" title="Nhân đôi" onClick={() => copyItem(i)}><i className="ti ti-copy" style={{ color: 'var(--muted)' }} /></button>}
                        {editable && <button className="icon-btn" title="Xóa" onClick={() => delItem(i)}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>}
                      </td>
                    </tr>
                  ))}
                  {items.length === 0 && <tr><td colSpan={showAssigneeCol ? 15 : 14} style={{ textAlign: 'center', color: '#999', padding: 20 }}>Chưa có sản phẩm nào</td></tr>}
                </tbody>
              </table>
            </div>
            {editable && items.length > 0 && (
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button className="btn ghost" onClick={async () => { const n = await askPrompt({ message: 'Thêm bao nhiêu dòng?', defaultValue: '5' }); if (n !== null) addItems(Math.max(1, parseInt(n || '0') || 0)) }} style={{ height: 30, padding: '0 8px', fontSize: 12 }}><i className="ti ti-rows" /> Thêm nhiều dòng</button>
              </div>
            )}
            <div style={{ marginTop: 14, textAlign: 'right', fontSize: 14, display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-end' }}>
              <div>Tiền hàng (chưa VAT): <b style={{ color: 'var(--navy)' }}>{fmtVND(subtotal)} đ</b></div>
              <div style={{ color: 'var(--muted)' }}>Tiền VAT: <b>{fmtVND(vatAmount)} đ</b></div>
              <div style={{ fontSize: 15 }}>Tổng cộng (gồm VAT): <b style={{ color: 'var(--navy)' }}>{fmtVND(totalWithVat)} đ</b></div>
            </div>
          </div>

          {/* Nhà cung cấp — Task 4: 2 cụm.
              · Cụm 'Bộ phận đề xuất' (req): AI CŨNG nhập/xem được (kể cả người yêu cầu không có
                quyền xem NCC) — sửa bug người yêu cầu không đề xuất nổi NCC của mình.
              · Cụm 'Khảo sát / Thu mua' (pur): chỉ hiện khi có quyền xem NCC (supplier.read);
                chỉ Quản lý/Admin thu mua (supplier.write) mới sửa được. */}
          {(() => {
            const canSupRead = can('supplier', 'read')
            const canWritePur = isNew ? can('supplier', 'write') : (pr.can_edit_supplier_pur ?? can('supplier', 'write'))
            const req = pr.supplier_req || {}
            const pur = pr.supplier_pur || {}
            return (
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title">Nhà cung cấp</h3>

            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--navy)', marginBottom: 8 }}>NCC do bộ phận đề xuất (nếu có)</div>
            <div className="form-grid" style={{ marginBottom: canSupRead ? 18 : 4 }}>
              <div className="form-row">
                <label>Tên nhà cung cấp đề xuất</label>
                <input value={req.name || ''} placeholder="Nhà cung cấp tối ưu nhất" disabled={!editable} onChange={(e) => setSup('supplier_req', 'name', e.target.value)} />
              </div>
              <div className="form-row">
                <label>Mã số thuế NCC</label>
                <input value={req.tax_code || ''} placeholder="Mã số thuế NCC" disabled={!editable} onChange={(e) => setSup('supplier_req', 'tax_code', e.target.value)} />
              </div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Liên hệ NCC (SĐT / Email / Địa chỉ...)</label>
                <input value={req.contact || ''} placeholder="Thông tin liên hệ nhà cung cấp..." disabled={!editable} onChange={(e) => setSup('supplier_req', 'contact', e.target.value)} />
              </div>
            </div>

            {canSupRead && (
              <>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--teal)', marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8 }}>
                  NCC từ khảo sát / thu mua
                  {pr.supplier_from_survey && <span style={{ fontSize: 11, fontWeight: 400, color: 'var(--muted)' }}>(nguồn: Yêu cầu báo giá)</span>}
                  {!canWritePur && <span style={{ fontSize: 11, fontWeight: 400, color: 'var(--muted)' }}>· chỉ xem</span>}
                </div>
                <div className="form-grid">
                  <div className="form-row">
                    <label>Tên nhà cung cấp</label>
                    <input value={pur.name || ''} placeholder="Nhà cung cấp tối ưu nhất" disabled={!editable || !canWritePur} onChange={(e) => setSup('supplier_pur', 'name', e.target.value)} />
                  </div>
                  <div className="form-row">
                    <label>Mã số thuế NCC</label>
                    <input value={pur.tax_code || ''} placeholder="Mã số thuế NCC" disabled={!editable || !canWritePur} onChange={(e) => setSup('supplier_pur', 'tax_code', e.target.value)} />
                  </div>
                  <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                    <label>Liên hệ NCC (SĐT / Email / Địa chỉ...)</label>
                    <input value={pur.contact || ''} placeholder="Thông tin liên hệ nhà cung cấp..." disabled={!editable || !canWritePur} onChange={(e) => setSup('supplier_pur', 'contact', e.target.value)} />
                  </div>
                </div>
              </>
            )}
          </div>
          ) })()}

          {/* Chứng từ/Tài liệu đính kèm khác */}
          <DocumentAttachmentSection
            entity="purchase_request"
            entityId={Number(id)}
            files={files}
            editable={editable}
            isNew={isNew}
            onRefresh={loadAll}
          />

          {/* CR-029: trao đổi trong phiếu — chỉ có khi phiếu đã lưu (cần id) */}
          {!isNew && <CommentThread entity="purchase_request" entityId={Number(id)} />}

        </div>

        {isLogShown && (
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title"><i className="ti ti-history" /> Lịch sử thao tác</h3>
            <AuditTimeline logs={logs} />
          </div>
        )}
      </div>

      {/* Popup danh sách Đơn mua hàng liên quan (cùng mã PYC) */}
      {showPoModal && pos && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(27,37,89,.3)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4vh 12px', overflowY: 'auto' }}
          onClick={() => setShowPoModal(false)}>
          <div className="card" style={{ width: 860, maxWidth: '100%', padding: 20 }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 className="sec-title" style={{ margin: 0, border: 0, padding: 0 }}>Đơn mua hàng liên quan ({pos.length})</h3>
              <span className="clickable" style={{ color: '#94a3b8', fontSize: 18 }} onClick={() => setShowPoModal(false)}><i className="ti ti-x" /></span>
            </div>
            <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
              <table className="items-table" style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Mã PO</th>
                    <th style={{ textAlign: 'left' }}>NCC</th>
                    <th style={{ textAlign: 'right' }}>Tổng tiền</th>
                    <th style={{ textAlign: 'center', width: 150 }}>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {pos.map((po: any) => (
                    <tr key={po.id}>
                      <td>
                        <span className="clickable" style={{ color: 'var(--teal)', fontWeight: 500, cursor: 'pointer' }}
                          onClick={() => navigate(`/purchase-orders/${po.id}`)}>{po.code || `#${po.id}`}</span>
                      </td>
                      <td>{po.supplier_name || po.supplier_code || ''}</td>
                      <td style={{ textAlign: 'right' }}>{fmtVNDBlank(po.amount)}</td>
                      <td style={{ textAlign: 'center' }}>{poBadge(po.status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
              <button className="btn ghost" onClick={() => navigate(`/purchase-orders?pr_code=${encodeURIComponent(pr.code)}`)}><i className="ti ti-external-link" />Mở trang Đơn mua hàng</button>
              <button className="btn" onClick={() => setShowPoModal(false)}>Đóng</button>
            </div>
          </div>
        </div>
      )}

      {/* Popup chi tiết dòng */}
      {edit && editIdx != null && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(27,37,89,.3)', zIndex: 200, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '4vh 12px', overflowY: 'auto' }}>
          <div className="card" style={{ width: 760, maxWidth: '100%', padding: 20 }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 className="sec-title" style={{ margin: 0, border: 0, padding: 0 }}>Chi tiết dòng #{editIdx + 1}</h3>
              <span className="clickable" style={{ color: '#94a3b8', fontSize: 18 }} onClick={() => setEditIdx(null)}><i className="ti ti-x" /></span>
            </div>

            {/* Cụm ẢNH GỐC SP (đầu popup, thu gọn) + nút So sánh — chỉ khi dòng đã lưu & khớp catalog */}
            {edit.id && (edit.product_id ? (
              <div style={{ marginBottom: 14 }}>
                <AttachmentGallery entity="product" entityId={edit.product_id} readOnly compact
                  title="Hình ảnh SP (gốc)" onImages={setOrigImgs}
                  headerRight={origImgs.length > 0 && compareImgs.length > 0 && (
                    <button className="btn ghost" style={{ height: 28, fontSize: 12.5, padding: '0 10px' }}
                      onClick={() => setCompareOpen(true)}><i className="ti ti-arrows-diff" /> So sánh</button>
                  )} />
              </div>
            ) : (
              <div style={{ fontSize: 12.5, color: 'var(--muted)', marginBottom: 14 }}><i className="ti ti-photo-off" /> Mã hàng không khớp catalog — không có ảnh gốc để tham chiếu.</div>
            ))}

            <div className="form-grid">
              <div className="form-row">
                <label>Mã vật tư <span className="req">*</span></label>
                <ProductPicker code={edit.product_code} name={edit.product_name} disabled={!editable} onPick={(prod) => applyProduct(editIdx, prod)} />
              </div>
              <div className="form-row">
                <label>Tên vật tư <span className="req">*</span></label>
                <TextAreaAuto style={{ minHeight: 40, fontSize: 14 }} value={edit.product_name || ''} disabled={!editable} onChange={(v) => setItem(editIdx, 'product_name', v)} />
              </div>
              <div className="form-row">
                <label>Phân loại</label>
                <SearchSelect value={edit.item_group || ''} options={groups} disabled={!editable} placeholder="Chọn/tìm phân loại…"
                  onChange={(v) => setGroup(editIdx, v)} />
              </div>
              <div className="form-row">
                <label>Mô tả phân loại</label>
                <input value={edit.group_desc || ''} disabled placeholder="Tự động theo phân loại" />
              </div>
              <div className="form-row">
                <label>Số lượng mua <span className="req">*</span></label>
                <NumberInput decimals value={edit.qty} onChange={(v) => setItem(editIdx, 'qty', v)} disabled={!editable} placeholder="Nhập số lượng" />
              </div>
              <div className="form-row">
                <label>Giá đề xuất (chưa VAT)</label>
                <NumberInput value={edit.price} maxDecimals={PRICE_DECIMALS} onChange={(v) => setItem(editIdx, 'price', v)} disabled={!editable} placeholder="Để trống nếu chưa có giá" />
              </div>
              <div className="form-row">
                <label title="% VAT theo dòng">VAT (%)</label>
                <NumberInput value={edit.vat_pct ?? 8} max={VAT_MAX} maxDecimals={VAT_DECIMALS} disabled={!editable} onChange={(v) => setItem(editIdx, 'vat_pct', v)} placeholder="Nhập % VAT (0 – 99,99)" />
              </div>
              <div className="form-row">
                <label>ĐVT</label>
                <SearchSelect value={edit.unit || ''} options={units} disabled={!editable} placeholder="Chọn/tìm ĐVT…" onChange={(v) => setItem(editIdx, 'unit', v)} />
              </div>
              <div className="form-row">
                <label>Thành tiền (gồm VAT)</label>
                <input value={(() => { const v = lineAmount(edit); return v ? fmt(v) + ' đ' : '' })()} placeholder="—" disabled />
              </div>
              <div className="form-row">
                <label>Kho nhận <span className="req">*</span></label>
                <SearchSelect value={edit.warehouse || ''} options={warehouseOptions} disabled={!editable} placeholder="Chọn/tìm kho…" onChange={(v) => setItem(editIdx, 'warehouse', v)} />
              </div>
              <div className="form-row">
                <label>Ngày cần hàng <span className="req">*</span></label>
                <DateInput value={edit.required_date || ''} disabled={!editable}
                  onChange={(v) => setItem(editIdx, 'required_date', v)} />
              </div>
              <div className="form-row">
                <label title="NSTM phụ trách cập nhật — đổi giá trị đã có phải kèm lý do">Ngày dự kiến có hàng</label>
                <DateInput value={edit.expected_date || ''} disabled={!canLineStatus(edit)} onChange={(v) => setItem(editIdx, 'expected_date', v)} />
              </div>
              {showAssigneeCol && (
                <div className="form-row">
                  <label>Nhân sự phụ trách</label>
                  <SearchSelect value={edit.assignee || ''} disabled={!canAssignPurchaser}
                    onChange={(v) => setItem(editIdx, 'assignee', v)} options={purchaserOptions}
                    placeholder={canAssignPurchaser ? 'Chọn NSTM...' : ''} />
                </div>
              )}
              <div className="form-row">
                <label title="Tự đồng bộ từ Đơn mua hàng — không sửa tay">Trạng thái xử lý</label>
                <div><span className="badge" style={{ background: (LS_COLOR[edit.line_status] || '#94a3b8') + '22', color: LS_COLOR[edit.line_status] || '#64748b' }}>{prLineStatusLabel(edit.line_status || LS_NO_PO)}</span>
                  <span style={{ fontSize: 11.5, color: 'var(--muted)', marginLeft: 8 }}>tự đồng bộ từ Đơn mua hàng</span></div>
              </div>
              <div className="form-row">
                <label title="Tổng SL đã nhận / đã đặt, đồng bộ từ Đơn mua hàng">Tiến độ (nhận / đặt)</label>
                <div style={{ fontSize: 13 }}>
                  <b style={{ color: '#0d9488' }}>{fmt(edit.qty_received)}</b>
                  <span style={{ color: 'var(--muted)' }}> / {fmt(edit.qty_ordered)}</span>
                  <span style={{ color: 'var(--muted)' }}> {edit.unit || ''}</span>
                </div>
              </div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Chi tiết tiến độ</label>
                <textarea value={edit.progress_note || ''} disabled={!canEditNote(edit)} onChange={(e) => setItem(editIdx, 'progress_note', e.target.value)} />
              </div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Ghi chú khác</label>
                <textarea value={edit.note || ''} disabled={!canEditNote(edit)} onChange={(e) => setItem(editIdx, 'note', e.target.value)} />
              </div>
            </div>

            {/* Cụm ẢNH ĐỐI CHIẾU của dòng (upload/xóa/kéo-thả) — dưới form.
                Dòng CHƯA LƯU (phiếu mới hoặc dòng vừa thêm) vẫn chọn được ảnh: gallery giữ
                File ở `_pendingImgs` của dòng, `save()` tải lên ngay sau khi dòng có id thật.
                Trước đây chặn "Lưu phiếu trước để đính kèm" -> người dùng phải làm 2 lượt. */}
            <div style={{ marginTop: 16 }}>
              <AttachmentGallery entity="purchase_request_line_image" entityId={edit.id || 0}
                permEntity="purchase_request" title="File đính kèm (đối chiếu)" onImages={setCompareImgs}
                pendingFiles={edit._pendingImgs || KHONG_CO_FILE}
                onPendingChange={(fs) => setItem(editIdx, '_pendingImgs', fs)}
                maxHint="Ảnh chụp thực tế để so với ảnh gốc · tối đa 5MB/ảnh · có thể chọn nhiều" />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
              <button className="btn ghost" onClick={() => setEditIdx(null)}>{editable ? 'Đóng' : 'Hủy'}</button>
              {!editable && (canLineStatus(edit) || canAssignPurchaser) && (
                <button className="btn" onClick={() => savePopupLine(items[editIdx])}><i className="ti ti-device-floppy" />Lưu dòng</button>
              )}
              {editable && <button className="btn" onClick={async () => { const ok = await save(false); if (ok) setEditIdx(null) }}><i className="ti ti-device-floppy" />Xong</button>}
            </div>
          </div>
        </div>
      )}

      {/* Popup tham chiếu giá đã mua trước đó của 1 dòng — chọn xong chỉ FILL, không lưu */}
      {historyIdx !== null && items[historyIdx] && (
        <PurchaseHistoryPickerModal
          productCode={items[historyIdx].product_code}
          productName={items[historyIdx].product_name}
          onPick={(h) => applyHistory(historyIdx, h)}
          onClose={() => setHistoryIdx(null)}
        />
      )}

      {/* Lightbox chia đôi: trái = ảnh gốc SP, phải = ảnh đối chiếu của dòng */}
      {compareOpen && (
        <CompareLightbox left={origImgs} right={compareImgs}
          leftLabel="Ảnh gốc (catalog)" rightLabel="Ảnh đối chiếu (thực tế)"
          onClose={() => setCompareOpen(false)} />
      )}
    </div>
  )
}
