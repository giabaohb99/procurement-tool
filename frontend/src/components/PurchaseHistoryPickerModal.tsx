import { useEffect, useState } from 'react'
import { api } from '../api/client'
import Pagination from './Pagination'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const PAGE_SIZE = 20

export type HistoryPick = {
  unit: string
  qty_order: number
  price: number
  vat: number
}

/**
 * Popup "Lịch sử mua hàng gần nhất" — mở từ dòng hàng khi lập ĐMH.
 * Liệt kê các lần mua đã HOÀN THÀNH của đúng mã hàng đó (20 dòng/trang, có ô tìm kiếm).
 * Chọn 1 dòng → trả về ĐVT/SL đặt/Đơn giá/VAT% để trang cha FILL vào dòng hàng.
 *
 * KHÔNG lọc theo NCC của đơn đang lập — mục đích chính là so giá giữa các NCC.
 * Trang cha chỉ fill vào state, KHÔNG tự lưu.
 */
export default function PurchaseHistoryPickerModal({
  productCode, productName, onPick, onClose,
}: {
  productCode: string
  productName?: string
  onPick: (v: HistoryPick) => void
  onClose: () => void
}) {
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [kw, setKw] = useState('')          // từ khóa đã debounce → thực sự gửi lên API
  const [loading, setLoading] = useState(true)

  // Khóa cuộn nền + đóng bằng Esc (theo lệ các popup khác trong app)
  useEffect(() => {
    document.body.style.overflow = 'hidden'
    const onEsc = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onEsc)
    return () => { document.body.style.overflow = ''; window.removeEventListener('keydown', onEsc) }
  }, [onClose])

  // Gõ xong mới gọi API (tránh bắn request mỗi ký tự); đổi từ khóa thì về trang 1
  useEffect(() => {
    const t = setTimeout(() => { setKw(search); setPage(1) }, 300)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => {
    setLoading(true)
    api.get(`/api/products/${encodeURIComponent(productCode)}/purchase-history`,
      { params: { page, page_size: PAGE_SIZE, search: kw } })
      .then((r) => { setRows(r.data.data.items || []); setTotal(r.data.data.total || 0) })
      .catch(() => { setRows([]); setTotal(0) })
      .finally(() => setLoading(false))
  }, [productCode, page, kw])

  const chon = (h: any) => {
    onPick({
      unit: h.unit || '',
      qty_order: Number(h.qty_order) || 0,
      price: Number(h.price) || 0,
      vat: Number(h.vat) || 0,
    })
    onClose()
  }

  return (
    <div onClick={onClose}
      style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 150,
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 12 }}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}
        style={{ width: 1060, maxWidth: '96vw', maxHeight: '92vh', background: '#fff', borderRadius: 14,
          boxShadow: '0 24px 40px -12px rgba(15,23,42,.28)', display: 'flex', flexDirection: 'column',
          overflow: 'hidden', fontFamily: 'inherit' }}>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '14px 18px', borderBottom: '1px solid var(--border)', gap: 12 }}>
          <div style={{ minWidth: 0 }}>
            <h3 style={{ margin: 0, fontSize: 16, color: 'var(--navy)' }}>Lịch sử mua hàng gần nhất</h3>
            <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2, overflow: 'hidden',
              textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {productCode}{productName ? ` · ${productName}` : ''} · {total} lần mua đã hoàn thành
            </div>
          </div>
          <button className="icon-btn" title="Đóng" onClick={onClose}>
            <i className="ti ti-x" style={{ fontSize: 18, color: 'var(--muted)' }} />
          </button>
        </div>

        <div style={{ padding: '12px 18px 0' }}>
          <input value={search} onChange={(e) => setSearch(e.target.value)} autoFocus
            placeholder="Tìm theo Mã PO / Nhà cung cấp / Công ty…"
            style={{ width: '100%', fontFamily: 'inherit', fontSize: 13.5 }} />
        </div>

        <div className="items-scroll" style={{ flex: 1, overflow: 'auto', padding: '12px 18px' }}>
          <table className="items-table" style={{ minWidth: 900 }}>
            <thead>
              <tr>
                <th>Ngày đặt</th>
                <th>Mã PO</th>
                <th>Nhà cung cấp</th>
                <th>ĐVT</th>
                <th style={{ textAlign: 'right' }}>SL đặt</th>
                <th style={{ textAlign: 'right' }}>Đơn giá</th>
                <th style={{ textAlign: 'right' }}>VAT%</th>
                <th style={{ textAlign: 'right' }}>Thành tiền</th>
                <th>Công ty</th>
                <th style={{ width: 92, textAlign: 'center' }}>Chọn</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((h) => (
                <tr key={h.id} className="clickable" onClick={() => chon(h)}>
                  <td>{h.order_date}</td>
                  <td>{h.po_code}</td>
                  <td>{h.supplier_name || h.supplier_code}</td>
                  <td>{h.unit}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(h.qty_order)}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(h.price)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(h.vat)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(h.amount)}</td>
                  <td>{h.company_name}</td>
                  <td style={{ textAlign: 'center' }}>
                    <button className="btn ghost" style={{ height: 26, fontSize: 11, padding: '0 8px' }}
                      onClick={(e) => { e.stopPropagation(); chon(h) }}>
                      Dùng giá này
                    </button>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', color: '#999', padding: 18 }}>
                    {loading ? 'Đang tải…' : kw ? 'Không có kết quả khớp từ khóa' : 'Mã hàng này chưa có lịch sử mua hàng'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        <div style={{ padding: '8px 18px 14px', borderTop: '1px solid var(--border)' }}>
          <Pagination page={page} pageSize={PAGE_SIZE} total={total} hideSize
            onChange={(p) => setPage(p)} />
          <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
            Chọn 1 dòng để điền ĐVT · SL đặt · Đơn giá · VAT% vào dòng hàng. Đơn chưa được lưu — bấm Lưu để ghi nhận.
          </div>
        </div>
      </div>
    </div>
  )
}
