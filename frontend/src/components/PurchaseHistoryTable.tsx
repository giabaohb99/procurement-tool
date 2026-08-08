import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import Pagination from './Pagination'
import { fmtPrice, fmtVND } from '../utils/money'
import { fmtDateStr } from '../utils/datetime'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')

/**
 * Chú thích cho dòng DỮ LIỆU CŨ: chỉ ra đúng dòng trong file Excel gốc.
 * Lần mua trước khi có hệ thống thì không có ĐMH để mở, nhưng `extra` vẫn giữ nguồn
 * (file + sheet + số dòng) — đủ để đối chiếu lại bản gốc khi ai đó thắc mắc con số.
 */
function legacyOrigin(h: any): string {
  const e = h.extra || {}
  const parts = [e.nguon, e.sheet, e.dong_excel ? `dòng ${e.dong_excel}` : ''].filter(Boolean)
  return parts.length
    ? `Lần mua trước khi dùng hệ thống — không có đơn mua hàng.\nNguồn: ${parts.join(' · ')}`
    : 'Lần mua trước khi dùng hệ thống — không có đơn mua hàng để mở'
}

/**
 * Bảng LỊCH SỬ MUA HÀNG — 1 dòng = 1 lần mua (1 dòng hàng của ĐMH đã "Hoàn thành").
 * Dùng chung 2 màn: chi tiết Sản phẩm (truyền `productCode`) và chi tiết NCC (truyền `supplierCode`).
 * Cột thứ 3 đổi theo ngữ cảnh: ở màn SP hiện NCC, ở màn NCC hiện Sản phẩm.
 */
export default function PurchaseHistoryTable({
  productCode, supplierCode,
}: {
  productCode?: string
  supplierCode?: string
}) {
  const navigate = useNavigate()
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [loading, setLoading] = useState(false)

  const byProduct = !!productCode
  const url = byProduct
    ? `/api/products/${encodeURIComponent(productCode!)}/purchase-history`
    : `/api/suppliers/${encodeURIComponent(supplierCode || '')}/purchase-history`

  useEffect(() => {
    if (!productCode && !supplierCode) { setRows([]); setTotal(0); return }
    setLoading(true)
    api.get(url, { params: { page, page_size: pageSize } })
      .then((r) => { setRows(r.data.data.items || []); setTotal(r.data.data.total || 0) })
      .catch(() => { setRows([]); setTotal(0) })
      .finally(() => setLoading(false))
  }, [productCode, supplierCode, page, pageSize])

  return (
    // Cả 2 nơi dùng đều là TAB riêng (chi tiết SP / chi tiết NCC) → không cần margin trên
    <div className="card" style={{ padding: 18 }}>
      <h3 className="sec-title">Lịch sử mua hàng{total > 0 ? ` (${total})` : ''}</h3>
      <div className="items-scroll">
        <table className="items-table" style={{ minWidth: 900 }}>
          <thead>
            <tr>
              <th>Ngày đặt</th>
              <th>Mã PO</th>
              <th>{byProduct ? 'Nhà cung cấp' : 'Sản phẩm'}</th>
              <th>ĐVT</th>
              <th style={{ textAlign: 'right' }}>SL đặt</th>
              <th style={{ textAlign: 'right' }}>Đơn giá</th>
              <th style={{ textAlign: 'right' }}>VAT%</th>
              <th style={{ textAlign: 'right' }}>Thành tiền</th>
              <th>Công ty</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((h) => (
              // Dòng DỮ LIỆU CŨ (nhập từ file lịch sử trước khi có hệ thống) không có ĐMH
              // để mở → không cho click, cột Mã PO ghi rõ nguồn thay vì để trống.
              <tr key={h.id} className={h.po_id ? 'clickable' : undefined}
                  onClick={h.po_id ? () => navigate(`/purchase-orders/${h.po_id}`) : undefined}>
                <td>{fmtDateStr(h.order_date) || '—'}</td>
                <td>{h.po_code || (
                  // Không phải thiếu dữ liệu: lần mua này diễn ra TRƯỚC khi có hệ thống nên
                  // không hề tồn tại đơn để trỏ tới — ghi rõ để không ai đi tìm mã PO.
                  // Tooltip chỉ ra đúng dòng trong file Excel gốc: không truy được sang đơn
                  // nhưng vẫn truy được NGUỒN, đủ để đối chiếu khi cần.
                  <span className="badge gray" title={legacyOrigin(h)}
                    style={{ fontSize: 11, fontWeight: 500 }}>Dữ liệu cũ</span>
                )}</td>
                <td>{byProduct ? (h.supplier_name || h.supplier_code) : (h.product_name || h.product_code)}</td>
                <td>{h.unit}</td>
                <td style={{ textAlign: 'right' }}>{fmt(h.qty_order)}</td>
                <td style={{ textAlign: 'right' }}>{fmtPrice(h.price)}</td>
                <td style={{ textAlign: 'right' }}>{fmt(h.vat)}</td>
                <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmtVND(h.amount)}</td>
                <td>{h.company_name}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={9} style={{ textAlign: 'center', color: '#999', padding: 14 }}>
                  {loading ? 'Đang tải…' : 'Chưa có lịch sử mua hàng'}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {total > pageSize && (
        <Pagination page={page} pageSize={pageSize} total={total}
          onChange={(p, s) => { setPage(p); setPageSize(s) }} />
      )}
    </div>
  )
}
