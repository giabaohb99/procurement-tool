import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import Pagination from './Pagination'
import SearchSelect from './SearchSelect'
import FilterPanel, { FilterItem } from './FilterPanel'

/**
 * Tab "Đơn hàng về kho" ở trang chi tiết Kho.
 * 1 dòng = 1 DÒNG HÀNG của đơn mua hàng có liên quan tới kho này — lấy theo "Kho nhận mặc định"
 * ở Chi tiết dòng, hoặc có lần giao đổi kho về đây (xem GET /api/purchase-orders/lines).
 * Bấm dòng → mở chi tiết đơn mua hàng.
 */

const fmtQty = (n: any) => Number(n || 0).toLocaleString('vi-VN', { maximumFractionDigits: 3 })
const PG_COLOR: Record<string, string> = {
  'Chưa đặt hàng': '#94a3b8', 'Đã đặt hàng': '#2563eb', 'Đã nhận hàng': '#0891b2',
  'Chưa gửi ĐMH cho KT': '#db2777', 'Đã gửi ĐMH cho KT': '#7c3aed',
  'Hoàn thành': '#16a34a', 'Tạm ngưng': '#d97706', 'Hủy đơn': '#dc2626',
}
const PROGRESS_OPTIONS = Object.keys(PG_COLOR)
const pgBadge = (s: string) => (
  <span className="badge" style={{ background: (PG_COLOR[s] || '#94a3b8') + '22', color: PG_COLOR[s] || '#64748b' }}>{s}</span>
)

export default function WarehousePurchaseLines({ warehouseCode }: { warehouseCode?: string }) {
  const navigate = useNavigate()
  const { can } = useAuth()
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [q, setQ] = useState('')
  const [progress, setProgress] = useState('')
  const [loading, setLoading] = useState(true)
  const allowed = can('purchase_order', 'read')

  const timer = useRef<any>(null)
  useEffect(() => {
    if (!warehouseCode || !allowed) { setRows([]); setTotal(0); setLoading(false); return }
    clearTimeout(timer.current)
    timer.current = setTimeout(() => {
      setLoading(true)
      api.get('/api/purchase-orders/lines', {
        params: {
          warehouse_code: warehouseCode, page, page_size: pageSize,
          ...(q.trim() ? { q: q.trim() } : {}),
          ...(progress ? { progress_status: progress } : {}),
        },
      })
        .then((r) => { setRows(r.data.data.items || []); setTotal(r.data.data.total || 0) })
        .catch(() => { setRows([]); setTotal(0) })
        .finally(() => setLoading(false))
    }, 300)
    return () => clearTimeout(timer.current)
  }, [warehouseCode, allowed, page, pageSize, q, progress])

  if (!allowed) {
    return <div className="card" style={{ padding: 30, textAlign: 'center', color: '#999' }}>
      Bạn không có quyền xem đơn mua hàng.
    </div>
  }

  const R = { textAlign: 'right' as const }
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <FilterPanel canClear={!!(q || progress)} onClear={() => { setQ(''); setProgress(''); setPage(1) }}>
        <FilterItem label="Tìm mã PO / sản phẩm" grow>
          <input value={q} placeholder="Nhập mã PO, mã hoặc tên sản phẩm…"
            onChange={(e) => { setQ(e.target.value); setPage(1) }} />
        </FilterItem>
        <FilterItem label="Tiến độ dòng" width={200}>
          <SearchSelect value={progress} placeholder="Tất cả" options={PROGRESS_OPTIONS}
            onChange={(v) => { setProgress(v); setPage(1) }} />
        </FilterItem>
      </FilterPanel>

      <div className="card" style={{ padding: 18 }}>
        <h3 className="sec-title">Đơn hàng về kho{total > 0 ? ` (${total} dòng hàng)` : ''}</h3>
        <div className="items-scroll">
          <table className="items-table" style={{ minWidth: 1040 }}>
            <thead>
              <tr>
                <th>Ngày đặt</th><th>Mã PO</th><th>Nhà cung cấp</th>
                <th>Mã SP</th><th>Tên sản phẩm</th><th>ĐVT</th>
                <th style={R}>SL đặt</th>
                <th style={R} title="SL đã nhận tại kho này — phần chưa ghi rõ kho ở lần giao tính về kho mặc định của dòng">Đã nhận (kho này)</th>
                <th style={R} title="SL đã nhận trên toàn bộ các kho của dòng">Đã nhận (tất cả)</th>
                <th style={R}>Còn lại</th>
                <th>Tiến độ</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.item_id} className="clickable" onClick={() => navigate(`/purchase-orders/${r.po_id}`)}>
                  <td>{r.order_date}</td>
                  <td style={{ color: 'var(--teal)', fontWeight: 600 }}>{r.po_code}</td>
                  <td>{r.supplier_name || r.supplier_code}</td>
                  <td>{r.product_code}</td><td>{r.product_name}</td><td>{r.unit}</td>
                  <td style={R}>{fmtQty(r.qty_order)}</td>
                  <td style={{ ...R, fontWeight: 600 }}>{fmtQty(r.qty_received_here)}</td>
                  <td style={R}>{fmtQty(r.qty_received)}</td>
                  <td style={{ ...R, color: r.qty_remaining > 0 ? 'var(--red)' : undefined }}>{fmtQty(r.qty_remaining)}</td>
                  <td>{pgBadge(r.progress_status)}</td>
                </tr>
              ))}
              {!loading && rows.length === 0 && (
                <tr><td colSpan={11} style={{ textAlign: 'center', color: '#999', padding: 16 }}>
                  {q || progress ? 'Không có dòng hàng nào khớp bộ lọc' : 'Chưa có đơn mua hàng nào chỉ định về kho này'}
                </td></tr>
              )}
              {loading && <tr><td colSpan={11} style={{ textAlign: 'center', color: '#999', padding: 16 }}>Đang tải…</td></tr>}
            </tbody>
          </table>
        </div>
        <Pagination page={page} pageSize={pageSize} total={total}
          onChange={(p, s) => { setPage(p); setPageSize(s) }} />
      </div>
    </div>
  )
}
