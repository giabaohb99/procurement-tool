import { useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { askConfirm, askPrompt } from '../components/confirm'
import { useAuth } from '../auth/AuthContext'
import DateInput from '../components/DateInput'
import NotFound from '../components/NotFound'
import NumberInput from '../components/NumberInput'
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

/** Màn TẠO phiếu: nhận danh sách khoản nợ đã tick qua URL (`?payables=1,2,3`), cho soát/sửa
 *  số tiền đề nghị + bỏ bớt khoản, rồi mới POST. Thoát giữa chừng = không sinh phiếu nháp nào. */
function PaymentRequestCreate() {
  const navigate = useNavigate()
  const location = useLocation()
  const [sp] = useSearchParams()
  const idsParam = sp.get('payables') || ''
  const ids = useMemo(() => idsParam.split(',').map(Number).filter(Boolean), [idsParam])

  const [rows, setRows] = useState<any[]>(() => (location.state as any)?.rows || [])
  const [loading, setLoading] = useState(false)
  const [requestDate, setRequestDate] = useState(new Date().toISOString().slice(0, 10))
  const [paymentMethod, setPaymentMethod] = useState('transfer')
  const [note, setNote] = useState('')
  const [amounts, setAmounts] = useState<Record<number, number>>({})
  const [dropped, setDropped] = useState<number[]>([])
  const [saving, setSaving] = useState(false)

  // Mở lại bằng link/F5 (không còn state điều hướng) → nạp lại đúng các khoản đã tick
  useEffect(() => {
    if (!ids.length || rows.length) return
    setLoading(true)
    api.get('/api/payables', { params: { ids: ids.join(','), year: 'all', page_size: 500 } })
      .then((r) => setRows(r.data.data.items || []))
      .finally(() => setLoading(false))
  }, [idsParam])

  // Số tiền đề nghị mặc định = còn phải trả
  useEffect(() => {
    setAmounts((prev) => {
      const next = { ...prev }
      rows.forEach((r) => { if (next[r.id] === undefined) next[r.id] = Number(r.remaining) || 0 })
      return next
    })
  }, [rows])

  const kept = rows.filter((r) => !dropped.includes(r.id))
  // Server tách mỗi (NCC × loại công nợ) thành 1 phiếu — hiện trước để người dùng biết sẽ ra mấy phiếu
  const groups = useMemo(() => {
    const m = new Map<string, any[]>()
    kept.forEach((r) => {
      const k = `${r.supplier_code}||${r.source_type}`
      m.set(k, [...(m.get(k) || []), r])
    })
    return Array.from(m.values())
  }, [kept, dropped])
  const noInvoice = kept.filter((r) => !String(r.invoice_no || '').trim())
  const total = kept.reduce((s, r) => s + (Number(amounts[r.id]) || 0), 0)

  async function create() {
    if (!kept.length) { toast.error('Chưa chọn khoản công nợ nào'); return }
    setSaving(true)
    try {
      const lines = kept.map((r) => ({ payable_id: r.id, amount: Number(amounts[r.id]) || 0 }))
      const r = await api.post(API, { request_date: requestDate, note, payment_method: paymentMethod, lines })
      const created = r.data.data || []
      toast.success(created.length === 1 ? 'Đã tạo yêu cầu thanh toán'
        : `Đã tạo ${created.length} phiếu yêu cầu thanh toán (mỗi nhà cung cấp 1 phiếu).`)
      if (created.length === 1) navigate(`/payment-requests/${created[0].id}`, { replace: true })
      else navigate('/payment-requests', { replace: true })
    } catch (ex: any) { toast.error(ex?.response?.data?.error?.message || 'Lỗi tạo yêu cầu thanh toán') }
    finally { setSaving(false) }
  }

  if (!ids.length) return (
    <div style={{ padding: 20 }}>
      <h2 className="page-title">Tạo yêu cầu thanh toán</h2>
      <div className="card" style={{ padding: 20 }}>
        Phiếu yêu cầu thanh toán được tạo từ màn <b>Công nợ</b>: chọn các khoản nợ (cùng/khác NCC) rồi bấm
        <i> "Tạo yêu cầu thanh toán"</i> — hệ thống tự tách mỗi nhà cung cấp 1 phiếu.
        <div style={{ marginTop: 14 }}><button className="btn" onClick={() => navigate('/payables')}><i className="ti ti-cash" />Tới màn Công nợ</button></div>
      </div>
    </div>
  )
  if (loading) return <div style={{ padding: 40 }}>Đang tải...</div>

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate(-1)}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>Tạo yêu cầu thanh toán</h2>
        <span className="badge gray">Chưa lưu</span>
        <span style={{ flex: 1 }} />
        <button className="btn" disabled={saving || !kept.length} onClick={create}>
          <i className="ti ti-check" />{saving ? 'Đang tạo…' : `Tạo ${groups.length > 1 ? `${groups.length} phiếu` : 'phiếu'}`}
        </button>
      </div>

      <div className="card" style={{ padding: 14, marginBottom: 16, borderLeft: '4px solid var(--teal)' }}>
        Soát lại số tiền đề nghị rồi bấm <b>Tạo phiếu</b>. Rời màn này mà chưa bấm thì <b>không phiếu nháp nào được sinh ra</b>.
        {groups.length > 1 && <> Hệ thống sẽ tách thành <b>{groups.length} phiếu</b> (mỗi nhà cung cấp / loại công nợ 1 phiếu).</>}
      </div>

      {noInvoice.length > 0 && (
        <div className="card" style={{ padding: 14, marginBottom: 16, borderLeft: '4px solid var(--red)' }}>
          <b style={{ color: 'var(--red)' }}>{noInvoice.length} khoản chưa có Số hóa đơn</b> — bỏ các khoản này ra thì mới tạo được phiếu:
          {' '}{noInvoice.map((r) => r.po_code || `#${r.id}`).join(', ')}
        </div>
      )}

      <div className="card" style={{ padding: 18, marginBottom: 16 }}>
        <h3 className="sec-title">Thông tin phiếu</h3>
        <div className="form-grid">
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
        <h3 className="sec-title">Các khoản công nợ sẽ thanh toán ({kept.length})</h3>
        <div className="items-scroll">
          <table className="items-table" style={{ minWidth: 1000 }}>
            <thead><tr><th style={{ width: 36 }}>#</th><th>Nhà cung cấp</th><th>Loại</th><th>PO</th><th>Số HĐ</th><th>Hạn trả</th>
              <th style={{ textAlign: 'right' }}>Tổng nợ</th><th style={{ textAlign: 'right' }}>Đã trả</th>
              <th style={{ textAlign: 'right' }}>Còn lại</th><th style={{ textAlign: 'right' }}>Đề nghị trả</th>
              <th style={{ width: 50, textAlign: 'center' }}>Bỏ</th></tr></thead>
            <tbody>
              {kept.map((r, i) => (
                <tr key={r.id}>
                  <td>{i + 1}</td>
                  <td>{r.supplier_name || r.supplier_code}</td>
                  <td>{r.source_type === 'shipping' ? 'Vận chuyển' : 'Hàng hóa'}</td>
                  <td>{r.po_code}</td>
                  <td>{r.invoice_no || <span style={{ color: 'var(--red)', fontSize: 12 }}>chưa có HĐ</span>}</td>
                  <td>{r.due_date}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(r.total)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(r.paid_amount)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(r.remaining)}</td>
                  <td style={{ textAlign: 'right' }}>
                    <NumberInput className="cell-input" style={{ width: 140, textAlign: 'right' }}
                      value={amounts[r.id] ?? 0} onChange={(v) => setAmounts((s) => ({ ...s, [r.id]: v }))} />
                  </td>
                  <td style={{ textAlign: 'center' }}>
                    <button className="icon-btn" title="Bỏ khoản này khỏi phiếu" onClick={() => setDropped((s) => [...s, r.id])}>
                      <i className="ti ti-x" style={{ fontSize: 16, color: 'var(--red)' }} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ textAlign: 'right', fontSize: 16, color: 'var(--navy)', marginTop: 12 }}>Tổng đề nghị thanh toán: <b>{fmt(total)}</b></div>
        {dropped.length > 0 && (
          <div style={{ marginTop: 10 }}>
            <button className="btn ghost" onClick={() => setDropped([])}><i className="ti ti-arrow-back-up" />Khôi phục {dropped.length} khoản đã bỏ</button>
          </div>
        )}
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

  const editable = req.status === 'draft' && can('payment_request', 'write')
  const companyName = companies.find((c) => c.id === req.company_id)?.name || '—'
  const setLineAmount = (i: number, v: number) =>
    setReq((s: any) => ({ ...s, lines: s.lines.map((l: any, idx: number) => idx === i ? { ...l, amount: v } : l) }))

  async function save() {
    try {
      await api.patch(`${API}/${id}`, { request_date: req.request_date, note: req.note, payment_method: req.payment_method || 'transfer', lines: req.lines.map((l: any) => ({ payable_id: l.payable_id, amount: Number(l.amount) || 0 })) })
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
        <div className="items-scroll">
          <table className="items-table" style={{ minWidth: 800 }}>
            <thead><tr><th>#</th><th>PO</th><th>Số HĐ</th><th>Ngày PS</th><th>Hạn trả</th><th style={{ textAlign: 'right' }}>Tổng nợ</th><th style={{ textAlign: 'right' }}>Đã trả</th><th style={{ textAlign: 'right' }}>Đề nghị trả</th></tr></thead>
            <tbody>
              {req.lines.map((l: any, i: number) => (
                <tr key={i}>
                  <td>{i + 1}</td><td>{l.po_code}</td><td>{l.invoice_no}</td><td>{l.incur_date}</td><td>{l.due_date}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(l.payable_total)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(l.payable_paid)}</td>
                  <td style={{ textAlign: 'right' }}>
                    {editable ? <NumberInput className="cell-input" style={{ width: 140, textAlign: 'right' }} value={l.amount} onChange={(v) => setLineAmount(i, v)} /> : fmt(l.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ textAlign: 'right', fontSize: 16, color: 'var(--navy)', marginTop: 12 }}>Tổng đề nghị thanh toán: <b>{fmt(total)}</b></div>
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
