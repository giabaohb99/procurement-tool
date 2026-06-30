import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { poBadge } from '../config/cruds'

const API = '/api/purchase-orders'
const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const QC = ['', 'Đạt', 'Thiếu', 'Lỗi']

const emptyItem = {
  product_code: '', product_name: '', item_group: '', spec: '', unit: '',
  qty_request: 0, qty_order: 0, price: 0, vat: 8, warehouse_code: '', note: '', deliveries: [],
}
const emptyDelivery = {
  delivery_no: 1, warehouse_code: '', carrier_code: '', carrier_name: '', ship_qty: 0, ship_unit: '',
  received_qty: 0, promised_date: '', expected_date: '', received_date: '', invoice_no: '',
  shipping_unit_price: 0, shipping_amount: 0, qc_result: '', progress_note: '',
}

export default function PurchaseOrderDetail() {
  const { id } = useParams()
  const isNew = id === 'new'
  const { can } = useAuth()
  const navigate = useNavigate()

  const [po, setPo] = useState<any>({
    code: '', misa_code: '', pr_code: '', survey_code: '', company_id: 0, supplier_code: '',
    supplier_name: '', department: '', nspt: '', order_date: new Date().toISOString().slice(0, 10),
    vat_rate: 0.08, is_urgent: false, note: '', status: 'draft', items: [],
  })
  const [companies, setCompanies] = useState<any[]>([])
  const [suppliers, setSuppliers] = useState<any[]>([])
  const [products, setProducts] = useState<any[]>([])
  const [units, setUnits] = useState<string[]>([])
  const [warehouses, setWarehouses] = useState<any[]>([])
  const [prList, setPrList] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [attByDelivery, setAttByDelivery] = useState<Record<number, any[]>>({})
  const [editingItemIdx, setEditingItemIdx] = useState<number | null>(null)
  const [err, setErr] = useState(''); const [msg, setMsg] = useState('')

  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    api.get('/api/suppliers', { params: { page_size: 1000 } }).then((r) => setSuppliers(r.data.data.items))
    api.get('/api/products', { params: { page_size: 2000 } }).then((r) => setProducts(r.data.data.items))
    api.get('/api/units', { params: { page_size: 300 } }).then((r) => setUnits(r.data.data.items.map((x: any) => x.name)))
    api.get('/api/warehouses', { params: { page_size: 300 } }).then((r) => setWarehouses(r.data.data.items))
    api.get('/api/purchase-requests', { params: { page_size: 1000 } }).then((r) => setPrList(r.data.data.items))
  }, [])

  async function loadAll() {
    const r = await api.get(`${API}/${id}`); setPo(r.data.data)
    api.get('/api/audit-logs', { params: { entity: 'purchase_order', entity_id: id } }).then((x) => setLogs(x.data.data))
    api.get('/api/attachments', { params: { entity: 'purchase_order', entity_id: id } }).then((x) => setFiles(x.data.data))
  }
  useEffect(() => { if (!isNew) loadAll() }, [id])

  const goodsSuppliers = suppliers.filter((s) => s.supplier_type !== 'transport')
  const carriers = suppliers.filter((s) => s.supplier_type === 'transport')

  const headerEditable = isNew || po.status === 'draft' || po.status === 'rejected'
  const deliveryEditable = !isNew && ['approved', 'partial', 'received'].includes(po.status)

  const setH = (k: string, v: any) => setPo((s: any) => ({ ...s, [k]: v }))
  const items = po.items || []
  const setItem = (i: number, patch: any) =>
    setPo((s: any) => ({ ...s, items: s.items.map((it: any, idx: number) => idx === i ? { ...it, ...patch } : it) }))
  const addItems = (n = 1) => setPo((s: any) => ({ ...s, items: [...(s.items || []), ...Array.from({ length: n }, () => ({ ...emptyItem }))] }))
  const delItem = (i: number) => setPo((s: any) => ({ ...s, items: s.items.filter((_: any, idx: number) => idx !== i) }))

  const rowAmount = (it: any) => (Number(it.qty_order) || 0) * (Number(it.price) || 0) * (1 + (Number(it.vat) || 0) / 100)
  const subtotal = items.reduce((s: number, it: any) => s + (Number(it.qty_order) || 0) * (Number(it.price) || 0), 0)
  const vat = items.reduce((s: number, it: any) => s + rowAmount(it), 0) - subtotal
  const shippingTotal = items.reduce((s: number, it: any) => s + (it.deliveries || []).reduce((a: number, d: any) => a + (Number(d.shipping_amount) || 0), 0), 0)

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
        ...it, deliveries: [...(it.deliveries || []), { ...emptyDelivery, delivery_no: (it.deliveries?.length || 0) + 1, warehouse_code: it.warehouse_code, ship_unit: it.unit }],
      }),
    }))
  const delDelivery = (ii: number, di: number) =>
    setPo((s: any) => ({
      ...s, items: s.items.map((it: any, idx: number) => idx !== ii ? it : {
        ...it, deliveries: it.deliveries.filter((_: any, j: number) => j !== di),
      }),
    }))

  const onPickProduct = (i: number, code: string) => {
    const p = products.find((x) => x.code === code)
    setItem(i, p ? { product_code: p.code, product_name: p.name, unit: p.unit || '', item_group: p.item_group || '' } : { product_code: code })
  }
  const onPickSupplier = (code: string) => {
    const s = goodsSuppliers.find((x) => x.code === code)
    setPo((st: any) => ({ ...st, supplier_code: code, supplier_name: s ? s.name : '', vat_rate: s ? (Number(s.vat) || st.vat_rate) : st.vat_rate }))
  }
  const onPickCarrier = (ii: number, di: number, code: string) => {
    const c = carriers.find((x) => x.code === code)
    setDelivery(ii, di, { carrier_code: code, carrier_name: c ? c.name : (code ? 'NCC tự vận chuyển' : '') })
  }
  const onPickPr = (code: string) => {
    const pr = prList.find((p) => p.code === code)
    setPo((s: any) => ({ ...s, pr_code: code, ...(pr ? { department: pr.department || s.department, nspt: pr.requester || s.nspt, company_id: pr.company_id || s.company_id } : {}) }))
  }

  async function save() {
    setErr(''); setMsg('')
    const body: any = {
      misa_code: po.misa_code, pr_code: po.pr_code, survey_code: po.survey_code,
      company_id: Number(po.company_id) || 0, supplier_code: po.supplier_code, supplier_name: po.supplier_name,
      department: po.department, nspt: po.nspt, order_date: po.order_date,
      vat_rate: Number(po.vat_rate) || 0, is_urgent: po.is_urgent, note: po.note,
      items: items.filter((it: any) => it.product_name || it.product_code).map((it: any) => ({
        id: it.id, product_code: it.product_code, product_name: it.product_name, item_group: it.item_group,
        spec: it.spec, unit: it.unit, qty_request: Number(it.qty_request) || 0, qty_order: Number(it.qty_order) || 0,
        price: Number(it.price) || 0, vat: Number(it.vat) || 0, warehouse_code: it.warehouse_code, note: it.note,
        deliveries: (it.deliveries || []).map((d: any) => ({
          id: d.id, delivery_no: Number(d.delivery_no) || 1, warehouse_code: d.warehouse_code,
          carrier_code: d.carrier_code, carrier_name: d.carrier_name, ship_qty: Number(d.ship_qty) || 0,
          ship_unit: d.ship_unit, received_qty: Number(d.received_qty) || 0, promised_date: d.promised_date,
          expected_date: d.expected_date, received_date: d.received_date, invoice_no: d.invoice_no,
          shipping_unit_price: Number(d.shipping_unit_price) || 0, shipping_amount: Number(d.shipping_amount) || 0,
          qc_result: d.qc_result, progress_note: d.progress_note,
        })),
      })),
    }
    try {
      if (isNew) { const r = await api.post(API, body); navigate(`/purchase-orders/${r.data.data.id}`) }
      else { await api.patch(`${API}/${id}`, body); setMsg('Đã lưu thành công'); loadAll() }
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }

  async function action(path: string, payload: any = {}) {
    setErr('')
    try { await api.post(`${API}/${id}/${path}`, payload); loadAll() }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi') }
  }

  async function uploadFiles(fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'purchase_order'); fd.append('entity_id', String(id))
    Array.from(fl).forEach((f) => fd.append('files', f))
    try { await api.post('/api/attachments', fd); loadAll() } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi tải file') }
  }

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

  function openDeliveries(i: number) {
    setEditingItemIdx(i)
    ;(items[i].deliveries || []).forEach((d: any) => { if (d.id) loadDeliveryAtt(d.id) })
  }

  // inline cell helpers for item table
  const txt = (i: number, k: string, w: number | string = 120) => (
    <input className="cell-input" style={{ width: w }} value={items[i][k] ?? ''} disabled={!headerEditable} onChange={(e) => setItem(i, { [k]: e.target.value })} />
  )
  const num = (i: number, k: string, w = 90) => (
    <input className="cell-input" type="number" style={{ width: w }} value={items[i][k] ?? 0} disabled={!headerEditable} onChange={(e) => setItem(i, { [k]: Number(e.target.value) })} />
  )

  const title = isNew ? 'Tạo Đơn mua hàng' : `Đơn mua hàng ${po.code || ''}`
  const isLogShown = !isNew && logs.length > 0

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/purchase-orders')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>{title}</h2>
        {!isNew && poBadge(po.status)}
        <span style={{ flex: 1 }} />
        {!isNew && can('purchase_order', 'print') && (
          <button className="btn ghost" onClick={() => window.open(`/print/purchase-order/${id}`, '_blank')}><i className="ti ti-printer" />In PO gửi NCC</button>
        )}
        {(headerEditable || deliveryEditable) && can('purchase_order', isNew ? 'create' : 'write') && (
          <button className="btn" onClick={save}>{isNew ? 'Tạo' : 'Lưu'}</button>
        )}
        {!isNew && po.status === 'draft' && can('purchase_order', 'write') && (
          <button className="btn secondary" onClick={() => action('submit')}><i className="ti ti-send" />Gửi duyệt</button>
        )}
        {!isNew && po.status === 'submitted' && can('purchase_order', 'approve') && (
          <>
            <button className="btn" onClick={() => action('approve')}><i className="ti ti-check" />Duyệt</button>
            <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={() => action('reject', { reason: prompt('Lý do từ chối:') || '' })}><i className="ti ti-x" />Từ chối</button>
          </>
        )}
      </div>

      <div className={isLogShown ? 'detail-grid' : ''}>
        <div>
          {/* Thông tin chung */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title">Thông tin chung</h3>
            <div className="form-grid">
              <div className="form-row"><label>Mã PO</label><input value={po.code || ''} disabled placeholder="Tự sinh khi tạo" /></div>
              <div className="form-row"><label>Mã PYC nguồn</label>
                <input list="po-pyc-list" placeholder="Nhập/chọn mã PYC…" value={po.pr_code || ''} disabled={!headerEditable} onChange={(e) => onPickPr(e.target.value)} />
                <datalist id="po-pyc-list">{prList.map((p) => <option key={p.id} value={p.code}>{p.purpose || ''}</option>)}</datalist>
              </div>
              <div className="form-row"><label>Mã đơn MISA</label><input value={po.misa_code || ''} disabled={!headerEditable} onChange={(e) => setH('misa_code', e.target.value)} /></div>
              <div className="form-row"><label>Công ty nhận HĐ *</label>
                <select value={po.company_id || ''} disabled={!headerEditable} onChange={(e) => setH('company_id', Number(e.target.value))}>
                  <option value="">-- Chọn --</option>{companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div className="form-row"><label>Nhà cung cấp bán hàng *</label>
                <select value={po.supplier_code || ''} disabled={!headerEditable} onChange={(e) => onPickSupplier(e.target.value)}>
                  <option value="">-- Chọn NCC --</option>{goodsSuppliers.map((s) => <option key={s.id} value={s.code}>{s.code} — {s.name}</option>)}
                </select>
              </div>
              <div className="form-row"><label>Ngày đặt hàng</label><input type="date" value={po.order_date || ''} disabled={!headerEditable} onChange={(e) => setH('order_date', e.target.value)} /></div>
              <div className="form-row"><label>Bộ phận</label><input value={po.department || ''} disabled={!headerEditable} onChange={(e) => setH('department', e.target.value)} /></div>
              <div className="form-row"><label>NSPT phụ trách</label><input value={po.nspt || ''} disabled={!headerEditable} onChange={(e) => setH('nspt', e.target.value)} /></div>
              <div className="form-row"><label>VAT (%)</label><input type="number" value={Math.round((Number(po.vat_rate) || 0) * 100)} disabled={!headerEditable} onChange={(e) => setH('vat_rate', Number(e.target.value) / 100)} /></div>
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
                  <button className="btn ghost" onClick={() => addItems(Math.max(1, parseInt(prompt('Thêm bao nhiêu dòng?', '3') || '0') || 0))} style={{ height: 32, fontSize: 13 }}><i className="ti ti-rows" />Thêm nhiều</button>
                </div>
              )}
            </div>
            <div className="items-scroll">
              <table className="items-table" style={{ minWidth: 1300 }}>
                <thead>
                  <tr>
                    <th style={{ width: 36 }}>#</th>
                    <th style={{ width: 130 }}>Mã hàng</th>
                    <th style={{ minWidth: 200 }}>Tên hàng *</th>
                    <th style={{ width: 130 }}>Phân loại</th>
                    <th style={{ width: 150 }}>Xuất xứ/TSKT</th>
                    <th style={{ width: 90 }}>ĐVT</th>
                    <th style={{ width: 90 }}>SL YC</th>
                    <th style={{ width: 100 }}>SL đặt</th>
                    <th style={{ width: 110 }}>Đơn giá</th>
                    <th style={{ width: 80 }}>VAT%</th>
                    <th style={{ width: 130 }}>Thành tiền</th>
                    <th style={{ width: 120 }}>Tiến độ giao</th>
                    <th style={{ width: 150, textAlign: 'center' }}>Giao hàng</th>
                    {headerEditable && <th style={{ width: 44 }} />}
                  </tr>
                </thead>
                <tbody>
                  {items.map((it: any, i: number) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td>
                        <select className="cell-input" style={{ width: 120 }} value={it.product_code || ''} disabled={!headerEditable} onChange={(e) => onPickProduct(i, e.target.value)}>
                          <option value="">-- Chọn --</option>{products.map((p) => <option key={p.id} value={p.code}>{p.code}</option>)}
                        </select>
                      </td>
                      <td>{txt(i, 'product_name', '100%')}</td>
                      <td>{txt(i, 'item_group', 120)}</td>
                      <td>{txt(i, 'spec', 140)}</td>
                      <td>
                        <select className="cell-input" style={{ width: 80 }} value={it.unit ?? ''} disabled={!headerEditable} onChange={(e) => setItem(i, { unit: e.target.value })}>
                          <option value="">—</option>{units.map((u) => <option key={u} value={u}>{u}</option>)}
                        </select>
                      </td>
                      <td>{num(i, 'qty_request', 80)}</td>
                      <td>{num(i, 'qty_order', 90)}</td>
                      <td>{num(i, 'price', 100)}</td>
                      <td>{num(i, 'vat', 70)}</td>
                      <td style={{ textAlign: 'right', fontWeight: 500 }}>{fmt(rowAmount(it))}</td>
                      <td style={{ textAlign: 'center', fontSize: 13 }}>
                        {fmt(it.qty_received || 0)}/{fmt(it.qty_order || 0)}
                        {it.line_status && <div style={{ fontSize: 11, color: 'var(--muted)' }}>{it.line_status}</div>}
                      </td>
                      <td style={{ textAlign: 'center' }}>
                        <button className="btn ghost" style={{ height: 30, fontSize: 12 }} disabled={isNew} title={isNew ? 'Lưu PO trước' : ''}
                                onClick={() => openDeliveries(i)}>
                          <i className="ti ti-truck-delivery" /> {(it.deliveries?.length || 0)} lần
                        </button>
                      </td>
                      {headerEditable && (
                        <td style={{ textAlign: 'center' }}>
                          <button className="icon-btn" onClick={() => delItem(i)}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>
                        </td>
                      )}
                    </tr>
                  ))}
                  {items.length === 0 && <tr><td colSpan={headerEditable ? 14 : 13} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Chưa có dòng nào</td></tr>}
                </tbody>
              </table>
            </div>
            <div style={{ marginTop: 14, textAlign: 'right', fontSize: 14 }}>
              <div>Tiền hàng: <b>{fmt(subtotal)}</b></div>
              <div>VAT: <b>{fmt(vat)}</b></div>
              <div style={{ fontSize: 16, color: 'var(--navy)', marginTop: 4 }}>Tổng tiền hàng: <b>{fmt(subtotal + vat)}</b></div>
              <div style={{ marginTop: 4, color: 'var(--muted)' }}>Tổng cước vận chuyển (riêng): <b>{fmt(shippingTotal)}</b></div>
            </div>
          </div>

          {/* Chứng từ chung */}
          {!isNew && (
            <div className="card" style={{ padding: 18, marginBottom: 16 }}>
              <h3 className="sec-title"><i className="ti ti-paperclip" /> Chứng từ đính kèm (báo giá, HĐ…)</h3>
              <input type="file" multiple onChange={(e) => uploadFiles(e.target.files)} />
              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {files.map((f) => (
                  <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                    <i className="ti ti-file" /><a href={f.url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{f.filename}</a>
                    <button className="icon-btn" onClick={async () => { if (confirm('Xóa file?')) { await api.delete(`/api/attachments/${f.id}`); loadAll() } }}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>
                  </div>
                ))}
                {files.length === 0 && <span style={{ color: '#999', fontSize: 13 }}>Chưa có file nào.</span>}
              </div>
            </div>
          )}

          {po.approve_note && <div className="card" style={{ padding: 14, marginBottom: 16 }}><b>Ghi chú duyệt:</b> {po.approve_note}</div>}
          {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
          {msg && <div style={{ color: 'var(--green)', fontSize: 13, marginTop: 8 }}>{msg}</div>}

          {!isNew && headerEditable && can('purchase_order', 'delete') && (
            <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)', marginTop: 20 }}
                    onClick={async () => { if (confirm('Xóa đơn mua hàng này?')) { await api.delete(`${API}/${id}`); navigate('/purchase-orders') } }}><i className="ti ti-trash" /> Xóa đơn</button>
          )}
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

      {/* Popup giao hàng nhiều lần của 1 dòng */}
      {editingItemIdx !== null && items[editingItemIdx] && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }} onClick={() => setEditingItemIdx(null)}>
          <div style={{ width: 1100, maxWidth: '100%', background: '#fff', borderRadius: 12, boxShadow: '0 20px 25px -5px rgba(0,0,0,.15)', display: 'flex', flexDirection: 'column', maxHeight: '88vh', overflow: 'hidden' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: 16, color: 'var(--navy)' }}>Giao hàng: {items[editingItemIdx].product_name || items[editingItemIdx].product_code}</h3>
                <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2 }}>
                  SL đặt {fmt(items[editingItemIdx].qty_order)} · Đã nhận {fmt(items[editingItemIdx].qty_received || 0)} · Còn lại {fmt((Number(items[editingItemIdx].qty_order) || 0) - (Number(items[editingItemIdx].qty_received) || 0))}
                </div>
              </div>
              <button className="icon-btn" onClick={() => setEditingItemIdx(null)}><i className="ti ti-x" style={{ fontSize: 18 }} /></button>
            </div>

            <div style={{ padding: 16, overflowY: 'auto', flex: 1 }}>
              {!deliveryEditable && <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 10 }}>⚠️ Chỉ thêm/sửa lần giao khi đơn đã được duyệt.</div>}
              {deliveryEditable && (
                <button className="btn ghost" style={{ height: 30, fontSize: 13, marginBottom: 10 }} onClick={() => addDelivery(editingItemIdx)}><i className="ti ti-plus" />Thêm lần giao</button>
              )}
              <div className="items-scroll">
                <table className="items-table" style={{ minWidth: 1400 }}>
                  <thead>
                    <tr>
                      <th style={{ width: 50 }}>Lần</th>
                      <th style={{ width: 130 }}>Kho nhận</th>
                      <th style={{ width: 160 }}>Đơn vị vận chuyển</th>
                      <th style={{ width: 90 }}>SL gửi</th>
                      <th style={{ width: 90 }}>SL nhận</th>
                      <th style={{ width: 110 }}>Cam kết</th>
                      <th style={{ width: 110 }}>Ngày nhận</th>
                      <th style={{ width: 110 }}>Số HĐ</th>
                      <th style={{ width: 110 }}>Đơn giá VC</th>
                      <th style={{ width: 120 }}>Thành tiền VC</th>
                      <th style={{ width: 100 }}>QC</th>
                      <th style={{ width: 150 }}>Phiếu giao</th>
                      {deliveryEditable && <th style={{ width: 40 }} />}
                    </tr>
                  </thead>
                  <tbody>
                    {(items[editingItemIdx].deliveries || []).map((d: any, di: number) => {
                      const ii = editingItemIdx
                      const dis = !deliveryEditable
                      return (
                        <tr key={di}>
                          <td><input className="cell-input" type="number" style={{ width: 44 }} value={d.delivery_no ?? 1} disabled={dis} onChange={(e) => setDelivery(ii, di, { delivery_no: Number(e.target.value) })} /></td>
                          <td>
                            <select className="cell-input" style={{ width: 120 }} value={d.warehouse_code ?? ''} disabled={dis} onChange={(e) => setDelivery(ii, di, { warehouse_code: e.target.value })}>
                              <option value="">—</option>{warehouses.map((w) => <option key={w.id} value={w.code}>{w.code} — {w.name}</option>)}
                            </select>
                          </td>
                          <td>
                            <select className="cell-input" style={{ width: 150 }} value={d.carrier_code ?? ''} disabled={dis} onChange={(e) => onPickCarrier(ii, di, e.target.value)}>
                              <option value="">NCC tự vận chuyển</option>{carriers.map((c) => <option key={c.id} value={c.code}>{c.name}</option>)}
                            </select>
                          </td>
                          <td><input className="cell-input" type="number" style={{ width: 80 }} value={d.ship_qty ?? 0} disabled={dis} onChange={(e) => setDelivery(ii, di, { ship_qty: Number(e.target.value) })} /></td>
                          <td><input className="cell-input" type="number" style={{ width: 80 }} value={d.received_qty ?? 0} disabled={dis} onChange={(e) => setDelivery(ii, di, { received_qty: Number(e.target.value) })} /></td>
                          <td><input className="cell-input" type="date" style={{ width: 100 }} value={d.promised_date ?? ''} disabled={dis} onChange={(e) => setDelivery(ii, di, { promised_date: e.target.value })} /></td>
                          <td><input className="cell-input" type="date" style={{ width: 100 }} value={d.received_date ?? ''} disabled={dis} onChange={(e) => setDelivery(ii, di, { received_date: e.target.value })} /></td>
                          <td><input className="cell-input" style={{ width: 100 }} value={d.invoice_no ?? ''} disabled={dis} onChange={(e) => setDelivery(ii, di, { invoice_no: e.target.value })} /></td>
                          <td><input className="cell-input" type="number" style={{ width: 100 }} value={d.shipping_unit_price ?? 0} disabled={dis} onChange={(e) => { const up = Number(e.target.value); setDelivery(ii, di, { shipping_unit_price: up, shipping_amount: up * (Number(d.ship_qty) || 0) }) }} /></td>
                          <td><input className="cell-input" type="number" style={{ width: 110 }} value={d.shipping_amount ?? 0} disabled={dis} onChange={(e) => setDelivery(ii, di, { shipping_amount: Number(e.target.value) })} /></td>
                          <td>
                            <select className="cell-input" style={{ width: 90 }} value={d.qc_result ?? ''} disabled={dis} onChange={(e) => setDelivery(ii, di, { qc_result: e.target.value })}>
                              {QC.map((q) => <option key={q} value={q}>{q || '—'}</option>)}
                            </select>
                          </td>
                          <td style={{ fontSize: 12 }}>
                            {d.id ? (
                              <div>
                                <input type="file" id={`datt-${d.id}`} style={{ display: 'none' }} onChange={(e) => uploadDeliveryAtt(d.id, e.target.files)} />
                                <label htmlFor={`datt-${d.id}`} className="btn ghost" style={{ cursor: 'pointer', height: 26, fontSize: 11, padding: '0 8px' }}><i className="ti ti-upload" /> Tải</label>
                                {(attByDelivery[d.id] || []).map((f) => (
                                  <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 3 }}>
                                    <a href={f.url} target="_blank" style={{ color: 'var(--teal)', textDecoration: 'underline', maxWidth: 90, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.filename}</a>
                                    <button className="icon-btn" onClick={async () => { await api.delete(`/api/attachments/${f.id}`); loadDeliveryAtt(d.id) }}><i className="ti ti-x" style={{ color: 'var(--red)', fontSize: 13 }} /></button>
                                  </div>
                                ))}
                              </div>
                            ) : <span style={{ color: '#999' }}>Lưu để đính kèm</span>}
                          </td>
                          {deliveryEditable && (
                            <td style={{ textAlign: 'center' }}><button className="icon-btn" onClick={() => delDelivery(ii, di)}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button></td>
                          )}
                        </tr>
                      )
                    })}
                    {(items[editingItemIdx].deliveries || []).length === 0 && <tr><td colSpan={13} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Chưa có lần giao nào</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button className="btn ghost" style={{ height: 36, fontSize: 13 }} onClick={() => setEditingItemIdx(null)}>Đóng</button>
              {(headerEditable || deliveryEditable) && <button className="btn" style={{ height: 36, fontSize: 13 }} onClick={() => { setEditingItemIdx(null); save() }}>Lưu & cập nhật tồn/công nợ</button>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
