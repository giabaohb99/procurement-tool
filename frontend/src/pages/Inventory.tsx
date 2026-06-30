import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')

export default function Inventory() {
  const { can } = useAuth()
  const [rows, setRows] = useState<any[]>([])
  const [companies, setCompanies] = useState<any[]>([])
  const [warehouses, setWarehouses] = useState<any[]>([])
  const [products, setProducts] = useState<any[]>([])
  const [f, setF] = useState<{ company_id?: string; warehouse_code?: string; product_code?: string }>({})
  const [showAdjust, setShowAdjust] = useState(false)
  const [adj, setAdj] = useState<any>({ company_id: 0, warehouse_code: '', product_code: '', product_name: '', unit: '', qty: 0, note: '' })
  const [msg, setMsg] = useState(''); const [err, setErr] = useState('')

  const companyName = (cid: number) => companies.find((c) => c.id === cid)?.name || cid || '—'

  async function load() {
    const params: any = { page_size: 500 }
    if (f.company_id) params.company_id = f.company_id
    if (f.warehouse_code) params.warehouse_code = f.warehouse_code
    if (f.product_code) params.product_code = f.product_code
    const r = await api.get('/api/inventory', { params })
    setRows(r.data.data.items)
  }
  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    api.get('/api/warehouses', { params: { page_size: 300 } }).then((r) => setWarehouses(r.data.data.items))
    api.get('/api/products', { params: { page_size: 2000 } }).then((r) => setProducts(r.data.data.items))
    load()
  }, [])

  async function submitAdjust() {
    setErr('')
    try {
      await api.post('/api/inventory/adjust', { ...adj, company_id: Number(adj.company_id) || 0, qty: Number(adj.qty) || 0 })
      setShowAdjust(false); setMsg('Đã điều chỉnh tồn kho'); load()
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi điều chỉnh') }
  }

  const onAdjProduct = (code: string) => {
    const p = products.find((x) => x.code === code)
    setAdj((s: any) => ({ ...s, product_code: code, product_name: p ? p.name : s.product_name, unit: p ? p.unit : s.unit }))
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Tồn kho</h2>
        {can('inventory', 'write') && <button className="btn" onClick={() => setShowAdjust(true)}><i className="ti ti-adjustments" />Điều chỉnh tồn</button>}
      </div>

      <div className="card filters" style={{ padding: 14, marginBottom: 12, display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Công ty</label><br />
          <select value={f.company_id || ''} onChange={(e) => setF((s) => ({ ...s, company_id: e.target.value }))}>
            <option value="">Tất cả</option>{companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Kho</label><br />
          <select value={f.warehouse_code || ''} onChange={(e) => setF((s) => ({ ...s, warehouse_code: e.target.value }))}>
            <option value="">Tất cả</option>{warehouses.map((w) => <option key={w.id} value={w.code}>{w.code} — {w.name}</option>)}
          </select>
        </div>
        <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Mã SP</label><br />
          <input value={f.product_code || ''} onChange={(e) => setF((s) => ({ ...s, product_code: e.target.value }))} placeholder="Mã sản phẩm" />
        </div>
        <button className="btn" onClick={load}>Lọc</button>
      </div>

      {msg && <div style={{ color: 'var(--green)', fontSize: 13, marginBottom: 8 }}>{msg}</div>}
      <div className="card">
        <table>
          <thead><tr><th>Công ty</th><th>Kho</th><th>Mã SP</th><th>Tên sản phẩm</th><th>ĐVT</th><th style={{ textAlign: 'right' }}>Tồn hiện tại</th><th style={{ textAlign: 'right' }}>Đơn giá BQ</th><th style={{ textAlign: 'right' }}>Giá trị tồn</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}>
                <td>{companyName(r.company_id)}</td><td>{r.warehouse_code}</td><td>{r.product_code}</td>
                <td>{r.product_name}</td><td>{r.unit}</td>
                <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(r.qty)}</td>
                <td style={{ textAlign: 'right' }}>{fmt(r.avg_cost)}</td>
                <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(r.value)}</td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={8} style={{ textAlign: 'center', color: '#999', padding: 20 }}>Chưa có tồn kho</td></tr>}
          </tbody>
        </table>
      </div>

      {showAdjust && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }} onClick={() => setShowAdjust(false)}>
          <div className="modal-card" style={{ width: 440, maxWidth: '100%', background: '#fff', borderRadius: 12, padding: 20 }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginTop: 0, color: 'var(--navy)' }}>Điều chỉnh tồn kho</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>Công ty</label>
                <select style={{ width: '100%' }} value={adj.company_id || ''} onChange={(e) => setAdj((s: any) => ({ ...s, company_id: Number(e.target.value) }))}>
                  <option value="">-- Chọn --</option>{companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: 13, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>Kho</label>
                <select style={{ width: '100%' }} value={adj.warehouse_code || ''} onChange={(e) => setAdj((s: any) => ({ ...s, warehouse_code: e.target.value }))}>
                  <option value="">-- Chọn --</option>{warehouses.map((w) => <option key={w.id} value={w.code}>{w.code} — {w.name}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: 13, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>Sản phẩm</label>
                <select style={{ width: '100%' }} value={adj.product_code || ''} onChange={(e) => onAdjProduct(e.target.value)}>
                  <option value="">-- Chọn --</option>{products.map((p) => <option key={p.id} value={p.code}>{p.code} — {p.name}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: 13, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>Số lượng điều chỉnh (+/−)</label>
                <input style={{ width: '100%' }} type="number" value={adj.qty} onChange={(e) => setAdj((s: any) => ({ ...s, qty: e.target.value }))} />
              </div>
              <div>
                <label style={{ fontSize: 13, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>Lý do</label>
                <input style={{ width: '100%' }} value={adj.note} onChange={(e) => setAdj((s: any) => ({ ...s, note: e.target.value }))} />
              </div>
            </div>
            {err && <div className="err" style={{ marginTop: 8 }}>{err}</div>}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 14 }}>
              <button className="btn ghost" onClick={() => setShowAdjust(false)}>Hủy</button>
              <button className="btn" onClick={submitAdjust}>Lưu điều chỉnh</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
