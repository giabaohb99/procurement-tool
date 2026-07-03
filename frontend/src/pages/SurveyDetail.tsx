import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { prBadge } from '../config/cruds'
import ProductPicker from '../components/ProductPicker'
import SearchSelect from '../components/SearchSelect'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const GROUPS = ['Bao bì', 'Nguyên liệu', 'In ấn', 'Chai lọ', 'Hóa chất']
const VAT_OPTS = ['0', '2', '4', '6', '8', '10']
const APPROVE_OPTS = ['Chờ duyệt', 'Đã duyệt', 'Không duyệt']
const APPROVE_COLOR: Record<string, string> = { 'Chờ duyệt': '#d97706', 'Đã duyệt': '#16a34a', 'Không duyệt': '#b91c1c' }

// Kiểu trường: date | text | textarea | num | check | computed | unit(chọn) | vat(chọn) | approve(chọn)
type SecField = { k: string; label: string; type?: string; full?: boolean }
type Section = { title: string; fields: SecField[] }

const SUPPLIER_SECTIONS: Section[] = [
  { title: 'Lịch làm việc với NCC', fields: [
    { k: 'contact_date', label: 'Ngày liên hệ NCC', type: 'date' },
    { k: 'reply_date', label: 'Ngày dự kiến NCC phản hồi', type: 'date' },
    { k: 'result_date', label: 'Ngày dự kiến trả KQ', type: 'date' },
  ] },
  { title: 'Thông tin nhà cung cấp', fields: [
    { k: 'supplier_code', label: 'Tên viết tắt NCC', type: 'supplier' },
    { k: 'supplier_name', label: 'Tên nhà cung cấp', type: 'text' },
    { k: 'tax_code', label: 'Mã số thuế', type: 'text' },
    { k: 'reg_address', label: 'Địa chỉ theo giấy đăng kí', type: 'textarea', full: true },
    { k: 'warehouse_address', label: 'Địa chỉ kho của NCC', type: 'textarea', full: true },
    { k: 'google_maps', label: 'Link định vị kho', type: 'text', full: true },
  ] },
  { title: 'Kinh doanh & Báo giá', fields: [
    { k: 'contact_person', label: 'NVKD của NCC', type: 'text' },
    { k: 'contact_phone', label: 'SĐT NCC đang làm việc', type: 'text' },
    { k: 'supply_group', label: 'Nhóm SP/dịch vụ cung ứng', type: 'textarea', full: true },
    { k: 'quote_folder', label: 'Link báo giá', type: 'text' },
    { k: 'source_of_information', label: 'Nguồn thông tin đầu vào', type: 'text' },
  ] },
  { title: 'Đánh giá mặt hàng khảo sát', fields: [
    { k: 'production_tech', label: 'Công nghệ SX, đa dạng chủng loại', type: 'textarea', full: true },
    { k: 'production_time', label: 'Thời gian SX', type: 'text' },
    { k: 'nvkd_eval', label: 'Đánh giá tư vấn NVKD', type: 'text' },
    { k: 'invoice_policy', label: 'Hóa đơn', type: 'text' },
    { k: 'reliability', label: 'Mức độ tin cậy', type: 'text' },
    { k: 'delivery_policy', label: 'Chính sách nhận hàng', type: 'textarea', full: true },
    { k: 'debt_policy', label: 'Chính sách công nợ', type: 'textarea', full: true },
    { k: 'defect_return', label: 'Hàng lỗi, hàng trả', type: 'textarea', full: true },
    { k: 'nspt_note', label: 'Nhận xét (NSPT)', type: 'textarea', full: true },
  ] },
  { title: 'Phê duyệt Trưởng phòng / Quản lý', fields: [
    { k: 'line_approve', label: 'Duyệt (TP/QL)', type: 'approve' },
    { k: 'line_approve_note', label: 'Yêu cầu (TP/QL)', type: 'textarea', full: true },
  ] },
]

const PRODUCT_SECTIONS: Section[] = [
  { title: 'Lịch làm việc', fields: [
    { k: 'contact_date', label: 'Ngày liên hệ', type: 'date' },
    { k: 'reply_date', label: 'Ngày dự kiến phản hồi', type: 'date' },
    { k: 'result_date', label: 'Ngày dự kiến trả KQ', type: 'date' },
  ] },
  { title: 'Nhà cung cấp & Sản phẩm', fields: [
    { k: 'supplier_code', label: 'Tên viết tắt NCC', type: 'supplier' },
    { k: 'internal_code', label: 'Mã SP (theo NCC)', type: 'text' },
    { k: 'product_name', label: 'Tên SP (tên NCC đặt)', type: 'text', full: true },
    { k: 'spec', label: 'Thông số kỹ thuật', type: 'textarea', full: true },
    { k: 'origin', label: 'Xuất xứ sản phẩm', type: 'text' },
  ] },
  { title: 'Báo giá & Quy đổi', fields: [
    { k: 'quote_unit', label: 'ĐVT', type: 'unit' },
    { k: 'moq', label: 'MOQ tối thiểu', type: 'num' },
    { k: 'price_by_volume', label: 'Giá theo sản lượng (VNĐ)', type: 'num' },
    { k: 'volume_range', label: 'Khung sản lượng (theo ĐVT)', type: 'text' },
    { k: 'vat', label: 'VAT (%)', type: 'vat' },
    { k: 'amount', label: 'Thành tiền (VNĐ)', type: 'computed' },
    { k: 'internal_unit', label: 'ĐVT (quy đổi về ĐVT Cty)', type: 'unit' },
    { k: 'amount_converted', label: 'Thành tiền (đã quy đổi)', type: 'num' },
    { k: 'shipping_cost', label: 'Chi phí vận chuyển (VNĐ)', type: 'num' },
    { k: 'delivery_time', label: 'Thời gian giao hàng', type: 'text' },
    { k: 'delivery_place', label: 'Địa điểm giao/nhận hàng', type: 'text' },
    { k: 'quote_file', label: 'Link báo giá', type: 'text' },
  ] },
  { title: 'Lấy mẫu & LAB', fields: [
    { k: 'sample_ready', label: 'Mẫu sẵn', type: 'check' },
    { k: 'sample_date', label: 'Ngày lấy mẫu', type: 'date' },
    { k: 'sample_qty', label: 'Số lượng mẫu nhận', type: 'num' },
    { k: 'lab_result', label: 'Đánh giá chất lượng từ LAB', type: 'textarea', full: true },
  ] },
  { title: 'Đánh giá & Phê duyệt', fields: [
    { k: 'nspt_note', label: 'NSPT Đánh giá', type: 'textarea', full: true },
    { k: 'line_approve', label: 'Duyệt', type: 'approve' },
    { k: 'line_approve_note', label: 'Ý kiến TP/QL', type: 'textarea', full: true },
  ] },
]

type Col = { key: string; label: string; w: number; type?: string; options?: string[] }

const SUPPLIER_COLS: Col[] = [
  { key: 'contact_date', label: 'Ngày LH', w: 110, type: 'date' },
  { key: 'reply_date', label: 'NCC phản hồi', w: 120, type: 'date' },
  { key: 'result_date', label: 'Ngày trả KQ', w: 120, type: 'date' },
  { key: 'supplier_code', label: 'NCC (viết tắt) *', w: 140, type: 'supplier' },
  { key: 'supplier_name', label: 'Tên pháp lý', w: 220 },
  { key: 'tax_code', label: 'MST', w: 110 },
  { key: 'reg_address', label: 'Địa chỉ ĐKKD', w: 200 },
  { key: 'warehouse_address', label: 'Địa chỉ kho', w: 200 },
  { key: 'google_maps', label: 'Google Maps', w: 160 },
  { key: 'contact_person', label: 'Người LH (NVKD)', w: 140 },
  { key: 'contact_phone', label: 'SĐT', w: 110 },
  { key: 'supply_group', label: 'Nhóm SP cung ứng', w: 160 },
  { key: 'quote_folder', label: 'Folder báo giá', w: 160 },
  { key: 'production_tech', label: 'Công nghệ SX', w: 150 },
  { key: 'production_time', label: 'Thời gian SX', w: 120 },
  { key: 'nvkd_eval', label: 'Đánh giá NVKD', w: 130 },
  { key: 'invoice_policy', label: 'Chính sách hóa đơn', w: 170 },
  { key: 'reliability', label: 'Mức tin cậy', w: 130, type: 'select', options: ['', 'Cao', 'Trung bình', 'Thấp'] },
  { key: 'delivery_policy', label: 'Chính sách giao nhận', w: 170 },
  { key: 'debt_policy', label: 'Chính sách công nợ', w: 160, type: 'select', options: ['', 'Tiền mặt', 'Công nợ 30 ngày', 'Công nợ 60 ngày', 'Công nợ 90 ngày', 'Trả trước'] },
  { key: 'defect_return', label: 'Hàng lỗi/trả', w: 150 },
  { key: 'nspt_note', label: 'Nhận xét NSPT', w: 160 },
  { key: 'nspt_reason', label: 'Lý do', w: 160 },
  { key: 'line_approve', label: 'Duyệt (TP/QL)', w: 140, type: 'select', options: ['', 'Chờ duyệt', 'Đã duyệt', 'Không duyệt'] },
  { key: 'line_approve_note', label: 'Ghi chú duyệt', w: 180 },
]

const PRODUCT_COLS: Col[] = [
  { key: 'supplier_code', label: 'NCC *', w: 140, type: 'supplier' },
  { key: 'internal_code', label: 'Mã SP (NCC)', w: 120 },
  { key: 'product_name', label: 'Tên SP theo NCC *', w: 220 },
  { key: 'spec', label: 'Thông số KT', w: 180 },
  { key: 'origin', label: 'Xuất xứ', w: 100 },
  { key: 'quote_unit', label: 'ĐVT báo giá', w: 120, type: 'unit' },
  { key: 'moq', label: 'MOQ', w: 90, type: 'num' },
  { key: 'price_by_volume', label: 'Giá theo khung', w: 120, type: 'num' },
  { key: 'volume_range', label: 'Khung SL', w: 110 },
  { key: 'vat', label: 'VAT(%)', w: 90, type: 'select', options: ['0', '2', '4', '6', '8', '10'] },
  { key: 'request_qty', label: 'SL YC', w: 90, type: 'num' },
  { key: 'amount', label: 'Thành tiền', w: 120, type: 'computed' },
  { key: 'internal_unit', label: 'ĐVT quy đổi', w: 120, type: 'unit' },
  { key: 'amount_converted', label: 'TT quy đổi', w: 120, type: 'num' },
  { key: 'shipping_cost', label: 'Phí VC', w: 100, type: 'num' },
  { key: 'delivery_time', label: 'TG giao', w: 110 },
  { key: 'delivery_place', label: 'Nơi giao nhận', w: 150 },
  { key: 'quote_file', label: 'File báo giá', w: 150 },
  { key: 'sample_ready', label: 'Mẫu sẵn', w: 80, type: 'check' },
  { key: 'sample_date', label: 'Ngày mẫu', w: 120, type: 'date' },
  { key: 'sample_qty', label: 'SL mẫu', w: 90, type: 'num' },
  { key: 'lab_result', label: 'KQ LAB', w: 150 },
  { key: 'lab_note', label: 'Ghi chú LAB', w: 150 },
  { key: 'nspt_note', label: 'Nhận xét NSPT', w: 160 },
  { key: 'nspt_reason', label: 'Lý do NSPT', w: 160 },
  { key: 'line_approve', label: 'Duyệt (TP/QL)', w: 140, type: 'select', options: ['', 'Chờ duyệt', 'Đã duyệt', 'Không duyệt'] },
  { key: 'line_approve_note', label: 'Ghi chú duyệt', w: 180 },
]

export default function SurveyDetail({ type }: { type: 'supplier' | 'product' }) {
  const { id } = useParams()
  const isNew = id === 'new'
  const { can, user } = useAuth()
  const navigate = useNavigate()
  const slug = `surveys-${type}`
  const API = `/api/${slug}`
  const cols = type === 'supplier' ? SUPPLIER_COLS : PRODUCT_COLS
  const sections = type === 'supplier' ? SUPPLIER_SECTIONS : PRODUCT_SECTIONS

  // Identify core columns to show directly on the main table (bản tóm tắt nhanh)
  const coreKeys = type === 'supplier'
    ? ['contact_date', 'supplier_code', 'supplier_name', 'contact_person', 'contact_phone', 'nspt_note', 'line_approve']
    : ['supplier_code', 'internal_code', 'product_name', 'quote_unit', 'moq', 'price_by_volume', 'amount', 'line_approve']

  const tableCols = cols.filter(c => coreKeys.includes(c.key))

  // emptyLine phủ hết trường trong các cụm (kể cả 3 cột ngày mới của khảo sát SP)
  // Trạng thái duyệt của dòng mặc định "Chờ duyệt".
  const emptyLine = Object.fromEntries(sections.flatMap((s) => s.fields).map((f) =>
    [f.k, f.k === 'line_approve' ? 'Chờ duyệt' : f.type === 'check' ? false : (f.type === 'num' || f.type === 'computed') ? 0 : '']))

  const [sv, setSv] = useState<any>({
    pr_code: '', received_date: new Date().toISOString().slice(0, 10), result_due_date: '',
    item_group: '', requirement_detail: '', request_qty: 0, market_price: 0, nspt: '',
    has_product_code: false, item_code: '', item_name: '', uom: '', proposed_rate: 0,
    status: 'draft', approve_note: '', lines: [],
  })
  const [suppliers, setSuppliers] = useState<any[]>([])
  const [units, setUnits] = useState<string[]>([])
  const [prList, setPrList] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [attByLine, setAttByLine] = useState<Record<number, any[]>>({})
  const [err, setErr] = useState(''); const [msg, setMsg] = useState('')
  
  // UX upgrade states
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [selectedIdxs, setSelectedIdxs] = useState<number[]>([])

  useEffect(() => {
    api.get('/api/suppliers', { params: { page_size: 1000 } }).then((r) => setSuppliers(r.data.data.items))
    api.get('/api/units', { params: { page_size: 200 } }).then((r) => setUnits(r.data.data.items.map((x: any) => x.name)))
    api.get('/api/purchase-requests', { params: { page_size: 1000 } }).then((r) => setPrList(r.data.data.items))
  }, [])

  // Khi chọn mã PYC -> tự điền các trường header từ yêu cầu mua đó
  const onPickPr = (code: string) => {
    const pr = prList.find((p) => p.code === code)
    setSv((s: any) => ({
      ...s,
      pr_code: code,
      ...(pr ? { requirement_detail: pr.purpose || s.requirement_detail } : {}),
    }))
  }

  async function loadAll() {
    const r = await api.get(`${API}/${id}`)
    const data = r.data.data
    data.lines = (data.lines || []).map((l: any) => ({ ...l, line_approve: l.line_approve || 'Chờ duyệt' }))
    setSv(data)
    api.get('/api/audit-logs', { params: { entity: 'survey', entity_id: id } }).then((x) => setLogs(x.data.data))
    api.get('/api/attachments', { params: { entity: 'survey', entity_id: id } }).then((x) => setFiles(x.data.data))
  }

  useEffect(() => { if (!isNew) loadAll() }, [id, type])

  // Chỉ cho sửa khi ở trạng thái nháp/từ chối VÀ có quyền tạo/ghi
  const editable = (isNew || sv.status === 'draft' || sv.status === 'rejected') && can('survey', isNew ? 'create' : 'write')
  // Quyền duyệt dòng: người có quyền approve sửa được ô Duyệt (kể cả admin khi đang soạn);
  // người không có quyền → khóa cứng. liveApprove = lưu trực tiếp qua endpoint khi phiếu đã gửi duyệt.
  const canApprove = can('survey', 'approve')
  const canEditApprove = canApprove && (isNew || ['draft', 'rejected', 'submitted'].includes(sv.status))
  const liveApprove = !isNew && sv.status === 'submitted' && canApprove
  const MGR_KEYS = ['line_approve', 'line_approve_note']
  const setH = (k: string, v: any) => setSv((s: any) => ({ ...s, [k]: v }))

  // NSPT phụ trách = người tạo phiếu (tự điền khi tạo mới)
  useEffect(() => {
    if (isNew && !sv.nspt && user) setH('nspt', (user as any).full_name || '')
  }, [isNew, user])

  // Chọn Mã VTBB/VL từ danh mục → tự điền tên/ĐVT/phân loại
  const pickItem = (prod: any) => {
    if (!prod) { setSv((s: any) => ({ ...s, item_code: '', item_name: '' })); return }
    setSv((s: any) => ({
      ...s, item_code: prod.code, item_name: prod.name,
      uom: prod.unit || s.uom, item_group: prod.item_group || s.item_group,
    }))
  }

  const lines = sv.lines || []
  const setLine = (i: number, patch: any) => setSv((s: any) => ({ ...s, lines: s.lines.map((it: any, idx: number) => idx === i ? { ...it, ...patch } : it) }))
  const addLines = (n = 1) => setSv((s: any) => ({ ...s, lines: [...(s.lines || []), ...Array.from({ length: n }, () => ({ ...emptyLine }))] }))
  const delLine = (i: number) => {
    setSv((s: any) => ({ ...s, lines: s.lines.filter((_: any, idx: number) => idx !== i) }))
    setSelectedIdxs(s => s.filter(idx => idx !== i).map(idx => idx > i ? idx - 1 : idx))
    if (editingIndex === i) setEditingIndex(null)
    else if (editingIndex !== null && editingIndex > i) setEditingIndex(editingIndex - 1)
  }

  // Thành tiền dòng = SL dự kiến (ở header) × giá theo sản lượng × (1+VAT)
  const rowAmount = (it: any) => (Number(sv.request_qty) || 0) * (Number(it.price_by_volume) || 0) * (1 + (Number(it.vat) || 0) / 100)
  const subtotal = type === 'product' ? lines.reduce((s: number, it: any) => s + rowAmount(it), 0) : 0

  const duplicateLine = (i: number) => {
    const cloned = { ...lines[i] }
    setSv((s: any) => ({ ...s, lines: [...s.lines, cloned] }))
  }

  const toggleSelect = (i: number) => {
    setSelectedIdxs(s => s.includes(i) ? s.filter(idx => idx !== i) : [...s, i])
  }

  const toggleSelectAll = () => {
    if (selectedIdxs.length === lines.length) setSelectedIdxs([])
    else setSelectedIdxs(lines.map((_, i) => i))
  }

  const deleteSelected = () => {
    if (confirm('Xóa các dòng đã chọn?')) {
      setSv((s: any) => ({
        ...s,
        lines: s.lines.filter((_: any, idx: number) => !selectedIdxs.includes(idx))
      }))
      setSelectedIdxs([])
      setEditingIndex(null)
    }
  }

  function buildBody() {
    return {
      pr_code: sv.pr_code, received_date: sv.received_date, item_group: sv.item_group,
      requirement_detail: sv.requirement_detail, nspt: sv.nspt,
      has_product_code: !!sv.has_product_code, item_code: sv.item_code, item_name: sv.item_name,
      request_qty: Number(sv.request_qty) || 0, uom: sv.uom, proposed_rate: Number(sv.proposed_rate) || 0,
      lines: lines.filter((it: any) => type === 'supplier' ? it.supplier_code : it.product_name),
    }
  }

  async function save() {
    setErr(''); setMsg('')
    try {
      if (isNew) { const r = await api.post(API, buildBody()); navigate(`/${slug}/${r.data.data.id}`) }
      else { await api.patch(`${API}/${id}`, buildBody()); setMsg('Đã lưu thành công'); loadAll() }
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }

  // Điều kiện gửi duyệt: mọi trường phải điền (trừ file + trường của quản lý)
  function validateSubmit(): string {
    if (!sv.item_group) return 'Vui lòng chọn Phân loại'
    if (sv.has_product_code) {
      if (!sv.item_code) return 'Vui lòng chọn Mã VTBB/VL'
      if (!(Number(sv.request_qty) > 0)) return 'Vui lòng nhập Số lượng dự kiến mua'
      if (!sv.uom) return 'Vui lòng chọn ĐVT ở phần Thông tin tiếp nhận'
      if (!(Number(sv.proposed_rate) > 0)) return 'Vui lòng nhập Giá đề xuất'
    } else if (!String(sv.requirement_detail || '').trim()) {
      return 'Nhập Yêu cầu kỹ thuật & chất lượng, hoặc tick "Đã có mã sản phẩm sẵn"'
    }
    const valid = lines.filter((it: any) => type === 'supplier' ? it.supplier_code : it.product_name)
    if (valid.length === 0) return 'Cần ít nhất 1 dòng khảo sát'
    for (let i = 0; i < lines.length; i++) {
      const it = lines[i]
      if (!(type === 'supplier' ? it.supplier_code : it.product_name)) continue
      for (const sec of sections) for (const f of sec.fields) {
        if (MGR_KEYS.includes(f.k)) continue                       // trường của quản lý → bỏ qua
        const t = f.type || 'text'
        if (t === 'num' || t === 'computed' || t === 'check') continue
        if (['sample_date', 'sample_qty', 'lab_result'].includes(f.k) && !it.sample_ready) continue
        if (!String(it[f.k] ?? '').trim()) return `Dòng ${i + 1}: thiếu "${f.label}"`
      }
    }
    return ''
  }

  async function doSubmit() {
    const v = validateSubmit()
    if (v) { setErr(v); return }
    setErr(''); setMsg('')
    try {
      await api.patch(`${API}/${id}`, buildBody())        // lưu bản mới nhất trước
      await api.post(`${API}/${id}/submit`); loadAll()
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi gửi duyệt') }
  }

  async function saveLineApprove() {
    setErr(''); setMsg('')
    const payload = { lines: lines.filter((l: any) => l.id).map((l: any) => ({ id: l.id, line_approve: l.line_approve || '', line_approve_note: l.line_approve_note || '' })) }
    try { await api.patch(`${API}/${id}/line-approve`, payload); setMsg('Đã lưu duyệt dòng'); loadAll() }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi lưu duyệt dòng') }
  }

  // Chọn trạng thái duyệt ngay trên bảng. Khi phiếu đã gửi duyệt → lưu ngay qua endpoint;
  // khi còn soạn (Nháp) → chỉ cập nhật, lưu chung khi bấm "Lưu".
  async function changeLineApprove(i: number, val: string) {
    setLine(i, { line_approve: val })
    const it = lines[i]
    if (liveApprove && it.id) {
      setErr(''); setMsg('')
      try { await api.patch(`${API}/${id}/line-approve`, { lines: [{ id: it.id, line_approve: val, line_approve_note: it.line_approve_note || '' }] }); setMsg(`Đã lưu duyệt dòng ${i + 1}`) }
      catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi lưu duyệt dòng') }
    }
  }

  async function action(path: string, payload: any = {}) {
    setErr('')
    try { await api.post(`${API}/${id}/${path}`, payload); loadAll() }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi') }
  }

  async function uploadFiles(fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'survey'); fd.append('entity_id', String(id))
    Array.from(fl).forEach((f) => fd.append('files', f))
    try { await api.post('/api/attachments', fd); loadAll() } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi tải file') }
  }

  // ----- Đính kèm file theo TỪNG DÒNG (entity = survey_line) -----
  async function loadLineAtt(lineId: number) {
    const r = await api.get('/api/attachments', { params: { entity: 'survey_line', entity_id: lineId } })
    setAttByLine((s) => ({ ...s, [lineId]: r.data.data }))
  }
  async function uploadLineAtt(lineId: number, fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'survey_line'); fd.append('entity_id', String(lineId))
    Array.from(fl).forEach((f) => fd.append('files', f))
    try { await api.post('/api/attachments', fd); loadLineAtt(lineId) } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi tải file') }
  }
  function openLine(i: number) {
    setEditingIndex(i)
    const lid = lines[i]?.id
    if (lid) loadLineAtt(lid)
  }

  // Render 1 trường trong popup theo kiểu (date/text/textarea/num/check/computed/unit/vat/approve)
  // Trường của quản lý (Duyệt/Ý kiến) sửa được khi quản lý đang duyệt dòng (phiếu submitted).
  function lineField(f: SecField, i: number) {
    const it = lines[i]; const k = f.k; const t = f.type || 'text'
    // Trường của quản lý (Duyệt/Ý kiến) mở khi có quyền approve; người khảo sát khóa cứng
    const ce = MGR_KEYS.includes(k) ? canEditApprove : editable
    if (t === 'computed') return <input value={fmt(rowAmount(it))} disabled />
    if (t === 'check') return (
      <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: ce ? 'pointer' : 'default', height: 40 }}>
        <input type="checkbox" checked={!!it[k]} disabled={!ce} onChange={(e) => setLine(i, { [k]: e.target.checked })} style={{ width: 18, height: 18 }} /> {f.label}
      </label>
    )
    if (t === 'date') return <input type="date" value={it[k] ?? ''} disabled={!ce} onChange={(e) => setLine(i, { [k]: e.target.value })} />
    if (t === 'num') return <input type="number" value={it[k] ?? 0} disabled={!ce} onChange={(e) => setLine(i, { [k]: Number(e.target.value) })} />
    if (t === 'textarea') return <textarea value={it[k] ?? ''} disabled={!ce} style={{ minHeight: 64 }} onChange={(e) => setLine(i, { [k]: e.target.value })} />
    if (t === 'supplier') return <SearchSelect value={it[k] ?? ''} disabled={!ce} placeholder="Chọn/tìm NCC…"
      options={suppliers.map((s) => ({ value: s.code, label: `${s.code} — ${s.name}` }))}
      onChange={(v) => { const sup = suppliers.find((s) => s.code === v); setLine(i, sup ? { supplier_code: sup.code, supplier_name: sup.name, tax_code: sup.tax_code, reg_address: sup.address } : { supplier_code: v }) }} />
    if (t === 'unit') return <SearchSelect value={it[k] ?? ''} options={units} disabled={!ce} placeholder="Chọn/tìm ĐVT…" onChange={(v) => setLine(i, { [k]: v })} />
    if (t === 'vat') return <SearchSelect value={String(it[k] ?? '')} options={VAT_OPTS} disabled={!ce} placeholder="Chọn VAT…" onChange={(v) => setLine(i, { [k]: Number(v) })} />
    if (t === 'approve') return <SearchSelect value={it[k] || 'Chờ duyệt'} options={APPROVE_OPTS} colorMap={APPROVE_COLOR} disabled={!ce} placeholder="Chọn…" onChange={(v) => setLine(i, { [k]: v })} />
    return <input value={it[k] ?? ''} disabled={!ce} onChange={(e) => setLine(i, { [k]: e.target.value })} />
  }

  function cell(col: Col, i: number) {
    const it = lines[i]
    // Cột "Duyệt": người có quyền duyệt mới chọn; không có quyền → KHÓA CỨNG (badge màu)
    if (col.key === 'line_approve') {
      if (canEditApprove)
        return <div style={{ width: col.w }}><SearchSelect variant="table" colorMap={APPROVE_COLOR} value={it[col.key] || 'Chờ duyệt'} options={APPROVE_OPTS} placeholder="Duyệt…" onChange={(v) => changeLineApprove(i, v)} /></div>
      const st = it.line_approve || 'Chờ duyệt'; const c = APPROVE_COLOR[st] || '#64748b'
      return <span className="badge" style={{ background: `${c}1a`, color: c, border: `1px solid ${c}55` }}>{st}</span>
    }
    if (!editable) {
      if (col.type === 'computed') return fmt(rowAmount(it))
      if (col.type === 'check') return it[col.key] ? '✓' : ''
      return it[col.key] ?? ''
    }
    if (col.type === 'computed') return <span style={{ fontWeight: 500 }}>{fmt(rowAmount(it))}</span>
    if (col.type === 'check') return <input type="checkbox" checked={!!it[col.key]} onChange={(e) => setLine(i, { [col.key]: e.target.checked })} />
    if (col.type === 'num') return <input className="cell-input" type="number" style={{ width: col.w }} value={it[col.key] ?? 0} onChange={(e) => setLine(i, { [col.key]: Number(e.target.value) })} />
    if (col.type === 'date') return <input className="cell-input" type="date" style={{ width: col.w }} value={it[col.key] ?? ''} onChange={(e) => setLine(i, { [col.key]: e.target.value })} />
    if (col.type === 'select') return (
      <div style={{ width: col.w }}><SearchSelect variant="table" colorMap={col.key === 'line_approve' ? APPROVE_COLOR : undefined}
        value={String(it[col.key] ?? '')} options={col.options!.filter((o) => o !== '')} placeholder="Chọn…"
        onChange={(v) => setLine(i, { [col.key]: col.key === 'vat' ? Number(v) : v })} /></div>
    )
    if (col.type === 'unit') return (
      <div style={{ width: col.w }}><SearchSelect variant="table" value={it[col.key] ?? ''} options={units} placeholder="Chọn/tìm ĐVT…" onChange={(v) => setLine(i, { [col.key]: v })} /></div>
    )
    if (col.type === 'supplier') return (
      <div style={{ width: col.w }}><SearchSelect variant="table" value={it[col.key] ?? ''} placeholder="Chọn/tìm NCC…"
        options={suppliers.map((s) => ({ value: s.code, label: `${s.code} — ${s.name}` }))}
        onChange={(v) => { const sup = suppliers.find((s) => s.code === v); setLine(i, sup ? { supplier_code: sup.code, supplier_name: sup.name, tax_code: sup.tax_code, reg_address: sup.address } : { supplier_code: v }) }} /></div>
    )
    return <input className="cell-input" style={{ width: col.w }} value={it[col.key] ?? ''} onChange={(e) => setLine(i, { [col.key]: e.target.value })} />
  }

  const title = type === 'supplier' ? 'Khảo sát Nhà cung cấp' : 'Khảo sát Sản phẩm'
  const isLogShown = !isNew && logs.length > 0;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate(`/${slug}`)}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>{isNew ? `Tạo ${title}` : `${title} ${sv.code || ''}`}</h2>
        {!isNew && prBadge(sv.status)}
        <span style={{ flex: 1 }} />
        {editable && can('survey', isNew ? 'create' : 'write') && <button className="btn" onClick={save}>{isNew ? 'Tạo' : 'Lưu'}</button>}
        {!isNew && editable && can('survey', 'write') && <button className="btn secondary" onClick={doSubmit}><i className="ti ti-send" />Gửi duyệt</button>}
        {!isNew && sv.status === 'submitted' && can('survey', 'approve') && (
          <>
            <button className="btn" onClick={() => { if (confirm('Duyệt cả phiếu khảo sát này?')) action('approve') }}><i className="ti ti-check" />Duyệt phiếu</button>
            <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={() => { const r = prompt('Lý do trả lại (để khảo sát lại):'); if (r !== null) action('reject', { reason: r }) }}><i className="ti ti-arrow-back-up" />Trả lại</button>
          </>
        )}
      </div>

      <div className={isLogShown ? "detail-grid" : ""}>
        <div>
          {/* Thông tin tiếp nhận */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title">Thông tin tiếp nhận</h3>
            <div className="form-grid">
              <div className="form-row"><label>Mã yêu cầu (PYC) <span style={{ color: 'var(--muted)', fontWeight: 400 }}>(nếu có)</span></label>
                <input list="pyc-list" placeholder="Nhập/chọn mã PYC để tự điền…" value={sv.pr_code} disabled={!editable} onChange={(e) => onPickPr(e.target.value)} />
                <datalist id="pyc-list">{prList.map((p) => <option key={p.id} value={p.code}>{p.purpose || ''}</option>)}</datalist>
              </div>
              <div className="form-row"><label>Ngày tiếp nhận</label><input type="date" value={sv.received_date || ''} disabled={!editable} onChange={(e) => setH('received_date', e.target.value)} /></div>
              <div className="form-row"><label>Phân loại</label>
                <SearchSelect value={sv.item_group} options={GROUPS} disabled={!editable} placeholder="Chọn/tìm phân loại…" onChange={(v) => setH('item_group', v)} />
              </div>
              <div className="form-row"><label>NSPT phụ trách (người tạo)</label><input value={sv.nspt || ''} disabled placeholder="Tự động theo người tạo" /></div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Yêu cầu kỹ thuật & chất lượng</label><textarea value={sv.requirement_detail || ''} disabled={!editable} placeholder="Mô tả thông số kỹ thuật, chất lượng, yêu cầu khác (nếu chưa có mã sản phẩm)…" onChange={(e) => setH('requirement_detail', e.target.value)} /></div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', margin: 0, color: 'var(--navy)' }}>
                  <input type="checkbox" checked={!!sv.has_product_code} disabled={!editable} onChange={(e) => setH('has_product_code', e.target.checked)} style={{ width: 18, height: 18 }} />
                  Đã có mã sản phẩm sẵn trong hệ thống
                </label>
              </div>
              {sv.has_product_code && (
                <>
                  <div className="form-row"><label>Mã VTBB / VL</label>
                    <ProductPicker code={sv.item_code} name={sv.item_name} disabled={!editable} onPick={pickItem} />
                  </div>
                  <div className="form-row"><label>Tên VTBB / VL</label><input value={sv.item_name || ''} disabled placeholder="Tự động theo mã" /></div>
                  <div className="form-row"><label>Số lượng dự kiến mua</label><input type="number" value={sv.request_qty || 0} disabled={!editable} onChange={(e) => setH('request_qty', Number(e.target.value))} /></div>
                  <div className="form-row"><label>ĐVT</label>
                    <SearchSelect value={sv.uom} options={units} disabled={!editable} placeholder="Chọn/tìm ĐVT…" onChange={(v) => setH('uom', v)} />
                  </div>
                  <div className="form-row"><label>Giá đề xuất (VNĐ)</label><input type="number" value={sv.proposed_rate || 0} disabled={!editable} onChange={(e) => setH('proposed_rate', Number(e.target.value))} /></div>
                </>
              )}
            </div>
          </div>

          {/* Bảng khảo sát */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
              <h3 className="sec-title" style={{ margin: 0, border: 'none', padding: 0 }}>{type === 'supplier' ? 'Bảng khảo sát NCC' : 'Bảng khảo sát Sản phẩm'}</h3>
              <div style={{ display: 'flex', gap: 8 }}>
                {editable && selectedIdxs.length > 0 && (
                  <button className="btn secondary" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={deleteSelected}>
                    <i className="ti ti-trash" /> Xóa các dòng đã chọn ({selectedIdxs.length})
                  </button>
                )}
                {editable && (
                  <>
                    <button className="btn ghost" onClick={() => addLines(1)} style={{ height: 32, fontSize: 13 }}><i className="ti ti-plus" />Thêm dòng</button>
                    <button className="btn ghost" onClick={() => addLines(Math.max(1, parseInt(prompt('Thêm bao nhiêu dòng?', '3') || '0') || 0))} style={{ height: 32, fontSize: 13 }}><i className="ti ti-rows" />Thêm nhiều</button>
                  </>
                )}
              </div>
            </div>

            <div className="items-scroll">
              <table className="items-table">
                <thead>
                  <tr>
                    {editable && <th style={{ width: 36, textAlign: 'center' }}><input type="checkbox" checked={lines.length > 0 && selectedIdxs.length === lines.length} onChange={toggleSelectAll} /></th>}
                    <th style={{ width: 36 }}>#</th>
                    {tableCols.map((c) => <th key={c.key} style={{ width: c.w }}>{c.label}</th>)}
                    <th style={{ width: 100, textAlign: 'center' }}>Hành động</th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map((_: any, i: number) => (
                    <tr key={i} style={selectedIdxs.includes(i) ? { background: '#f0f9ff' } : {}}>
                      {editable && (
                        <td style={{ textAlign: 'center' }}>
                          <input type="checkbox" checked={selectedIdxs.includes(i)} onChange={() => toggleSelect(i)} />
                        </td>
                      )}
                      <td>{i + 1}</td>
                      {tableCols.map((c) => <td key={c.key}>{cell(c, i)}</td>)}
                      <td style={{ textAlign: 'center' }}>
                        <div style={{ display: 'inline-flex', gap: 6 }}>
                          <button className="icon-btn" title="Chỉnh sửa chi tiết" onClick={() => openLine(i)}>
                            <i className="ti ti-edit" style={{ fontSize: 16, color: 'var(--teal)' }} />
                          </button>
                          {editable && (
                            <button className="icon-btn" title="Nhân bản dòng" onClick={() => duplicateLine(i)}>
                              <i className="ti ti-copy" style={{ fontSize: 16, color: 'var(--muted)' }} />
                            </button>
                          )}
                          {editable && (
                            <button className="icon-btn" title="Xóa dòng" onClick={() => { if (confirm('Xóa dòng này?')) delLine(i) }}>
                              <i className="ti ti-trash" style={{ fontSize: 16, color: 'var(--red)' }} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                  {lines.length === 0 && <tr><td colSpan={tableCols.length + (editable ? 3 : 2)} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Chưa có dòng nào</td></tr>}
                </tbody>
              </table>
            </div>

            {type === 'product' && <div style={{ marginTop: 12, textAlign: 'right', fontSize: 15, color: 'var(--navy)' }}>Tổng thành tiền: <b>{fmt(subtotal)}</b></div>}
          </div>

          {sv.approve_note && <div className="card" style={{ padding: 14, marginBottom: 16 }}><b>Ghi chú duyệt:</b> {sv.approve_note}</div>}

          {!isNew && (
            <div className="card" style={{ padding: 18, marginBottom: 16 }}>
              <h3 className="sec-title"><i className="ti ti-paperclip" /> Chứng từ đính kèm</h3>
              {can('survey', 'write') && <input type="file" multiple onChange={(e) => uploadFiles(e.target.files)} />}
              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {files.map((f) => (
                  <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                    <i className="ti ti-file" /><a href={f.url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{f.filename}</a>
                    {can('survey', 'write') && <button className="icon-btn" onClick={async () => { if (confirm('Xóa file?')) { await api.delete(`/api/attachments/${f.id}`); loadAll() } }}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>}
                  </div>
                ))}
                {files.length === 0 && <span style={{ color: '#999', fontSize: 13 }}>Chưa có file nào.</span>}
              </div>
            </div>
          )}

          {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
          {msg && <div style={{ color: 'var(--green)', fontSize: 13, marginTop: 8 }}>{msg}</div>}
        </div>

        {isLogShown && (
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title"><i className="ti ti-history" /> Lịch sử thao tác</h3>
            <div className="timeline">
              {logs.map((l, i) => (
                <div key={i} className="tl-item">
                  <span className={'tl-dot ' + (l.action === 'approved' ? 'create' : l.action === 'rejected' ? 'delete' : l.action)} />
                  <div><div style={{ fontSize: 13 }}><b>{l.by}</b> — {l.action_label}{l.message ? `: ${l.message}` : ''}</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)' }}>{new Date(l.at).toLocaleString('vi-VN')}</div></div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Popup chi tiết dòng — chia cụm, to hơn, có đính kèm file theo dòng */}
      {editingIndex !== null && lines[editingIndex] && (() => {
        const it = lines[editingIndex]
        const lid = it.id
        const atts = (lid && attByLine[lid]) || []
        return (
          <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.45)', zIndex: 100, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '4vh 12px', overflowY: 'auto' }} onClick={() => setEditingIndex(null)}>
            <div style={{ width: 980, maxWidth: '100%', background: '#fff', borderRadius: 12, boxShadow: '0 20px 25px -5px rgba(0,0,0,0.15)', display: 'flex', flexDirection: 'column', maxHeight: '92vh', overflow: 'hidden' }} onClick={(e) => e.stopPropagation()}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
                <h3 style={{ margin: 0, fontSize: 16, color: 'var(--navy)', fontWeight: 600 }}>
                  Chi tiết dòng #{editingIndex + 1}{it.supplier_code ? ` — ${it.supplier_code}` : ''}
                </h3>
                <button className="icon-btn" onClick={() => setEditingIndex(null)}><i className="ti ti-x" style={{ fontSize: 18 }} /></button>
              </div>

              <div style={{ padding: '16px 20px', overflowY: 'auto', flex: 1 }}>
                {sections.map((sec) => (
                  <div key={sec.title} style={{ marginBottom: 18 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--teal)', textTransform: 'uppercase', letterSpacing: .3, marginBottom: 10, paddingBottom: 6, borderBottom: '1px solid var(--border)' }}>{sec.title}</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px 20px' }}>
                      {sec.fields.map((f) => (
                        <div className="form-row" key={f.k} style={f.full ? { gridColumn: '1 / -1' } : undefined}>
                          <label>{f.label}</label>
                          {lineField(f, editingIndex)}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}

                {/* Đính kèm file theo dòng */}
                <div style={{ marginBottom: 4 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--teal)', textTransform: 'uppercase', letterSpacing: .3, marginBottom: 10, paddingBottom: 6, borderBottom: '1px solid var(--border)' }}>Đính kèm file (theo dòng)</div>
                  {!lid ? (
                    <span style={{ color: '#999', fontSize: 13 }}><i>Lưu phiếu trước rồi mới đính kèm được file cho dòng này.</i></span>
                  ) : (
                    <div>
                      {editable && (
                        <div style={{ marginBottom: 8 }}>
                          <input type="file" id={`sla-${lid}`} multiple style={{ display: 'none' }} onChange={(e) => uploadLineAtt(lid, e.target.files)} />
                          <label htmlFor={`sla-${lid}`} className="btn ghost" style={{ cursor: 'pointer', height: 32, fontSize: 13 }}><i className="ti ti-upload" /> Tải file lên</label>
                        </div>
                      )}
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        {atts.map((f) => (
                          <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                            <i className="ti ti-file" /><a href={f.url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{f.filename}</a>
                            {editable && <button className="icon-btn" onClick={async () => { if (confirm('Xóa file?')) { await api.delete(`/api/attachments/${f.id}`); loadLineAtt(lid) } }}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>}
                          </div>
                        ))}
                        {atts.length === 0 && <span style={{ color: '#999', fontSize: 13 }}>Chưa có file nào.</span>}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                <button className="btn ghost" style={{ height: 36, padding: '0 18px', fontSize: 13 }} onClick={() => setEditingIndex(null)}>Đóng</button>
                {liveApprove && <button className="btn" style={{ height: 36, padding: '0 18px', fontSize: 13 }} onClick={() => { saveLineApprove(); setEditingIndex(null) }}><i className="ti ti-check" />Lưu duyệt dòng</button>}
              </div>
            </div>
          </div>
        )
      })()}
    </div>
  )
}
