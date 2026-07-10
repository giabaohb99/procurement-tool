import React, { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { srBadge } from '../config/cruds'
import ProductPicker from '../components/ProductPicker'
import SearchSelect from '../components/SearchSelect'
import { toast } from '../components/toast'
import { fmtDateTime } from '../utils/datetime'
import { askConfirm, askPrompt } from '../components/confirm'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const VAT_OPTS = ['0', '2', '4', '6', '8', '10']
const APPROVE_OPTS = ['Chờ duyệt', 'Đã duyệt', 'Không duyệt', 'Thiếu thông tin']
const APPROVE_COLOR: Record<string, string> = { 'Chờ duyệt': '#d97706', 'Đã duyệt': '#16a34a', 'Không duyệt': '#b91c1c', 'Thiếu thông tin': '#ea580c' }

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
  { title: 'Ghi chú', fields: [
    { k: 'note', label: 'Ghi chú', type: 'textarea', full: true },
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
  { title: 'Ghi chú', fields: [
    { k: 'note', label: 'Ghi chú', type: 'textarea', full: true },
  ] },
  { title: 'Đánh giá & Phê duyệt', fields: [
    { k: 'nspt_note', label: 'NSPT Đánh giá', type: 'textarea', full: true },
    { k: 'line_approve', label: 'Duyệt', type: 'approve' },
    { k: 'line_approve_note', label: 'Ý kiến TP/QL', type: 'textarea', full: true },
  ] },
]

type Col = { key: string; label: string; w: number; type?: string; options?: string[] }

const SUPPLIER_CORE_KEYS = ['contact_date', 'supplier_code', 'supplier_name', 'contact_person', 'contact_phone', 'nspt_note', 'note', 'line_approve']

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
  { key: 'note', label: 'Ghi chú', w: 160 },
  { key: 'line_approve', label: 'Duyệt (TP/QL)', w: 140, type: 'select', options: ['', 'Chờ duyệt', 'Đã duyệt', 'Không duyệt', 'Thiếu thông tin'] },
  { key: 'line_approve_note', label: 'Ghi chú duyệt', w: 180 },
]

const PRODUCT_CORE_KEYS = ['supplier_code', 'internal_code', 'product_name', 'quote_unit', 'moq', 'price_by_volume', 'note', 'line_approve']

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
  { key: 'note', label: 'Ghi chú', w: 160 },
  { key: 'line_approve', label: 'Duyệt (TP/QL)', w: 140, type: 'select', options: ['', 'Chờ duyệt', 'Đã duyệt', 'Không duyệt', 'Thiếu thông tin'] },
  { key: 'line_approve_note', label: 'Ghi chú duyệt', w: 180 },
]

const API = '/api/surveys'
const MGR_KEYS = ['line_approve', 'line_approve_note']
// Field KHÔNG bắt buộc khi Gửi duyệt (link, maps, folder, lý do, ghi chú phụ…)
const OPTIONAL_KEYS = ['supplier_code', 'google_maps', 'quote_folder', 'quote_file', 'source_of_information',
  'nspt_reason', 'lab_note', 'defect_return', 'reply_date', 'result_date', 'result_due_date']

function makeEmptyLine(sections: Section[]): Record<string, any> {
  return Object.fromEntries(
    sections.flatMap((s) => s.fields).map((f) => [
      f.k,
      f.k === 'line_approve' ? 'Chờ duyệt' : f.type === 'check' ? false : (f.type === 'num' || f.type === 'computed' || f.type === 'vat') ? 0 : '',
    ])
  )
}

const emptySupplierLine = makeEmptyLine(SUPPLIER_SECTIONS)
const emptyProductLine = makeEmptyLine(PRODUCT_SECTIONS)

// Tập key kiểu số của mỗi loại dòng — để ép Number khi gửi (BE là float).
const numKeysOf = (sections: any[]) => new Set<string>(
  sections.flatMap((s) => s.fields)
    .filter((f: any) => f.type === 'num' || f.type === 'computed' || f.type === 'vat')
    .map((f: any) => f.k)
)
const SUP_NUM_KEYS = numKeysOf(SUPPLIER_SECTIONS)
const PROD_NUM_KEYS = numKeysOf(PRODUCT_SECTIONS)

// Ô nhập SỐ: rỗng khi = 0, gõ không dính số 0 ở đầu (dùng state cục bộ khi focus)
function NumCell({ value, onChange, disabled, className, style }: any) {
  const [foc, setFoc] = useState(false)
  const [raw, setRaw] = useState('')
  const shown = foc ? raw : (value ? String(value) : '')
  return (
    <input type="number" disabled={disabled} className={className} style={style} value={shown}
      onFocus={() => { setRaw(value ? String(value) : ''); setFoc(true) }}
      onBlur={() => setFoc(false)}
      onChange={(e) => { setRaw(e.target.value); onChange(Number(e.target.value) || 0) }} />
  )
}

export default function SurveyDetail() {
  const { id } = useParams()
  const isNew = id === 'new'
  const { can, user } = useAuth()
  const navigate = useNavigate()

  const supplierTableCols = SUPPLIER_COLS.filter((c) => SUPPLIER_CORE_KEYS.includes(c.key))
  const productTableCols = PRODUCT_COLS.filter((c) => PRODUCT_CORE_KEYS.includes(c.key))

  const [sv, setSv] = useState<any>({
    pr_code: '', sr_code: '', survey_request_id: 0, received_date: new Date().toISOString().slice(0, 10), result_due_date: '',
    item_group: '', requirement_detail: '', request_qty: 0, nspt: '',
    has_product_code: false, item_code: '', item_name: '', uom: '', proposed_rate: 0,
    status: 'draft', approve_note: '',
    supplier_lines: [],
    product_lines: [],
  })
  const [suppliers, setSuppliers] = useState<any[]>([])
  const [units, setUnits] = useState<string[]>([])
  const [groups, setGroups] = useState<string[]>([])
  const [prList, setPrList] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [attByLine, setAttByLine] = useState<Record<number, any[]>>({})
  const [attProgress, setAttProgress] = useState<number | null>(null)          // % đang upload (null = không upload)
  const [pendingAtt, setPendingAtt] = useState<Record<string, any[]>>({})      // file ĐÃ upload, chờ gắn khi lưu (dòng chưa có id); key = `${tbl}-${index}`
  // Thông báo dùng toast chung thay cho banner/alert trình duyệt.
  const setErr = (m: string) => { if (m) toast.error(m) }
  const setMsg = (m: string) => { if (m) toast.success(m) }
  // Ô bắt buộc còn trống khi Gửi duyệt (key = `${tbl}-${index}-${fieldKey}`) → tô đỏ.
  const [invalidCells, setInvalidCells] = useState<Set<string>>(new Set())

  // Popup state: which table ('supplier'|'product') + which row index
  const [editingTable, setEditingTable] = useState<'supplier' | 'product' | null>(null)
  const [editingIndex, setEditingIndex] = useState<number | null>(null)

  // Selection state for each table
  const [selSupplier, setSelSupplier] = useState<number[]>([])
  const [selProduct, setSelProduct] = useState<number[]>([])

  // fillMode: popup mở ở chế độ "Bổ sung" cho dòng Thiếu thông tin (phiếu không editable)
  const [fillMode, setFillMode] = useState(false)

  useEffect(() => {
    api.get('/api/suppliers', { params: { page_size: 1000 } }).then((r) => setSuppliers(r.data.data.items))
    api.get('/api/units', { params: { page_size: 200 } }).then((r) => setUnits(r.data.data.items.map((x: any) => x.name)))
    api.get('/api/item-groups', { params: { page_size: 1000 } }).then((r) => setGroups(r.data.data.items.map((x: any) => x.name))).catch(() => {})
    // Nguồn liên kết = Yêu cầu khảo sát (đã scope theo người dùng: NSTM thấy phiếu được gán, admin/QL thấy hết)
    api.get('/api/survey-requests', { params: { page_size: 1000 } }).then((r) => setPrList(r.data.data.items)).catch(() => {})
  }, [])

  // Chọn Yêu cầu khảo sát -> lưu liên kết (id + code) + gợi ý Yêu cầu kỹ thuật từ mục đích
  const onPickPr = (code: string) => {
    const sr = prList.find((p) => p.code === code)
    setSv((s: any) => ({
      ...s,
      sr_code: code,
      survey_request_id: sr ? sr.id : 0,
      ...(sr ? { requirement_detail: sr.purpose || s.requirement_detail } : {}),
    }))
  }

  async function loadAll() {
    const r = await api.get(`${API}/${id}`)
    const data = r.data.data
    data.supplier_lines = (data.supplier_lines || []).map((l: any) => ({ ...l, line_approve: l.line_approve || 'Chờ duyệt' }))
    data.product_lines = (data.product_lines || []).map((l: any) => ({ ...l, line_approve: l.line_approve || 'Chờ duyệt' }))
    setSv(data)
    api.get('/api/audit-logs', { params: { entity: 'survey', entity_id: id } }).then((x) => setLogs(x.data.data))
    api.get('/api/attachments', { params: { entity: 'survey', entity_id: id } }).then((x) => setFiles(x.data.data))
  }

  useEffect(() => { if (!isNew) loadAll() }, [id])

  const editable = (isNew || sv.status === 'draft' || sv.status === 'rejected') && can('survey', isNew ? 'create' : 'write')
  const canApprove = can('survey', 'approve')
  const canEditApprove = canApprove && (isNew || ['draft', 'rejected', 'submitted'].includes(sv.status))
  const liveApprove = !isNew && sv.status === 'submitted' && canApprove

  const setH = (k: string, v: any) => setSv((s: any) => ({ ...s, [k]: v }))

  useEffect(() => {
    if (isNew && !sv.nspt && user) setH('nspt', (user as any).full_name || '')
  }, [isNew, user])

  // Task 1: mở từ nút "Tạo phiếu khảo sát" trên Yêu cầu khảo sát -> tự gắn liên kết YCKS
  const [searchParams] = useSearchParams()
  useEffect(() => {
    if (!isNew) return
    const srId = Number(searchParams.get('sr') || 0)
    const srCode = searchParams.get('sr_code') || ''
    if (srId) setSv((s: any) => (s.survey_request_id ? s : { ...s, survey_request_id: srId, sr_code: srCode }))
  }, [isNew, searchParams])

  // Issue 3: giữ nháp form TẠO MỚI qua F5 (localStorage) — khôi phục khi mở lại, xóa khi tạo xong.
  const DRAFT_KEY = 'survey_new_draft'
  const [hydrated, setHydrated] = useState(false)
  useEffect(() => {
    if (!isNew) { setHydrated(true); return }
    try {
      const raw = localStorage.getItem(DRAFT_KEY)
      if (raw) { const d = JSON.parse(raw); if (d && typeof d === 'object') setSv((s: any) => ({ ...s, ...d })) }
    } catch { /* ignore */ }
    setHydrated(true)
  }, [isNew])
  useEffect(() => {
    if (!isNew || !hydrated) return
    try { localStorage.setItem(DRAFT_KEY, JSON.stringify(sv)) } catch { /* ignore */ }
  }, [isNew, hydrated, sv])

  const pickItem = (prod: any) => {
    if (!prod) { setSv((s: any) => ({ ...s, item_code: '', item_name: '' })); return }
    setSv((s: any) => ({
      ...s, item_code: prod.code, item_name: prod.name,
      uom: prod.unit || s.uom, item_group: prod.item_group || s.item_group,
    }))
  }

  // ---- Generic line helpers (supplier / product) ----
  const getLines = (tbl: 'supplier' | 'product') => tbl === 'supplier' ? (sv.supplier_lines || []) : (sv.product_lines || [])
  const lineKey = (tbl: 'supplier' | 'product') => tbl === 'supplier' ? 'supplier_lines' : 'product_lines'

  const setLine = (tbl: 'supplier' | 'product', i: number, patch: any) => {
    setSv((s: any) => ({ ...s, [lineKey(tbl)]: s[lineKey(tbl)].map((it: any, idx: number) => idx === i ? { ...it, ...patch } : it) }))
    // Sửa ô nào thì bỏ tô đỏ ô đó
    setInvalidCells((prev) => {
      if (!prev.size) return prev
      const next = new Set(prev)
      Object.keys(patch).forEach((k) => next.delete(`${tbl}-${i}-${k}`))
      return next.size === prev.size ? prev : next
    })
  }

  const addLines = (tbl: 'supplier' | 'product', n = 1) => {
    const empty = tbl === 'supplier' ? emptySupplierLine : emptyProductLine
    setSv((s: any) => ({ ...s, [lineKey(tbl)]: [...(s[lineKey(tbl)] || []), ...Array.from({ length: n }, () => ({ ...empty }))] }))
  }

  const delLine = (tbl: 'supplier' | 'product', i: number) => {
    setSv((s: any) => ({ ...s, [lineKey(tbl)]: s[lineKey(tbl)].filter((_: any, idx: number) => idx !== i) }))
    if (tbl === 'supplier') {
      setSelSupplier((s) => s.filter((idx) => idx !== i).map((idx) => (idx > i ? idx - 1 : idx)))
    } else {
      setSelProduct((s) => s.filter((idx) => idx !== i).map((idx) => (idx > i ? idx - 1 : idx)))
    }
    if (editingTable === tbl && editingIndex === i) { setEditingTable(null); setEditingIndex(null) }
    else if (editingTable === tbl && editingIndex !== null && editingIndex > i) setEditingIndex(editingIndex - 1)
  }

  const duplicateLine = (tbl: 'supplier' | 'product', i: number) => {
    const lines = getLines(tbl)
    const cloned = { ...lines[i] }
    setSv((s: any) => ({ ...s, [lineKey(tbl)]: [...s[lineKey(tbl)], cloned] }))
  }

  // Thành tiền từng dòng (chỉ hiển thị trong popup chi tiết SP)
  const rowAmount = (it: any) => (Number(sv.request_qty) || 0) * (Number(it.price_by_volume) || 0) * (1 + (Number(it.vat) || 0) / 100)

  // Giữ dòng nếu có BẤT KỲ nội dung (nháp cho lưu dở dang) — chỉ bỏ dòng RỖNG hẳn.
  // (KHÔNG bắt buộc chọn NCC/tên SP khi Lưu — cái đó chỉ bắt khi Gửi duyệt.)
  // So với dòng rỗng mẫu: bỏ qua id + line_approve (mặc định 'Chờ duyệt') để không sót field nào.
  const LINE_META = new Set(['id', 'line_approve', 'line_approve_note'])
  const lineHasContent = (it: any, empty: any) => Object.keys(empty).some((k) => {
    if (LINE_META.has(k)) return false
    const v = it[k]
    if (typeof v === 'number') return v !== 0
    if (typeof v === 'boolean') return v === true
    return !!(v && String(v).trim())
  })
  const supHasContent = (it: any) => lineHasContent(it, emptySupplierLine)
  const prodHasContent = (it: any) => lineHasContent(it, emptyProductLine)

  // Ép các field kiểu số (num/computed/vat) về Number — tránh gửi "" cho cột float ở BE (422).
  const coerceNums = (it: any, keys: Set<string>) => {
    const o = { ...it }
    keys.forEach((k) => { o[k] = Number(o[k]) || 0 })
    return o
  }

  function buildBody() {
    return {
      pr_code: sv.pr_code, sr_code: sv.sr_code || '', survey_request_id: Number(sv.survey_request_id) || 0,
      received_date: sv.received_date, result_due_date: sv.result_due_date || '',
      item_group: sv.item_group, requirement_detail: sv.requirement_detail, nspt: sv.nspt,
      has_product_code: !!sv.has_product_code, item_code: sv.item_code, item_name: sv.item_name,
      request_qty: Number(sv.request_qty) || 0, uom: sv.uom, proposed_rate: Number(sv.proposed_rate) || 0,
      supplier_lines: (sv.supplier_lines || []).filter(supHasContent).map((it: any) => coerceNums(it, SUP_NUM_KEYS)),
      product_lines: (sv.product_lines || []).filter(prodHasContent).map((it: any) => coerceNums(it, PROD_NUM_KEYS)),
    }
  }

  async function save() {
    setErr(''); setMsg('')
    try {
      if (isNew) {
        const r = await api.post(API, buildBody()); const d = r.data.data
        await flushPendingAtt(d.supplier_lines || [], d.product_lines || [])   // gắn file chờ vào dòng mới
        try { localStorage.removeItem(DRAFT_KEY) } catch { /* ignore */ }
        navigate(`/surveys/${d.id}`)
      } else {
        const r = await api.patch(`${API}/${id}`, buildBody()); const d = r.data?.data
        await flushPendingAtt(d?.supplier_lines || [], d?.product_lines || [])
        setMsg('Đã lưu thành công'); loadAll()
      }
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }

  // Trả { msg, invalid } — invalid là tập ô còn trống (để tô đỏ). msg rỗng = hợp lệ.
  function validateSubmit(): { msg: string; invalid: Set<string> } {
    const invalid = new Set<string>()
    if (!sv.item_group) return { msg: 'Vui lòng chọn Phân loại', invalid }
    if (sv.has_product_code) {
      if (!sv.item_code) return { msg: 'Vui lòng chọn Mã VTBB/VL', invalid }
      if (!(Number(sv.request_qty) > 0)) return { msg: 'Vui lòng nhập Số lượng dự kiến mua', invalid }
      if (!sv.uom) return { msg: 'Vui lòng chọn ĐVT ở phần Thông tin tiếp nhận', invalid }
      if (!(Number(sv.proposed_rate) > 0)) return { msg: 'Vui lòng nhập Giá đề xuất', invalid }
    } else if (!String(sv.requirement_detail || '').trim()) {
      return { msg: 'Nhập Yêu cầu kỹ thuật & chất lượng, hoặc tick "Đã có mã sản phẩm sẵn"', invalid }
    }
    const validSupplier = (sv.supplier_lines || []).filter((it: any) => it.supplier_code)
    const validProduct = (sv.product_lines || []).filter((it: any) => it.product_name)
    if (validSupplier.length === 0 && validProduct.length === 0)
      return { msg: 'Cần ít nhất 1 dòng khảo sát NCC hoặc Sản phẩm (đã chọn NCC / nhập Tên SP).', invalid }

    const badSup: number[] = []
    for (let i = 0; i < (sv.supplier_lines || []).length; i++) {
      const it = sv.supplier_lines[i]
      if (!it.supplier_code) continue
      let bad = false
      for (const sec of SUPPLIER_SECTIONS) for (const f of sec.fields) {
        if (MGR_KEYS.includes(f.k) || f.k === 'note' || OPTIONAL_KEYS.includes(f.k)) continue
        const t = f.type || 'text'
        if (t === 'num' || t === 'computed' || t === 'check') continue
        if (!String(it[f.k] ?? '').trim()) { invalid.add(`supplier-${i}-${f.k}`); bad = true }
      }
      if (bad) badSup.push(i + 1)
    }
    const badProd: number[] = []
    for (let i = 0; i < (sv.product_lines || []).length; i++) {
      const it = sv.product_lines[i]
      if (!it.product_name) continue
      let bad = false
      for (const sec of PRODUCT_SECTIONS) for (const f of sec.fields) {
        if (MGR_KEYS.includes(f.k) || f.k === 'note' || OPTIONAL_KEYS.includes(f.k)) continue
        const t = f.type || 'text'
        if (t === 'num' || t === 'computed' || t === 'check') continue
        if (['sample_date', 'sample_qty', 'lab_result'].includes(f.k) && !it.sample_ready) continue
        if (!String(it[f.k] ?? '').trim()) { invalid.add(`product-${i}-${f.k}`); bad = true }
      }
      if (bad) badProd.push(i + 1)
    }
    const parts: string[] = []
    if (badSup.length) parts.push(`Khảo sát NCC dòng ${badSup.join(', ')}`)
    if (badProd.length) parts.push(`Khảo sát Sản phẩm dòng ${badProd.join(', ')}`)
    const msg = parts.length ? `${parts.join('; ')} còn thiếu thông tin bắt buộc — mở chi tiết dòng để điền các ô đang tô đỏ.` : ''
    return { msg, invalid }
  }

  async function doSubmit() {
    const { msg, invalid } = validateSubmit()
    if (msg) { setInvalidCells(invalid); toast.error(msg); return }
    setInvalidCells(new Set())
    try {
      await api.patch(`${API}/${id}`, buildBody())
      await api.post(`${API}/${id}/submit`); loadAll()
      toast.success('Đã gửi duyệt phiếu khảo sát')
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi gửi duyệt') }
  }

  async function saveLineApprove() {
    setErr(''); setMsg('')
    const payload = {
      supplier_lines: (sv.supplier_lines || []).filter((l: any) => l.id).map((l: any) => ({ id: l.id, line_approve: l.line_approve || '', line_approve_note: l.line_approve_note || '' })),
      product_lines: (sv.product_lines || []).filter((l: any) => l.id).map((l: any) => ({ id: l.id, line_approve: l.line_approve || '', line_approve_note: l.line_approve_note || '' })),
    }
    try { await api.patch(`${API}/${id}/line-approve`, payload); setMsg('Đã lưu duyệt dòng'); loadAll() }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi lưu duyệt dòng') }
  }

  async function changeLineApprove(tbl: 'supplier' | 'product', i: number, val: string) {
    setLine(tbl, i, { line_approve: val })
    const it = getLines(tbl)[i]
    if (liveApprove && it?.id) {
      setErr(''); setMsg('')
      try {
        const singlePayload = tbl === 'supplier'
          ? { supplier_lines: [{ id: it.id, line_approve: val, line_approve_note: it.line_approve_note || '' }], product_lines: [] }
          : { supplier_lines: [], product_lines: [{ id: it.id, line_approve: val, line_approve_note: it.line_approve_note || '' }] }
        await api.patch(`${API}/${id}/line-approve`, singlePayload)
        setMsg(`Đã lưu duyệt dòng ${i + 1}`)
      } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi lưu duyệt dòng') }
    }
  }

  // Lưu bổ sung dòng Thiếu thông tin qua fill endpoint
  async function saveFillLine(tbl: 'supplier' | 'product', i: number) {
    if (editingIndex === null) return
    const it = getLines(tbl)[i]
    if (!it?.id) { setErr('Dòng chưa có ID, cần lưu phiếu trước.'); return }
    setErr(''); setMsg('')
    // Lấy tất cả field nội dung (bỏ qua MGR_KEYS và line_approve*)
    const sections = tbl === 'supplier' ? SUPPLIER_SECTIONS : PRODUCT_SECTIONS
    const body: Record<string, any> = {}
    sections.flatMap((s) => s.fields).forEach((f) => {
      if (MGR_KEYS.includes(f.k)) return
      body[f.k] = it[f.k]
    })
    try {
      await api.patch(`${API}/${id}/lines/${tbl}/${it.id}/fill`, body)
      setMsg('Đã bổ sung dòng thành công'); setEditingTable(null); setEditingIndex(null); setFillMode(false)
      loadAll()
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi bổ sung dòng') }
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
    try { await api.post('/api/attachments', fd); loadAll() }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi tải file') }
  }

  async function loadLineAtt(lineId: number) {
    const r = await api.get('/api/attachments', { params: { entity: 'survey_line', entity_id: lineId } })
    setAttByLine((s) => ({ ...s, [lineId]: r.data.data }))
  }
  // Upload NGAY khi chọn (có progress). Dòng đã có id → gắn luôn; dòng mới → giữ chờ, gắn khi Lưu.
  async function uploadLineAtt(tbl: 'supplier' | 'product', i: number, fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'survey_line')
    Array.from(fl).forEach((f) => fd.append('files', f))
    setErr(''); setAttProgress(0)
    try {
      const r = await api.post('/api/attachments/upload-file', fd, {
        onUploadProgress: (e: any) => { if (e.total) setAttProgress(Math.round((e.loaded * 100) / e.total)) },
      })
      const metas = r.data.data || []
      const lineId = getLines(tbl)[i]?.id
      if (lineId) {
        await api.post('/api/attachments/register', { entity: 'survey_line', entity_id: lineId, file_ids: metas.map((m: any) => m.file_id) })
        await loadLineAtt(lineId)
      } else {
        const key = `${tbl}-${i}`
        setPendingAtt((p) => ({ ...p, [key]: [...(p[key] || []), ...metas] }))
      }
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || ex?.response?.data?.message || 'Lỗi tải file') }
    finally { setAttProgress(null) }
  }
  // Gắn file chờ vào dòng sau khi lưu. buildBody LỌC bỏ dòng rỗng → phải map
  // index local (chỉ đếm dòng có supplier_code/product_name) sang dòng đã lưu.
  async function flushPendingAtt(supLines: any[], prodLines: any[]) {
    const supMap: Record<number, any> = {}; let j = 0
    ;(sv.supplier_lines || []).forEach((it: any, idx: number) => { if (supHasContent(it)) { supMap[idx] = supLines[j]; j++ } })
    const prodMap: Record<number, any> = {}; let k = 0
    ;(sv.product_lines || []).forEach((it: any, idx: number) => { if (prodHasContent(it)) { prodMap[idx] = prodLines[k]; k++ } })
    for (const [key, metas] of Object.entries(pendingAtt)) {
      const dash = key.lastIndexOf('-'); const tbl = key.slice(0, dash); const i = Number(key.slice(dash + 1))
      const line = tbl === 'supplier' ? supMap[i] : prodMap[i]
      if (line?.id && (metas as any[]).length) {
        try { await api.post('/api/attachments/register', { entity: 'survey_line', entity_id: line.id, file_ids: (metas as any[]).map((m) => m.file_id) }) } catch {}
      }
    }
    setPendingAtt({})
  }
  const removePendingAtt = (key: string, fi: number) =>
    setPendingAtt((p) => ({ ...p, [key]: (p[key] || []).filter((_, k) => k !== fi) }))

  function openLine(tbl: 'supplier' | 'product', i: number) {
    setEditingTable(tbl)
    setEditingIndex(i)
    const lid = getLines(tbl)[i]?.id
    if (lid) loadLineAtt(lid)
  }

  // ---- Field renderer in popup ----
  function lineField(f: SecField, tbl: 'supplier' | 'product', i: number) {
    const lines = getLines(tbl)
    const it = lines[i]; const k = f.k; const t = f.type || 'text'
    // fillMode: cho sửa tất cả field nội dung (không phải MGR) khi popup ở chế độ Bổ sung
    const ce = MGR_KEYS.includes(k) ? canEditApprove : (editable || fillMode)
    if (t === 'computed') return <input value={fmt(rowAmount(it))} disabled />
    if (t === 'check') return (
      <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: ce ? 'pointer' : 'default', height: 40 }}>
        <input type="checkbox" checked={!!it[k]} disabled={!ce} onChange={(e) => setLine(tbl, i, { [k]: e.target.checked })} style={{ width: 18, height: 18 }} /> {f.label}
      </label>
    )
    if (t === 'date') return <input type="date" value={it[k] ?? ''} disabled={!ce} onChange={(e) => setLine(tbl, i, { [k]: e.target.value })} />
    if (t === 'num') return <NumCell value={it[k]} disabled={!ce} onChange={(v: number) => setLine(tbl, i, { [k]: v })} />
    if (t === 'textarea') return <textarea value={it[k] ?? ''} disabled={!ce} style={{ minHeight: 64 }} onChange={(e) => setLine(tbl, i, { [k]: e.target.value })} />
    if (t === 'supplier') return <SearchSelect value={it[k] ?? ''} disabled={!ce} placeholder="Chọn/tìm NCC…"
      options={suppliers.map((s) => ({ value: s.code, label: `${s.code} — ${s.name}` }))}
      onChange={(v) => { const sup = suppliers.find((s) => s.code === v); setLine(tbl, i, sup ? { supplier_code: sup.code, supplier_name: sup.name, tax_code: sup.tax_code, reg_address: sup.address } : { supplier_code: v }) }} />
    if (t === 'unit') return <SearchSelect value={it[k] ?? ''} options={units} disabled={!ce} placeholder="Chọn/tìm ĐVT…" onChange={(v) => setLine(tbl, i, { [k]: v })} />
    if (t === 'vat') return <SearchSelect value={String(it[k] ?? '')} options={VAT_OPTS} disabled={!ce} placeholder="Chọn VAT…" onChange={(v) => setLine(tbl, i, { [k]: Number(v) })} />
    if (t === 'approve') return <SearchSelect value={it[k] || 'Chờ duyệt'} options={APPROVE_OPTS} colorMap={APPROVE_COLOR} disabled={!canEditApprove} placeholder="Chọn…" onChange={(v) => setLine(tbl, i, { [k]: v })} />
    return <input value={it[k] ?? ''} disabled={!ce} onChange={(e) => setLine(tbl, i, { [k]: e.target.value })} />
  }

  // ---- Cell renderer in summary table ----
  function cell(col: Col, tbl: 'supplier' | 'product', i: number) {
    const lines = getLines(tbl)
    const it = lines[i]
    if (col.key === 'line_approve') {
      if (canEditApprove)
        return <div style={{ width: '100%' }}><SearchSelect variant="table" colorMap={APPROVE_COLOR} value={it[col.key] || 'Chờ duyệt'} options={APPROVE_OPTS} placeholder="Duyệt…" onChange={(v) => changeLineApprove(tbl, i, v)} /></div>
      const st = it.line_approve || 'Chờ duyệt'; const c = APPROVE_COLOR[st] || '#64748b'
      return <span className="badge" style={{ background: `${c}1a`, color: c, border: `1px solid ${c}55` }}>{st}</span>
    }
    if (!editable) {
      if (col.type === 'computed') return fmt(rowAmount(it))
      if (col.type === 'check') return it[col.key] ? '✓' : ''
      if (col.type === 'num') return it[col.key] ? fmt(it[col.key]) : ''
      return it[col.key] ?? ''
    }
    if (col.type === 'computed') return <span style={{ fontWeight: 500 }}>{fmt(rowAmount(it))}</span>
    if (col.type === 'check') return <input type="checkbox" checked={!!it[col.key]} onChange={(e) => setLine(tbl, i, { [col.key]: e.target.checked })} />
    if (col.type === 'num') return <NumCell className="cell-input" style={{ width: '100%' }} value={it[col.key]} onChange={(v: number) => setLine(tbl, i, { [col.key]: v })} />
    if (col.type === 'date') return <input className="cell-input" type="date" style={{ width: '100%' }} value={it[col.key] ?? ''} onChange={(e) => setLine(tbl, i, { [col.key]: e.target.value })} />
    if (col.type === 'select') return (
      <div style={{ width: '100%' }}><SearchSelect variant="table" colorMap={col.key === 'line_approve' ? APPROVE_COLOR : undefined}
        value={String(it[col.key] ?? '')} options={col.options!.filter((o) => o !== '')} placeholder="Chọn…"
        onChange={(v) => setLine(tbl, i, { [col.key]: col.key === 'vat' ? Number(v) : v })} /></div>
    )
    if (col.type === 'unit') return (
      <div style={{ width: '100%' }}><SearchSelect variant="table" value={it[col.key] ?? ''} options={units} placeholder="Chọn/tìm ĐVT…" onChange={(v) => setLine(tbl, i, { [col.key]: v })} /></div>
    )
    if (col.type === 'supplier') return (
      <div style={{ width: '100%' }}><SearchSelect variant="table" value={it[col.key] ?? ''} placeholder="Chọn/tìm NCC…"
        options={suppliers.map((s) => ({ value: s.code, label: `${s.code} — ${s.name}` }))}
        onChange={(v) => { const sup = suppliers.find((s) => s.code === v); setLine(tbl, i, sup ? { supplier_code: sup.code, supplier_name: sup.name, tax_code: sup.tax_code, reg_address: sup.address } : { supplier_code: v }) }} /></div>
    )
    return <input className="cell-input" style={{ width: '100%' }} value={it[col.key] ?? ''} onChange={(e) => setLine(tbl, i, { [col.key]: e.target.value })} />
  }

  // ---- Render one survey table section (NCC or Product) ----
  function renderSurveyTable(
    tbl: 'supplier' | 'product',
    title: string,
    tableCols: Col[],
    selIdxs: number[],
    setSelIdxs: React.Dispatch<React.SetStateAction<number[]>>,
  ) {
    const lines = getLines(tbl)
    const toggleSelect = (i: number) => setSelIdxs((s) => s.includes(i) ? s.filter((idx) => idx !== i) : [...s, i])
    const toggleSelectAll = () => { if (selIdxs.length === lines.length) setSelIdxs([]); else setSelIdxs(lines.map((_: any, i: number) => i)) }
    const deleteSelected = async () => {
      if (await askConfirm({ message: 'Xóa các dòng đã chọn?' })) {
        setSv((s: any) => ({ ...s, [lineKey(tbl)]: s[lineKey(tbl)].filter((_: any, idx: number) => !selIdxs.includes(idx)) }))
        setSelIdxs([])
        if (editingTable === tbl) setEditingIndex(null)
      }
    }
    return (
      <div className="card" style={{ padding: 18, marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
          <h3 className="sec-title" style={{ margin: 0, border: 'none', padding: 0 }}>{title}</h3>
          <div style={{ display: 'flex', gap: 8 }}>
            {editable && selIdxs.length > 0 && (
              <button className="btn secondary" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={deleteSelected}>
                <i className="ti ti-trash" /> Xóa dòng đã chọn ({selIdxs.length})
              </button>
            )}
            {editable && (
              <>
                <button className="btn ghost" onClick={() => addLines(tbl, 1)} style={{ height: 32, fontSize: 13 }}><i className="ti ti-plus" />Thêm dòng</button>
                <button className="btn ghost" onClick={async () => { const s = await askPrompt({ message: 'Thêm bao nhiêu dòng?', defaultValue: '3' }); const n = parseInt(s || '0') || 0; if (n > 0) addLines(tbl, n) }} style={{ height: 32, fontSize: 13 }}><i className="ti ti-rows" />Thêm nhiều</button>
              </>
            )}
          </div>
        </div>

        <div className="items-scroll">
          <table className="items-table" style={{ width: '100%', minWidth: tbl === 'supplier' ? 1350 : 1400, tableLayout: 'fixed' }}>
            <thead>
              <tr>
                {editable && <th style={{ width: 36, textAlign: 'center' }}><input type="checkbox" checked={lines.length > 0 && selIdxs.length === lines.length} onChange={toggleSelectAll} /></th>}
                <th style={{ width: 36 }}>#</th>
                {tableCols.map((c) => <th key={c.key} style={{ width: c.w }}>{c.label}</th>)}
                <th style={{ width: 100, textAlign: 'center' }}>Hành động</th>
              </tr>
            </thead>
            <tbody>
              {lines.map((_: any, i: number) => (
                <tr key={i} style={selIdxs.includes(i) ? { background: '#f0f9ff' } : {}}>
                  {editable && (
                    <td style={{ textAlign: 'center' }}>
                      <input type="checkbox" checked={selIdxs.includes(i)} onChange={() => toggleSelect(i)} />
                    </td>
                  )}
                  <td>{i + 1}</td>
                  {tableCols.map((c) => {
                    const bad = editable && invalidCells.has(`${tbl}-${i}-${c.key}`)
                    return (
                      <td key={c.key} className={bad ? 'cell-invalid' : undefined}
                        style={bad ? { boxShadow: 'inset 0 0 0 1px #fca5a5', borderRadius: 6 } : undefined}>
                        {cell(c, tbl, i)}
                      </td>
                    )
                  })}
                  <td style={{ textAlign: 'center' }}>
                    <div style={{ display: 'inline-flex', gap: 6, flexWrap: 'nowrap' }}>
                      <button className="icon-btn" title="Chỉnh sửa chi tiết" onClick={() => { setFillMode(false); openLine(tbl, i) }}>
                        <i className="ti ti-edit" style={{ fontSize: 16, color: 'var(--teal)' }} />
                      </button>
                      {!editable && can('survey', 'write') && getLines(tbl)[i]?.line_approve === 'Thiếu thông tin' && (
                        <button className="btn ghost" title="Bổ sung nội dung dòng thiếu thông tin"
                          style={{ height: 26, padding: '0 8px', fontSize: 11.5, color: '#ea580c', borderColor: '#ea580c' }}
                          onClick={() => { setFillMode(true); openLine(tbl, i) }}>
                          <i className="ti ti-pencil-plus" style={{ fontSize: 13 }} /> Bổ sung
                        </button>
                      )}
                      {editable && (
                        <button className="icon-btn" title="Nhân bản dòng" onClick={() => duplicateLine(tbl, i)}>
                          <i className="ti ti-copy" style={{ fontSize: 16, color: 'var(--muted)' }} />
                        </button>
                      )}
                      {editable && (
                        <button className="icon-btn" title="Xóa dòng" onClick={async () => { if (await askConfirm({ message: 'Xóa dòng này?' })) delLine(tbl, i) }}>
                          <i className="ti ti-trash" style={{ fontSize: 16, color: 'var(--red)' }} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {lines.length === 0 && (
                <tr><td colSpan={tableCols.length + (editable ? 3 : 2)} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Chưa có dòng nào</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    )
  }

  const isLogShown = !isNew && logs.length > 0

  // Determine active popup data
  const activeLines = editingTable ? getLines(editingTable) : []
  const activeSections = editingTable === 'supplier' ? SUPPLIER_SECTIONS : PRODUCT_SECTIONS
  const activeIt = editingIndex !== null ? activeLines[editingIndex] : null
  const activeLid = activeIt?.id as number | undefined
  const activeAtts = (activeLid && attByLine[activeLid]) || []
  const activePendKey = editingTable && editingIndex !== null ? `${editingTable}-${editingIndex}` : ''
  const activePending = (activePendKey && pendingAtt[activePendKey]) || []

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/surveys')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>{isNew ? 'Tạo Phiếu Khảo sát' : `Phiếu Khảo sát ${sv.code || ''}`}</h2>
        {!isNew && sv.status !== 'draft' && srBadge(sv.status)}
        <span style={{ flex: 1 }} />
        {editable && can('survey', isNew ? 'create' : 'write') && (
          <button className="btn" onClick={save}>{isNew ? 'Tạo' : 'Lưu'}</button>
        )}
        {!isNew && editable && can('survey', 'write') && (
          <button className="btn secondary" onClick={doSubmit}><i className="ti ti-send" />Gửi duyệt</button>
        )}
        {!isNew && sv.status === 'submitted' && canApprove && (
          <>
            <button className="btn" onClick={async () => { if (await askConfirm({ message: 'Duyệt cả phiếu khảo sát này?', confirmText: 'Duyệt phiếu', danger: false })) action('approve') }}><i className="ti ti-check" />Duyệt phiếu</button>
            <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }}
              onClick={async () => { const r = await askPrompt({ title: 'Từ chối phiếu', message: 'Lý do từ chối (khóa phiếu):', danger: true, confirmText: 'Từ chối' }); if (r !== null) action('cancel', { reason: r }) }}>
              <i className="ti ti-ban" />Từ chối
            </button>
            <button className="btn ghost" style={{ color: 'var(--amber)', borderColor: 'var(--amber)' }}
              onClick={async () => { const r = await askPrompt({ title: 'Trả lại phiếu', message: 'Lý do trả lại (để khảo sát lại):' }); if (r !== null) action('reject', { reason: r }) }}>
              <i className="ti ti-arrow-back-up" />Trả lại
            </button>
          </>
        )}
        {!isNew && can('survey', 'delete') && (sv.status === 'draft' || sv.status === 'cancelled') && (
          <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }}
            onClick={async () => { if (await askConfirm({ message: 'Xóa phiếu khảo sát này?' })) { try { await api.delete(`${API}/${id}`); navigate('/surveys') } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi xóa') } } }}>
            <i className="ti ti-trash" />Xóa
          </button>
        )}
      </div>

      <div className={isLogShown ? 'detail-grid' : ''}>
        <div>
          {/* Header: Thông tin tiếp nhận */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title">Thông tin tiếp nhận</h3>
            <div className="form-grid">
              <div className="form-row">
                <label>Yêu cầu khảo sát <span style={{ color: 'var(--muted)', fontWeight: 400 }}>(nếu có)</span></label>
                <input list="ycks-list" placeholder="Nhập/chọn mã YCKS để tự điền…" value={sv.sr_code || ''} disabled={!editable} onChange={(e) => onPickPr(e.target.value)} />
                <datalist id="ycks-list">{prList.map((p) => <option key={p.id} value={p.code}>{p.purpose || ''}</option>)}</datalist>
              </div>
              <div className="form-row"><label>Ngày tiếp nhận</label><input type="date" value={sv.received_date || ''} disabled={!editable} onChange={(e) => setH('received_date', e.target.value)} /></div>
              <div className="form-row"><label>Ngày dự kiến trả KQ</label><input type="date" value={sv.result_due_date || ''} disabled={!editable} onChange={(e) => setH('result_due_date', e.target.value)} /></div>
              <div className="form-row">
                <label>Phân loại</label>
                <SearchSelect value={sv.item_group} options={groups} disabled={!editable} placeholder="Chọn/tìm phân loại…" onChange={(v) => setH('item_group', v)} />
              </div>
              <div className="form-row"><label>NSPT phụ trách (người tạo)</label><input value={sv.nspt || ''} disabled placeholder="Tự động theo người tạo" /></div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Yêu cầu kỹ thuật & chất lượng</label>
                <textarea value={sv.requirement_detail || ''} disabled={!editable} placeholder="Mô tả thông số kỹ thuật, chất lượng, yêu cầu khác…" onChange={(e) => setH('requirement_detail', e.target.value)} />
              </div>
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

          {/* Section: Khảo sát Nhà cung cấp */}
          {renderSurveyTable('supplier', 'Khảo sát Nhà cung cấp', supplierTableCols, selSupplier, setSelSupplier)}

          {/* Section: Khảo sát Sản phẩm */}
          {renderSurveyTable('product', 'Khảo sát Sản phẩm', productTableCols, selProduct, setSelProduct)}

          {sv.approve_note && (
            <div className="card" style={{ padding: 14, marginBottom: 16 }}><b>Ghi chú duyệt:</b> {sv.approve_note}</div>
          )}

          {/* Đính kèm file (survey-level) */}
          {!isNew && (
            <div className="card" style={{ padding: 18, marginBottom: 16 }}>
              <h3 className="sec-title"><i className="ti ti-paperclip" /> Chứng từ đính kèm</h3>
              {can('survey', 'write') && (
                <div style={{ marginBottom: 8 }}>
                  <input type="file" id="survey-file-upload" multiple style={{ display: 'none' }} onChange={(e) => uploadFiles(e.target.files)} />
                  <label htmlFor="survey-file-upload" className="btn ghost" style={{ cursor: 'pointer', height: 32, fontSize: 13 }}><i className="ti ti-upload" /> Tải file lên</label>
                </div>
              )}
              <div style={{ marginTop: 6, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {files.map((f) => (
                  <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                    <i className="ti ti-file" />
                    <a href={f.url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{f.filename}</a>
                    {can('survey', 'write') && (
                      <button className="icon-btn" onClick={async () => { if (await askConfirm({ message: 'Xóa file?' })) { await api.delete(`/api/attachments/${f.id}`); loadAll() } }}>
                        <i className="ti ti-trash" style={{ color: 'var(--red)' }} />
                      </button>
                    )}
                  </div>
                ))}
                {files.length === 0 && <span style={{ color: '#999', fontSize: 13 }}>Chưa có file nào.</span>}
              </div>
            </div>
          )}

        </div>

        {isLogShown && (
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title"><i className="ti ti-history" /> Lịch sử thao tác</h3>
            <div className="timeline">
              {logs.map((l, i) => (
                <div key={i} className="tl-item">
                  <span className={'tl-dot ' + (l.action === 'approved' ? 'create' : l.action === 'rejected' ? 'delete' : l.action)} />
                  <div>
                    <div style={{ fontSize: 13 }}><b>{l.by}</b> — {l.action_label}{l.message ? `: ${l.message}` : ''}</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)' }}>{fmtDateTime(l.at)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Popup chi tiết dòng */}
      {editingTable !== null && editingIndex !== null && activeIt && (() => {
        return (
          <div
            style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.45)', zIndex: 100, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '4vh 12px', overflowY: 'auto' }}
            onClick={() => { setEditingTable(null); setEditingIndex(null); setFillMode(false) }}
          >
            <div
              style={{ width: 980, maxWidth: '100%', background: '#fff', borderRadius: 12, boxShadow: '0 20px 25px -5px rgba(0,0,0,0.15)', display: 'flex', flexDirection: 'column', maxHeight: '92vh', overflow: 'hidden' }}
              onClick={(e) => e.stopPropagation()}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
                <h3 style={{ margin: 0, fontSize: 16, color: 'var(--navy)', fontWeight: 600 }}>
                  {editingTable === 'supplier' ? 'NCC' : 'SP'} — {fillMode ? <span style={{ color: '#ea580c' }}>Bổ sung</span> : 'Chi tiết'} dòng #{editingIndex + 1}
                  {activeIt.supplier_code ? ` — ${activeIt.supplier_code}` : ''}
                  {activeIt.product_name ? ` — ${activeIt.product_name}` : ''}
                </h3>
                <button className="icon-btn" onClick={() => { setEditingTable(null); setEditingIndex(null); setFillMode(false) }}>
                  <i className="ti ti-x" style={{ fontSize: 18 }} />
                </button>
              </div>

              <div style={{ padding: '16px 20px', overflowY: 'auto', flex: 1 }}>
                {activeSections.map((sec) => (
                  <div key={sec.title} style={{ marginBottom: 18 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--teal)', textTransform: 'uppercase', letterSpacing: .3, marginBottom: 10, paddingBottom: 6, borderBottom: '1px solid var(--border)' }}>{sec.title}</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px 20px' }}>
                      {sec.fields.map((f) => {
                        const bad = editingTable !== null && editingIndex !== null && invalidCells.has(`${editingTable}-${editingIndex}-${f.k}`)
                        return (
                          <div className="form-row" key={f.k} style={{ ...(f.full ? { gridColumn: '1 / -1' } : {}), ...(bad ? { borderRadius: 8, outline: '1px solid #fca5a5', outlineOffset: 3 } : {}) }}>
                            <label style={bad ? { color: '#e06666' } : undefined}>{f.label}{bad ? ' *' : ''}</label>
                            {lineField(f, editingTable, editingIndex)}
                          </div>
                        )
                      })}
                    </div>
                  </div>
                ))}

                {/* Đính kèm file theo dòng */}
                <div style={{ marginBottom: 4 }}>
                  <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--teal)', textTransform: 'uppercase', letterSpacing: .3, marginBottom: 10, paddingBottom: 6, borderBottom: '1px solid var(--border)' }}>Đính kèm file (theo dòng)</div>
                  <div>
                    {editable && (
                      <div style={{ marginBottom: 8 }}>
                        <input type="file" id="sla-upload" multiple accept=".pdf,.jpg,.jpeg,.png,.xlsx,.xls" style={{ display: 'none' }}
                          disabled={attProgress !== null}
                          onChange={(e) => { if (editingTable && editingIndex !== null) uploadLineAtt(editingTable, editingIndex, e.target.files); (e.currentTarget as any).value = '' }} />
                        <label htmlFor="sla-upload" className="btn ghost" style={{ cursor: attProgress !== null ? 'default' : 'pointer', height: 32, fontSize: 13, opacity: attProgress !== null ? .6 : 1 }}>
                          <i className="ti ti-upload" /> {attProgress !== null ? `Đang tải ${attProgress}%…` : 'Tải file lên'}
                        </label>
                        {attProgress !== null && (
                          <div style={{ height: 4, background: '#e5e7eb', borderRadius: 4, marginTop: 6, overflow: 'hidden' }}>
                            <div style={{ height: '100%', width: `${attProgress}%`, background: 'var(--teal)', transition: 'width .15s' }} />
                          </div>
                        )}
                        <div style={{ fontSize: 11.5, color: '#94a3b8', marginTop: 4 }}>Tối đa 10MB/file · pdf, ảnh, excel{!activeLid ? ' · sẽ lưu cùng phiếu' : ''}</div>
                      </div>
                    )}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {activeAtts.map((f) => (
                        <div key={'a' + f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                          <i className="ti ti-file" />
                          <a href={f.url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{f.filename}</a>
                          {editable && (
                            <button className="icon-btn" onClick={async () => { if (await askConfirm({ message: 'Xóa file?' })) { await api.delete(`/api/attachments/${f.id}`); if (activeLid) loadLineAtt(activeLid) } }}>
                              <i className="ti ti-trash" style={{ color: 'var(--red)' }} />
                            </button>
                          )}
                        </div>
                      ))}
                      {activePending.map((f, fi) => (
                        <div key={'p' + fi} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                          <i className="ti ti-clock" style={{ color: '#d97706' }} />
                          <a href={f.url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{f.filename}</a>
                          <span style={{ fontSize: 11, color: '#d97706' }}>chờ lưu</span>
                          {editable && (
                            <button className="icon-btn" onClick={() => removePendingAtt(activePendKey, fi)}>
                              <i className="ti ti-x" style={{ color: 'var(--red)' }} />
                            </button>
                          )}
                        </div>
                      ))}
                      {activeAtts.length === 0 && activePending.length === 0 && <span style={{ color: '#999', fontSize: 13 }}>Chưa có file nào.</span>}
                    </div>
                  </div>
                </div>
              </div>

              <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                <button className="btn ghost" style={{ height: 36, padding: '0 18px', fontSize: 13 }} onClick={() => { setEditingTable(null); setEditingIndex(null); setFillMode(false) }}>Đóng</button>
                {fillMode && editingTable && editingIndex !== null && (
                  <button className="btn" style={{ height: 36, padding: '0 18px', fontSize: 13, background: '#ea580c', borderColor: '#ea580c' }}
                    onClick={() => saveFillLine(editingTable, editingIndex)}>
                    <i className="ti ti-device-floppy" />Lưu bổ sung
                  </button>
                )}
                {liveApprove && !fillMode && (
                  <button className="btn" style={{ height: 36, padding: '0 18px', fontSize: 13 }} onClick={() => { saveLineApprove(); setEditingTable(null); setEditingIndex(null) }}>
                    <i className="ti ti-check" />Lưu duyệt dòng
                  </button>
                )}
              </div>
            </div>
          </div>
        )
      })()}
    </div>
  )
}
