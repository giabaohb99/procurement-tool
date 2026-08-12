import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { askConfirm, askPrompt } from '../components/confirm'
import { useAuth } from '../auth/AuthContext'
import DateInput from '../components/DateInput'
import NotFound from '../components/NotFound'
import NumberInput from '../components/NumberInput'
import SearchSelect from '../components/SearchSelect'
import { toast } from '../components/toast'
import { fmtDateTime } from '../utils/datetime'
import DocumentAttachmentSection from '../components/DocumentAttachmentSection'
import AuditTimeline from '../components/AuditTimeline'

const API = '/api/payment-requests'
const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const ST: Record<string, { label: string; cls: string }> = {
  draft: { label: 'Nháp', cls: 'gray' }, submitted: { label: 'Chờ duyệt', cls: 'warn' },
  approved: { label: 'Đã duyệt', cls: 'ok' }, paid: { label: 'Đã chi', cls: 'ok' },
  cancelled: { label: 'Đã từ chối', cls: 'err' },
}
const stBadge = (s: string) => { const x = ST[s] || { label: s, cls: 'gray' }; return <span className={'badge ' + x.cls}>{x.label}</span> }

// CR-035: hình thức thanh toán — quyết định bản in có in cụm "Thông tin chuyển khoản" hay để trống
const PM: Record<string, string> = { transfer: 'Chuyển khoản', cash: 'Tiền mặt' }
const pmHint = (m: string) => m === 'cash'
  ? 'Bản in để TRỐNG cụm "Thông tin chuyển khoản".'
  : 'Bản in lấy số tài khoản / ngân hàng của nhà cung cấp.'
const hintStyle = { fontSize: 12, color: 'var(--muted)', marginTop: 4 } as const

export default function PaymentRequestDetail() {
  const { id } = useParams()
  // CR-025: `/payment-requests/new` KHÔNG còn là "phiếu đã tạo" — là màn nhập liệu, chỉ ghi DB khi bấm Tạo.
  return id === 'new' ? <PaymentRequestCreate /> : <PaymentRequestView key={id} />
}

/** Dòng trên màn TẠO. `payable_id = 0` là dòng gõ tay (form trắng) — chưa gắn khoản nợ nào. */
type NewLine = {
  key: number
  payable_id: number
  supplier_code: string
  supplier_name: string
  source_type: string
  po_code: string
  invoice_no: string
  invoice_date: string
  due_date: string
  payable_total: number
  payable_paid: number
  amount: number
}

let seqKey = 0
const blankLine = (): NewLine => ({
  key: ++seqKey, payable_id: 0, supplier_code: '', supplier_name: '', source_type: '',
  po_code: '', invoice_no: '', invoice_date: '', due_date: '', payable_total: 0, payable_paid: 0, amount: 0,
})
const fromPayable = (r: any): NewLine => ({
  key: ++seqKey, payable_id: r.id, supplier_code: r.supplier_code || '', supplier_name: r.supplier_name || '',
  source_type: r.source_type || 'goods', po_code: r.po_code || '', invoice_no: r.invoice_no || '',
  invoice_date: r.invoice_date || '', due_date: r.due_date || '',
  payable_total: Number(r.total) || 0, payable_paid: Number(r.paid_amount) || 0,
  amount: Number(r.remaining) || 0,
})

/** Màn TẠO phiếu. Hai lối vào:
 *  - từ màn Công nợ (`?payables=1,2,3`): nạp sẵn các khoản đã tick;
 *  - FORM TRẮNG (CR-066): tự chọn NCC/công ty rồi gõ tay từng dòng.
 *  Cả hai lối đều cho sửa Số hóa đơn · Ngày hóa đơn · Đề nghị trả; Tổng nợ / Đã trả / Hạn trả
 *  là số ĐỌC TỪ CÔNG NỢ nên không sửa ở đây. Thoát giữa chừng = không sinh phiếu nháp nào. */
function PaymentRequestCreate() {
  const navigate = useNavigate()
  const location = useLocation()
  const [sp] = useSearchParams()
  const idsParam = sp.get('payables') || ''
  const ids = useMemo(() => idsParam.split(',').map(Number).filter(Boolean), [idsParam])
  const blankMode = !ids.length

  const [lines, setLines] = useState<NewLine[]>(
    () => ((location.state as any)?.rows || []).map(fromPayable))
  const [loading, setLoading] = useState(false)
  const [requestDate, setRequestDate] = useState(new Date().toISOString().slice(0, 10))
  const [paymentMethod, setPaymentMethod] = useState('transfer')
  const [note, setNote] = useState('')
  const [saving, setSaving] = useState(false)
  // Form trắng: phần đầu phiếu do người lập chọn (đi từ Công nợ/PO thì lấy theo state hoặc khoản nợ)
  const locState = (location.state as any) || {}
  const [supplierCode, setSupplierCode] = useState(() => locState.supplier_code || (locState.rows?.[0]?.supplier_code) || '')
  const [companyId, setCompanyId] = useState(() => locState.company_id || 0)
  const [sourceType, setSourceType] = useState(() => locState.source_type || 'goods')
  const [suppliers, setSuppliers] = useState<any[]>([])
  const [companies, setCompanies] = useState<any[]>([])

  // Mở lại bằng link/F5 (không còn state điều hướng) → nạp lại đúng các khoản đã tick
  useEffect(() => {
    if (!ids.length || lines.length) return
    setLoading(true)
    api.get('/api/payables', { params: { ids: ids.join(','), year: 'all', page_size: 500 } })
      .then((r) => setLines((r.data.data.items || []).map(fromPayable)))
      .finally(() => setLoading(false))
  }, [idsParam])

  useEffect(() => {
    if (!blankMode) return
    api.get('/api/suppliers', { params: { page_size: 1000 } }).then((r) => setSuppliers(r.data.data.items))
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    setLines((s) => (s.length ? s : [blankLine()]))
  }, [blankMode])

  const setLine = (key: number, patch: Partial<NewLine>) =>
    setLines((s) => s.map((l) => (l.key === key ? { ...l, ...patch } : l)))

  // Dòng gõ tay bám vào NCC nào: form trắng thì theo ô đã chọn, đi từ Công nợ thì theo khoản nợ đầu tiên
  const headPayable = lines.find((l) => l.payable_id)
  const headSupplier = blankMode ? supplierCode : (headPayable?.supplier_code || '')
  const headSource = blankMode ? sourceType : (headPayable?.source_type || 'goods')
  // Server tách mỗi (NCC × loại công nợ) thành 1 phiếu — hiện trước để người dùng biết sẽ ra mấy phiếu
  const groups = useMemo(() => {
    const m = new Set<string>()
    lines.forEach((l) => m.add(l.payable_id ? `${l.supplier_code}||${l.source_type}` : `${headSupplier}||${headSource}`))
    return Array.from(m)
  }, [lines, headSupplier, headSource])
  const noInvoice = lines.filter((l) => !l.invoice_no.trim())
  const total = lines.reduce((s, l) => s + (Number(l.amount) || 0), 0)

  async function create() {
    if (!lines.length) { toast.error('Chưa có dòng nào'); return }
    if (!headSupplier) { toast.error('Chưa chọn nhà cung cấp'); return }
    setSaving(true)
    try {
      const payload: any = {
        request_date: requestDate, note, payment_method: paymentMethod,
        supplier_code: headSupplier, company_id: companyId, source_type: headSource,
        lines: lines.map((l) => ({
          payable_id: l.payable_id, po_code: l.po_code, invoice_no: l.invoice_no,
          invoice_date: l.invoice_date, amount: Number(l.amount) || 0,
        })),
      }
      const r = await api.post(API, payload)
      const created = r.data.data || []
      toast.success(created.length === 1 ? 'Đã tạo yêu cầu thanh toán'
        : `Đã tạo ${created.length} phiếu yêu cầu thanh toán (mỗi nhà cung cấp 1 phiếu).`)
      if (created.length === 1) navigate(`/payment-requests/${created[0].id}`, { replace: true })
      else navigate('/payment-requests', { replace: true })
    } catch (ex: any) { toast.error(ex?.response?.data?.error?.message || 'Lỗi tạo yêu cầu thanh toán') }
    finally { setSaving(false) }
  }

  if (loading) return <div style={{ padding: 40 }}>Đang tải...</div>

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate(-1)}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>Tạo yêu cầu thanh toán</h2>
        <span className="badge gray">Chưa lưu</span>
        <span style={{ flex: 1 }} />
        {blankMode && <button className="btn ghost" onClick={() => navigate('/payables')}><i className="ti ti-cash" />Chọn từ Công nợ</button>}
        <button className="btn" disabled={saving || !lines.length} onClick={create}>
          <i className="ti ti-check" />{saving ? 'Đang tạo…' : `Tạo ${groups.length > 1 ? `${groups.length} phiếu` : 'phiếu'}`}
        </button>
      </div>

      <div className="card" style={{ padding: 14, marginBottom: 16, borderLeft: '4px solid var(--teal)' }}>
        Soát lại số tiền đề nghị rồi bấm <b>Tạo phiếu</b>. Rời màn này mà chưa bấm thì <b>không phiếu nháp nào được sinh ra</b>.
        {groups.length > 1 && <> Hệ thống sẽ tách thành <b>{groups.length} phiếu</b> (mỗi nhà cung cấp / loại công nợ 1 phiếu).</>}
      </div>

      {noInvoice.length > 0 && (
        <div className="card" style={{ padding: 14, marginBottom: 16, borderLeft: '4px solid var(--amber)' }}>
          <b>{noInvoice.length} dòng chưa có Số hóa đơn</b> — vẫn tạo và in bản nháp để trình ký được (ô hóa đơn in trắng, điền tay),
          nhưng <b>phải điền đủ và khớp khoản công nợ mới gửi duyệt được</b>.
        </div>
      )}

      <div className="card" style={{ padding: 18, marginBottom: 16 }}>
        <h3 className="sec-title">Thông tin phiếu</h3>
        <div className="form-grid">
          {blankMode && (
            <>
              <div className="form-row"><label>Nhà cung cấp <span style={{ color: 'var(--red)' }}>*</span></label>
                <SearchSelect value={supplierCode} placeholder="Chọn/tìm NCC…"
                  options={suppliers.map((s) => ({ value: s.code, label: `${s.code} — ${s.name}` }))}
                  onChange={setSupplierCode} />
              </div>
              <div className="form-row"><label>Công ty</label>
                <SearchSelect value={companyId ? String(companyId) : ''} placeholder="Chọn/tìm công ty…"
                  options={companies.map((c) => ({ value: String(c.id), label: c.name }))}
                  onChange={(v) => setCompanyId(Number(v) || 0)} />
              </div>
              <div className="form-row"><label>Loại công nợ</label>
                <select value={sourceType} onChange={(e) => setSourceType(e.target.value)}>
                  <option value="goods">Hàng hóa</option>
                  <option value="shipping">Vận chuyển</option>
                </select>
              </div>
            </>
          )}
          <div className="form-row"><label>Ngày lập</label><DateInput value={requestDate} onChange={setRequestDate} /></div>
          <div className="form-row">
            <label>Hình thức thanh toán</label>
            <select value={paymentMethod} onChange={(e) => setPaymentMethod(e.target.value)}>
              <option value="transfer">Chuyển khoản</option>
              <option value="cash">Tiền mặt</option>
            </select>
            <div style={hintStyle}>{pmHint(paymentMethod)}</div>
          </div>
          <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Ghi chú</label>
            <textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Ghi chú áp dụng cho các phiếu được tạo…" /></div>
        </div>
      </div>

      <div className="card" style={{ padding: 18, marginBottom: 16 }}>
        <h3 className="sec-title">Các khoản công nợ thanh toán ({lines.length})</h3>
        <div className="items-scroll">
          <table className="items-table" style={{ minWidth: 1100 }}>
            <thead><tr><th style={{ width: 36 }}>#</th><th>Nhà cung cấp</th><th>Loại</th><th>PO</th>
              <th>Số hóa đơn</th><th>Ngày hóa đơn</th><th>Hạn trả</th>
              <th style={{ textAlign: 'right' }}>Tổng nợ</th><th style={{ textAlign: 'right' }}>Đã trả</th>
              <th style={{ textAlign: 'right' }}>Đề nghị trả</th>
              <th style={{ width: 50, textAlign: 'center' }}>Bỏ</th></tr></thead>
            <tbody>
              {lines.map((l, i) => (
                <tr key={l.key}>
                  <td>{i + 1}</td>
                  <td>{l.payable_id ? (l.supplier_name || l.supplier_code)
                    : (suppliers.find((s) => s.code === headSupplier)?.name || headPayable?.supplier_name || headSupplier || '—')}</td>
                  <td>{(l.payable_id ? l.source_type : headSource) === 'shipping' ? 'Vận chuyển' : 'Hàng hóa'}</td>
                  <td>{l.payable_id ? l.po_code : (
                    <input className="cell-input" style={{ width: 130 }} value={l.po_code}
                      onChange={(e) => setLine(l.key, { po_code: e.target.value })} placeholder="Mã PO" />)}</td>
                  <td><input className="cell-input" style={{ width: 130 }} value={l.invoice_no}
                    onChange={(e) => setLine(l.key, { invoice_no: e.target.value })} placeholder="(để trống = in tay)" /></td>
                  <td><DateInput value={l.invoice_date} onChange={(v) => setLine(l.key, { invoice_date: v })} /></td>
                  <td>{l.due_date}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(l.payable_total)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(l.payable_paid)}</td>
                  <td style={{ textAlign: 'right' }}>
                    <NumberInput className="cell-input" style={{ width: 140, textAlign: 'right' }}
                      value={l.amount} onChange={(v) => setLine(l.key, { amount: v })} />
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button className="icon-btn" title="Bỏ dòng này khỏi phiếu"
                      onClick={() => setLines((s) => s.filter((x) => x.key !== l.key))}>
                      <i className="ti ti-x" style={{ fontSize: 16, color: 'var(--red)' }} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginTop: 12 }}>
          <button className="btn ghost" onClick={() => setLines((s) => [...s, blankLine()])}><i className="ti ti-plus" />Thêm dòng</button>
          <span style={{ flex: 1 }} />
          <span style={{ fontSize: 16, color: 'var(--navy)' }}>Tổng đề nghị thanh toán: <b>{fmt(total)}</b></span>
        </div>
      </div>
    </div>
  )
}

function PaymentRequestView() {
  const { id } = useParams()
  const { can } = useAuth()
  const navigate = useNavigate()
  const [req, setReq] = useState<any>(null)
  const [companies, setCompanies] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [notFound, setNotFound] = useState(false)

  async function loadAll() {
    try {
      const r = await api.get(`${API}/${id}`); setReq(r.data.data)
      api.get('/api/attachments', { params: { entity: 'payment_request', entity_id: id } }).then((x) => setFiles(x.data.data))
      api.get('/api/audit-logs', { params: { entity: 'payment_request', entity_id: id } }).then((x) => setLogs(x.data.data))
    } catch (ex: any) {
      if (ex?.response?.status === 403 || ex?.response?.status === 404) { setNotFound(true); return }
      throw ex
    }
  }
  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    setNotFound(false); loadAll()
  }, [id])

  if (notFound) return <NotFound backTo="/payment-requests" message="Không tìm thấy yêu cầu thanh toán này hoặc bạn không có quyền truy cập." />
  if (!req) return <div style={{ padding: 40 }}>Đang tải...</div>

  // CR-066: chỉ bản NHÁP mới sửa được. Gửi duyệt / duyệt xong là khóa cứng (backend cũng chặn).
  const editable = req.status === 'draft' && can('payment_request', 'write')
  const companyName = companies.find((c) => c.id === req.company_id)?.name || '—'
  const setLine = (i: number, patch: any) =>
    setReq((s: any) => ({ ...s, lines: s.lines.map((l: any, idx: number) => idx === i ? { ...l, ...patch } : l) }))
  const unmatched = (req.lines || []).filter((l: any) => !l.matched)

  async function save() {
    try {
      await api.patch(`${API}/${id}`, {
        request_date: req.request_date, note: req.note, payment_method: req.payment_method || 'transfer',
        lines: req.lines.map((l: any) => ({
          payable_id: l.payable_id, po_code: l.po_code || '', invoice_no: l.invoice_no || '',
          invoice_date: l.invoice_date || '', amount: Number(l.amount) || 0,
        })),
      })
      toast.success('Đã lưu'); loadAll()
    } catch (ex: any) { toast.error(ex?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }
  async function action(path: string) {
    try { await api.post(`${API}/${id}/${path}`); loadAll() } catch (ex: any) { toast.error(ex?.response?.data?.error?.message || 'Lỗi') }
  }
  async function uploadFiles(fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'payment_request'); fd.append('entity_id', String(id))
    Array.from(fl).forEach((f) => fd.append('files', f))
    await api.post('/api/attachments', fd); loadAll()
  }

  const total = req.lines.reduce((s: number, l: any) => s + (Number(l.amount) || 0), 0)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/payment-requests')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>Yêu cầu thanh toán {req.code}</h2>
        {stBadge(req.status)}
        <span style={{ flex: 1 }} />
        {can('payment_request', 'print') && <button className="btn ghost" onClick={() => window.open(`/print/payment-request/${id}`, '_blank')}><i className="ti ti-printer" />In phiếu</button>}
        {editable && can('payment_request', 'write') && <button className="btn" onClick={save}>Lưu</button>}
        {req.status === 'draft' && can('payment_request', 'write') && <button className="btn secondary" onClick={() => action('submit')}><i className="ti ti-send" />Gửi duyệt</button>}
        {req.status === 'submitted' && can('payment_request', 'approve') && <button className="btn" onClick={() => action('approve')}><i className="ti ti-check" />Duyệt</button>}
        {req.status === 'submitted' && can('payment_request', 'approve') && (
          <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }}
            onClick={async () => { const r = await askPrompt({ title: 'Từ chối phiếu', message: 'Lý do từ chối (khóa phiếu):', confirmText: 'Từ chối' }); if (r !== null) { try { await api.post(`${API}/${id}/reject`, { reason: r }); loadAll() } catch (ex: any) { toast.error(ex?.response?.data?.error?.message || 'Lỗi từ chối') } } }}>
            <i className="ti ti-ban" />Từ chối
          </button>
        )}
        {req.status === 'approved' && can('payment_request', 'write') && <button className="btn" onClick={async () => { if (await askConfirm({ message: 'Xác nhận đã chi tiền? Công nợ sẽ được trừ tương ứng.', confirmText: 'Ghi nhận đã chi', danger: false })) action('pay') }}><i className="ti ti-cash" />Ghi nhận đã chi</button>}
      </div>

      {req.status === 'cancelled' && req.reject_reason && (
        <div className="card" style={{ padding: 14, marginBottom: 16, borderLeft: '4px solid var(--red)' }}>
          <b style={{ color: 'var(--red)' }}>Lý do từ chối:</b> {req.reject_reason}
        </div>
      )}

      <div className="card" style={{ padding: 18, marginBottom: 16 }}>
        <h3 className="sec-title">Thông tin phiếu</h3>
        <div className="form-grid">
          <div className="form-row"><label>Nhà cung cấp</label><input value={req.supplier_name || req.supplier_code} disabled /></div>
          <div className="form-row"><label>Loại công nợ</label><input value={req.source_type === 'shipping' ? 'Vận chuyển' : 'Hàng hóa'} disabled /></div>
          <div className="form-row"><label>Công ty</label><input value={companyName} disabled /></div>
          <div className="form-row"><label>Người yêu cầu</label><input value={req.created_by_name || '—'} disabled /></div>
          <div className="form-row"><label>Ngày lập</label><input value={fmtDateTime(req.created_at) || '—'} disabled /></div>
          <div className="form-row">
            <label>Hình thức thanh toán</label>
            {editable ? (
              <select value={req.payment_method || 'transfer'}
                      onChange={(e) => setReq((s: any) => ({ ...s, payment_method: e.target.value }))}>
                <option value="transfer">Chuyển khoản</option>
                <option value="cash">Tiền mặt</option>
              </select>
            ) : <input value={PM[req.payment_method] || PM.transfer} disabled />}
            <div style={hintStyle}>{pmHint(req.payment_method || 'transfer')}{editable ? ' Nhớ bấm Lưu sau khi đổi.' : ''}</div>
          </div>
          <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Ghi chú</label><textarea value={req.note || ''} disabled={!editable} onChange={(e) => setReq((s: any) => ({ ...s, note: e.target.value }))} /></div>
        </div>
      </div>

      <div className="card" style={{ padding: 18, marginBottom: 16 }}>
        <h3 className="sec-title">Các khoản công nợ thanh toán</h3>
        {editable && unmatched.length > 0 && (
          <div style={{ padding: '10px 12px', marginBottom: 12, borderLeft: '4px solid var(--amber)', background: 'var(--bg-soft, #fff8e6)', fontSize: 13 }}>
            <b>{unmatched.length} dòng chưa khớp khoản công nợ nào.</b> In bản nháp trình ký thì được (ô còn thiếu in trắng để điền tay),
            nhưng <b>gửi duyệt</b> thì mỗi dòng phải có Số hóa đơn đúng với một khoản công nợ còn nợ — nếu không, lúc ghi nhận chi
            tiền sẽ không trừ được vào đâu.
          </div>
        )}
        <div className="items-scroll">
          <table className="items-table" style={{ minWidth: 900 }}>
            <thead><tr><th>#</th><th>PO</th><th>Số hóa đơn</th><th>Ngày hóa đơn</th><th>Hạn trả</th>
              <th style={{ textAlign: 'right' }}>Tổng nợ</th><th style={{ textAlign: 'right' }}>Đã trả</th>
              <th style={{ textAlign: 'right' }}>Đề nghị trả</th>
              {editable && <th style={{ width: 50, textAlign: 'center' }}>Bỏ</th>}</tr></thead>
            <tbody>
              {req.lines.map((l: any, i: number) => (
                <tr key={i}>
                  <td>{i + 1}</td>
                  <td>{editable ? <input className="cell-input" style={{ width: 130 }} value={l.po_code || ''}
                    onChange={(e) => setLine(i, { po_code: e.target.value })} placeholder="Mã PO" /> : l.po_code}</td>
                  <td>{editable ? <input className="cell-input" style={{ width: 130 }} value={l.invoice_no || ''}
                    onChange={(e) => setLine(i, { invoice_no: e.target.value })} placeholder="(để trống = in tay)" /> : l.invoice_no}</td>
                  <td>{editable ? <DateInput value={l.invoice_date || ''} onChange={(v) => setLine(i, { invoice_date: v })} /> : l.invoice_date}</td>
                  <td>{l.due_date}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(l.payable_total)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(l.payable_paid)}</td>
                  <td style={{ textAlign: 'right' }}>
                    {editable ? <NumberInput className="cell-input" style={{ width: 140, textAlign: 'right' }} value={l.amount} onChange={(v) => setLine(i, { amount: v })} /> : fmt(l.amount)}
                  </td>
                  {editable && (
                    <td style={{ textAlign: 'center' }}>
                      <button className="icon-btn" title="Bỏ dòng này khỏi phiếu"
                        onClick={() => setReq((s: any) => ({ ...s, lines: s.lines.filter((_: any, idx: number) => idx !== i) }))}>
                        <i className="ti ti-x" style={{ fontSize: 16, color: 'var(--red)' }} />
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', marginTop: 12 }}>
          {editable && (
            <button className="btn ghost" onClick={() => setReq((s: any) => ({ ...s, lines: [...s.lines, { payable_id: 0, po_code: '', invoice_no: '', invoice_date: '', due_date: '', payable_total: 0, payable_paid: 0, amount: 0 }] }))}>
              <i className="ti ti-plus" />Thêm dòng
            </button>
          )}
          <span style={{ flex: 1 }} />
          <span style={{ fontSize: 16, color: 'var(--navy)' }}>Tổng đề nghị thanh toán: <b>{fmt(total)}</b></span>
        </div>
        {editable && <div style={hintStyle}>Sửa xong nhớ bấm <b>Lưu</b>. Tổng nợ / Đã trả / Hạn trả đọc từ màn Công nợ, không sửa ở đây.</div>}
      </div>

      <DocumentAttachmentSection
        entity="payment_request"
        entityId={Number(id)}
        files={files}
        editable={can('payment_request', 'write')}
        isNew={false}
        title="Chứng từ thanh toán (Ủy nhiệm chi, biên lai…)"
        onRefresh={loadAll}
      />

      {logs.length > 0 && (
        <div className="card" style={{ padding: 18, marginBottom: 16 }}>
          <h3 className="sec-title"><i className="ti ti-history" /> Lịch sử thao tác</h3>
          <AuditTimeline logs={logs} />
        </div>
      )}

      {editable && can('payment_request', 'delete') && (
        <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)', marginTop: 16 }}
                onClick={async () => { if (await askConfirm({ message: 'Xóa phiếu này?' })) { await api.delete(`${API}/${id}`); navigate('/payment-requests') } }}><i className="ti ti-trash" /> Xóa phiếu</button>
      )}
    </div>
  )
}
