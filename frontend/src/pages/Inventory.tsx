import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import Pagination from '../components/Pagination'
import { useAuth } from '../auth/AuthContext'
import SearchSelect from '../components/SearchSelect'
import FilterPanel, { FilterItem } from '../components/FilterPanel'
import { fmtDateTime } from '../utils/datetime'
import NumberInput from '../components/NumberInput'
import TableHead, { TableCells } from '../components/TableHead'
import TableToolbar from '../components/TableToolbar'
import { useTableColumns, TableColumn } from '../hooks/useTableColumns'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
// ĐƠN GIÁ hiện đủ 4 số lẻ — mặc định toLocaleString chỉ cho 3, cắt mất chữ số cuối
const fmtPrice = (n: any) => Number(n || 0).toLocaleString('vi-VN', { maximumFractionDigits: 4 })

export default function Inventory() {
  const { can } = useAuth()
  const [rows, setRows] = useState<any[]>([])
  const [companies, setCompanies] = useState<any[]>([])
  const [warehouses, setWarehouses] = useState<any[]>([])
  const [products, setProducts] = useState<any[]>([])
  const [f, setF] = useState<{
    company_id?: string
    warehouse_code?: string
    product_code?: string
    product_name?: string
    item_group?: string
    qty_status?: string
  }>({})
  const [groups, setGroups] = useState<any[]>([])
  const [units, setUnits] = useState<any[]>([])
  const [sortField, setSortField] = useState<string>('product_code')
  const [sortAsc, setSortAsc] = useState<boolean>(true)
  const [showAdjust, setShowAdjust] = useState(false)
  const [adj, setAdj] = useState<any>({ company_id: 0, warehouse_code: '', product_code: '', product_name: '', unit: '', qty: 0, note: '' })
  const [msg, setMsg] = useState(''); const [err, setErr] = useState('')
  const [selectedItem, setSelectedItem] = useState<any>(null)
  const [history, setHistory] = useState<any[]>([])
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  const companyName = (cid: number) => companies.find((c) => c.id === cid)?.name || cid || '—'

  const R = { textAlign: 'right', whiteSpace: 'nowrap' } as React.CSSProperties
  const COLS = useMemo<TableColumn<any>[]>(() => [
    { key: 'company_name', label: 'Công ty', sort: 'company_name', cell: (r) => companyName(r.company_id) },
    { key: 'warehouse_code', label: 'Kho', sort: 'warehouse_code' },
    { key: 'product_code', label: 'Mã SP', sort: 'product_code' },
    { key: 'product_name', label: 'Tên sản phẩm', sort: 'product_name' },
    { key: 'unit', label: 'ĐVT', sort: 'unit' },
    { key: 'qty', label: 'Tồn hiện tại', sort: 'qty', align: 'right', td: { ...R, fontWeight: 600 }, cell: (r) => fmt(r.qty) },
    { key: 'avg_cost', label: 'Đơn giá BQ', sort: 'avg_cost', align: 'right', td: R, cell: (r) => fmtPrice(r.avg_cost) },
    { key: 'value', label: 'Giá trị tồn', sort: 'value', align: 'right', td: { ...R, fontWeight: 600 }, cell: (r) => fmt(r.value) },
  ], [companies])
  const table = useTableColumns('inventory', COLS)

  async function viewDetail(item: any) {
    setSelectedItem(item)
    setHistory([])
    try {
      const r = await api.get('/api/inventory/moves', {
        params: {
          company_id: item.company_id,
          warehouse_code: item.warehouse_code,
          product_code: item.product_code,
          page_size: 100,
        }
      })
      setHistory(r.data.data.items)
    } catch (e) {
      console.error(e)
    }
  }

  async function load() {
    const params: any = { page_size: 500 }
    if (f.company_id) params.company_id = f.company_id
    if (f.warehouse_code) params.warehouse_code = f.warehouse_code
    if (f.product_code) params.product_code = f.product_code
    if (f.product_name) params.product_name = f.product_name
    if (f.item_group) params.item_group = f.item_group
    if (f.qty_status) params.qty_status = f.qty_status
    const r = await api.get('/api/inventory', { params })
    setRows(r.data.data.items)
  }

  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    api.get('/api/warehouses', { params: { page_size: 300 } }).then((r) => setWarehouses(r.data.data.items))
    api.get('/api/products', { params: { page_size: 2000 } }).then((r) => setProducts(r.data.data.items))
    api.get('/api/item-groups', { params: { page_size: 1000 } }).then((r) => setGroups(r.data.data.items)).catch(() => {})
    api.get('/api/units', { params: { page_size: 300 } }).then((r) => setUnits(r.data.data.items)).catch(() => {})
  }, [])

  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortAsc(!sortAsc)
    } else {
      setSortField(field)
      setSortAsc(true)
    }
  }

  useEffect(() => {
    load()
  }, [f.company_id, f.warehouse_code, f.item_group, f.qty_status, f.product_code, f.product_name])

  useEffect(() => {
    setPage(1)
  }, [f.company_id, f.warehouse_code, f.item_group, f.qty_status, f.product_code, f.product_name, sortField, sortAsc])

  async function submitAdjust() {
    setErr('')
    try {
      await api.post('/api/inventory/adjust', {
        ...adj,
        company_id: Number(adj.company_id) || 0,
        qty: Number(adj.qty) || 0,
        unit_price: adj.unit_price ? Number(adj.unit_price) : null
      })
      setShowAdjust(false); setMsg('Đã điều chỉnh tồn kho'); load()
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi điều chỉnh') }
  }

  const onAdjProduct = (code: string) => {
    const p = products.find((x) => x.code === code)
    setAdj((s: any) => ({ ...s, product_code: code, product_name: p ? p.name : s.product_name, unit: p ? p.unit : s.unit }))
  }

  const openAdjustNew = () => {
    setAdj({ company_id: 0, warehouse_code: '', product_code: '', product_name: '', unit: '', qty: '', unit_price: '', note: '' })
    setErr('')
    setShowAdjust(true)
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Tồn kho</h2>
        {can('inventory', 'write') && <button className="btn" onClick={openAdjustNew}><i className="ti ti-adjustments" />Điều chỉnh tồn</button>}
      </div>

      <FilterPanel onClear={() => setF({})} canClear={Object.values(f).some((v) => v)}>
        <FilterItem label="Công ty">
          <SearchSelect value={f.company_id || ''} placeholder="Tất cả"
            options={companies.map((c) => ({ value: String(c.id), label: c.name }))}
            onChange={(v) => setF((s) => ({ ...s, company_id: v }))} />
        </FilterItem>
        <FilterItem label="Kho">
          <SearchSelect value={f.warehouse_code || ''} placeholder="Tất cả"
            options={warehouses.map((w) => ({ value: w.code, label: `${w.code} — ${w.name}` }))}
            onChange={(v) => setF((s) => ({ ...s, warehouse_code: v }))} />
        </FilterItem>
        <FilterItem label="Tên sản phẩm" grow>
          <input value={f.product_name || ''} onChange={(e) => setF((s) => ({ ...s, product_name: e.target.value }))} onKeyDown={(e) => e.key === 'Enter' && load()} placeholder="Tên sản phẩm…" />
        </FilterItem>

        <FilterItem label="Phân loại" secondary active={!!f.item_group}>
          <SearchSelect value={f.item_group || ''} placeholder="Tất cả"
            options={groups.map((g) => ({ value: g.name, label: g.name }))}
            onChange={(v) => setF((s) => ({ ...s, item_group: v }))} />
        </FilterItem>
        <FilterItem label="Trạng thái tồn" secondary active={!!f.qty_status}>
          <SearchSelect value={f.qty_status || ''} placeholder="Tất cả"
            options={[
              { value: 'in_stock', label: 'Có tồn (> 0)' },
              { value: 'out_of_stock', label: 'Hết hàng (= 0)' },
              { value: 'negative_stock', label: 'Âm kho (< 0)' },
            ]}
            onChange={(v) => setF((s) => ({ ...s, qty_status: v }))} />
        </FilterItem>
        <FilterItem label="Mã SP" width={150} secondary active={!!f.product_code}>
          <input value={f.product_code || ''} onChange={(e) => setF((s) => ({ ...s, product_code: e.target.value }))} onKeyDown={(e) => e.key === 'Enter' && load()} placeholder="Mã SP…" />
        </FilterItem>
      </FilterPanel>

      {msg && <div style={{ color: 'var(--green)', fontSize: 13, marginBottom: 8 }}>{msg}</div>}
      {(() => {
        const sortedRows = [...rows].sort((a, b) => {
          let valA = a[sortField]
          let valB = b[sortField]
          if (sortField === 'company_name') {
            valA = companyName(a.company_id)
            valB = companyName(b.company_id)
          }
          if (typeof valA === 'string') {
            return sortAsc ? String(valA).localeCompare(String(valB)) : String(valB).localeCompare(String(valA))
          } else {
            return sortAsc ? (Number(valA || 0) - Number(valB || 0)) : (Number(valB || 0) - Number(valA || 0))
          }
        })

        const totalRows = sortedRows.length
        const totalPages = Math.max(1, Math.ceil(totalRows / pageSize))
        const pagedRows = sortedRows.slice((page - 1) * pageSize, page * pageSize)
        const startIdx = totalRows === 0 ? 0 : (page - 1) * pageSize + 1
        const endIdx = Math.min(page * pageSize, totalRows)

        return (
          <div className="card table-card">
            <TableToolbar {...table} onRefresh={load} />
            <div className="table-scroll">
              <table>
                <TableHead {...table} sortBy={sortField} sortDir={sortAsc ? 'asc' : 'desc'} onSort={handleSort} />
                <tbody>
                  {pagedRows.map((r, i) => (
                    <tr key={r.id} className="clickable" onClick={() => viewDetail(r)}>
                      <TableCells columns={table.columns} row={r} index={i} />
                    </tr>
                  ))}
                  {totalRows === 0 && <tr><td colSpan={table.columns.length} className="table-empty">Chưa có tồn kho</td></tr>}
                </tbody>
              </table>
            </div>
            <div className="table-foot">
              <Pagination page={page} pageSize={pageSize} total={totalRows}
                onChange={(p, s) => { setPage(p); setPageSize(s) }} />
            </div>
          </div>
        )
      })()}

      {showAdjust && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
          <div className="modal-card" style={{ width: 520, maxWidth: '100%', background: '#fff', borderRadius: 12, padding: 24 }} onClick={(e) => e.stopPropagation()}>
            <h3 style={{ marginTop: 0, color: 'var(--navy)' }}>Điều chỉnh tồn kho</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <div>
                <label style={{ fontSize: 13, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>Công ty</label>
                <SearchSelect value={adj.company_id ? String(adj.company_id) : ''} placeholder="Chọn/tìm công ty…"
                  options={companies.map((c) => ({ value: String(c.id), label: c.name }))}
                  onChange={(v) => setAdj((s: any) => ({ ...s, company_id: Number(v) || 0 }))} />
              </div>
              <div>
                <label style={{ fontSize: 13, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>Kho</label>
                <SearchSelect value={adj.warehouse_code || ''} placeholder="Chọn/tìm kho…"
                  options={warehouses.map((w) => ({ value: w.code, label: `${w.code} — ${w.name}` }))}
                  onChange={(v) => setAdj((s: any) => ({ ...s, warehouse_code: v }))} />
              </div>
              <div>
                <label style={{ fontSize: 13, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>Sản phẩm</label>
                <SearchSelect value={adj.product_code || ''} placeholder="Chọn/tìm sản phẩm…"
                  options={products.map((p) => ({ value: p.code, label: `${p.code} — ${p.name}` }))}
                  onChange={(v) => onAdjProduct(v)} />
              </div>
              <div>
                <label style={{ fontSize: 13, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>Đơn vị tính (ĐVT)</label>
                <SearchSelect value={adj.unit || ''} placeholder="Chọn/tìm ĐVT…"
                  options={units.map((u) => ({ value: u.name, label: u.name }))}
                  onChange={(v) => setAdj((s: any) => ({ ...s, unit: v }))} />
              </div>
              {(() => {
                if (!adj.product_code) return null
                const currentInv = rows.find(
                  (r) =>
                    r.company_id === Number(adj.company_id) &&
                    r.warehouse_code === adj.warehouse_code &&
                    r.product_code === adj.product_code
                )
                return (
                  <div style={{ padding: 12, background: '#f8fafc', borderRadius: 8, fontSize: 13, border: '1px dashed #cbd5e1', display: 'flex', flexDirection: 'column', gap: 6 }}>
                    <div>
                      <span style={{ color: 'var(--muted)' }}>ĐVT sản phẩm: </span>
                      <strong>{adj.unit || '—'}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--muted)' }}>Tồn hiện tại ở kho này: </span>
                      <strong style={{ color: 'var(--navy)' }}>{currentInv ? fmt(currentInv.qty) : '0'}</strong>
                    </div>
                    <div>
                      <span style={{ color: 'var(--muted)' }}>Đơn giá bình quân hiện tại: </span>
                      <strong>{currentInv ? `${fmtPrice(currentInv.avg_cost)} đ` : '0 đ'}</strong>
                    </div>
                  </div>
                )
              })()}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                <div>
                  <label style={{ fontSize: 13, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>Số lượng (+/−)</label>
                  <input style={{ width: '100%', height: 38 }} type="number" value={adj.qty} onChange={(e) => setAdj((s: any) => ({ ...s, qty: e.target.value }))} placeholder="Ví dụ: 10 hoặc -5..." />
                </div>
                <div>
                  <label style={{ fontSize: 13, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>Đơn giá điều chỉnh (đ)</label>
                  <NumberInput className="input" style={{ width: '100%', height: 38 }} value={Number(adj.unit_price) || 0} maxDecimals={4} onChange={(n) => setAdj((s: any) => ({ ...s, unit_price: n }))} placeholder="Mặc định theo giá hiện tại" />
                </div>
              </div>
              <div>
                <label style={{ fontSize: 13, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>Lý do</label>
                <input style={{ width: '100%', height: 38 }} value={adj.note} onChange={(e) => setAdj((s: any) => ({ ...s, note: e.target.value }))} placeholder="Lý do điều chỉnh..." />
              </div>
            </div>
            {err && <div className="err" style={{ marginTop: 8 }}>{err}</div>}
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 14 }}>
              <button className="btn ghost" onClick={() => setShowAdjust(false)}>Hủy</button>
              {can('inventory', 'write') && <button className="btn" onClick={submitAdjust}>Lưu điều chỉnh</button>}
            </div>
          </div>
        </div>
      )}
      {selectedItem && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }} onClick={() => setSelectedItem(null)}>
          <div className="modal-card" style={{ width: 900, maxWidth: '100%', maxHeight: '90vh', overflowY: 'auto', background: '#fff', borderRadius: 12, padding: 24 }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 18, borderBottom: '1px solid #f1f5f9', paddingBottom: 12 }}>
              <h3 style={{ margin: 0, color: 'var(--navy)', fontSize: 18 }}>Chi tiết tồn kho & Lịch sử biến động</h3>
              <button className="btn ghost" style={{ padding: 4 }} onClick={() => setSelectedItem(null)}><i className="ti ti-x" style={{ fontSize: 20 }} /></button>
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16, marginBottom: 24, padding: 16, background: '#f8fafc', borderRadius: 8 }}>
              <div>
                <span style={{ fontSize: 12, color: 'var(--muted)', display: 'block' }}>Sản phẩm</span>
                <strong style={{ fontSize: 14 }}>{selectedItem.product_code} — {selectedItem.product_name}</strong>
                {(() => {
                  const p = products.find((x) => x.code === selectedItem.product_code)
                  return p ? (
                    <Link to={`/products/${p.id}`} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, marginLeft: 8, fontSize: 12, color: 'var(--primary)', fontWeight: 600, textDecoration: 'none' }} title="Xem chi tiết sản phẩm">
                      <i className="ti ti-external-link" /> Chi tiết
                    </Link>
                  ) : null
                })()}
              </div>
              <div>
                <span style={{ fontSize: 12, color: 'var(--muted)', display: 'block' }}>Đơn vị tính</span>
                <strong>{selectedItem.unit}</strong>
              </div>
              <div>
                <span style={{ fontSize: 12, color: 'var(--muted)', display: 'block' }}>Công ty</span>
                <strong>{companyName(selectedItem.company_id)}</strong>
              </div>
              <div>
                <span style={{ fontSize: 12, color: 'var(--muted)', display: 'block' }}>Kho</span>
                <strong>{selectedItem.warehouse_code}</strong>
              </div>
              <div>
                <span style={{ fontSize: 12, color: 'var(--muted)', display: 'block' }}>Tồn hiện tại</span>
                <strong style={{ fontSize: 16, color: selectedItem.qty >= 0 ? 'var(--navy)' : 'var(--red)' }}>{fmt(selectedItem.qty)}</strong>
              </div>
              <div>
                <span style={{ fontSize: 12, color: 'var(--muted)', display: 'block' }}>Đơn giá bình quân</span>
                <strong style={{ whiteSpace: 'nowrap' }}>{fmtPrice(selectedItem.avg_cost)} đ</strong>
              </div>
              <div>
                <span style={{ fontSize: 12, color: 'var(--muted)', display: 'block' }}>Giá trị tồn kho</span>
                <strong style={{ color: 'var(--primary)', whiteSpace: 'nowrap' }}>{fmt(selectedItem.value)} đ</strong>
              </div>
            </div>

            <h4 style={{ margin: '0 0 10px 0', color: 'var(--navy)', fontSize: 15 }}>Lịch sử giao dịch & cập nhật tồn kho</h4>
            <div className="table-wrapper" style={{ maxHeight: 350, overflowY: 'auto', border: '1px solid #e2e8f0', borderRadius: 8 }}>
              <table style={{ margin: 0 }}>
                <thead>
                  <tr style={{ background: '#f1f5f9', position: 'sticky', top: 0, zIndex: 1 }}>
                    <th>Thời gian</th>
                    <th>Loại giao dịch</th>
                    <th style={{ textAlign: 'right' }}>Thay đổi</th>
                    <th style={{ textAlign: 'right' }}>Đơn giá</th>
                    <th style={{ textAlign: 'right' }}>Thành tiền</th>
                    <th>Người thực hiện</th>
                    <th>Ghi chú / Lý do</th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h: any) => (
                    <tr key={h.id}>
                      <td style={{ whiteSpace: 'nowrap' }}>{fmtDateTime(h.at)}</td>
                      <td>
                        {h.ref_type === 'gr' ? (
                          <span className="badge ok" style={{ fontSize: 11 }}>Nhập kho (Nhận hàng)</span>
                        ) : (
                          <span className="badge info" style={{ fontSize: 11, background: '#e0f2fe', color: '#0369a1' }}>Điều chỉnh tay</span>
                        )}
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 600, color: h.qty >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        {h.qty >= 0 ? `+${fmt(h.qty)}` : fmt(h.qty)}
                      </td>
                      <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>{h.unit_price > 0 ? `${fmtPrice(h.unit_price)} đ` : '—'}</td>
                      <td style={{ textAlign: 'right', fontWeight: 500, whiteSpace: 'nowrap' }}>
                        {h.qty * h.unit_price !== 0 ? `${fmt(Math.abs(h.qty * h.unit_price))} đ` : '—'}
                      </td>
                      <td>{h.operator_name}</td>
                      <td style={{ maxWidth: 200, wordBreak: 'break-word' }}>{h.note || '—'}</td>
                    </tr>
                  ))}
                  {history.length === 0 && (
                    <tr>
                      <td colSpan={7} style={{ textAlign: 'center', color: '#999', padding: 20 }}>
                        Chưa có lịch sử biến động kho cho sản phẩm này
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
              {can('inventory', 'write') && (
                <button className="btn" onClick={() => {
                  setAdj({
                    company_id: selectedItem.company_id,
                    warehouse_code: selectedItem.warehouse_code,
                    product_code: selectedItem.product_code,
                    product_name: selectedItem.product_name,
                    unit: selectedItem.unit,
                    qty: '',
                    note: ''
                  })
                  setErr('')
                  setSelectedItem(null)
                  setShowAdjust(true)
                }}>
                  <i className="ti ti-adjustments" /> Điều chỉnh tồn kho này
                </button>
              )}
              <button className="btn ghost" onClick={() => setSelectedItem(null)}>Đóng</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
