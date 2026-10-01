// Bảng «Thuốc liên quan» của trang chi tiết thuốc BVTV (01/10/2026, đồng bộ bản v2
// `customs-pesticide-related-cards.tsx`, bê theo trang nguồn danhmuc.thuocbvtv.com): «Cùng công ty» và
// «Cùng hoạt chất». Số liệu tính ở backend: `GET /api/customs/pesticides/{id}/related`.
// Bố cục chốt sau hai lần bị chê (thẻ link lệch nhau → lưới ô có viền): BẢNG cùng khuôn bảng «Phạm vi
// sử dụng» ngay phía trên, nhãn tình trạng chung một cột, phân trang thay nút «Xem tất cả».
import { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import Pagination from '../Pagination'
import TableScroll from '../TableScroll'
import { PESTICIDE_STATUS, pesticideStatusBadgeClass } from '../../utils/customs-pesticide'

//  Lấy một lần đủ cả hai khối (trần backend 300), phân trang ở đây — đổi trang / tab không gọi lại.
const FETCH_LIMIT = 300

type Brief = {
  id: number; trade_name: string; pest_group: string; active_ingredient: string
  registrant: string; status: number; status_label: string
}
type Group = { total: number; items: Brief[]; label?: string }
type Related = { same_registrant: Group; same_ingredient: Group }
type Tab = 'registrant' | 'ingredient'

export default function CustomsPesticideRelated({ pesticideId, registrant }: { pesticideId: number; registrant: string }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [picked, setPicked] = useState<Tab | null>(null)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [data, setData] = useState<Related | null>(null)

  useEffect(() => {
    let alive = true
    setData(null); setPicked(null); setPage(1)
    api.get(`/api/customs/pesticides/${pesticideId}/related`, { params: { limit: FETCH_LIMIT }, _silent: true } as any)
      .then((r) => { if (alive) setData(r.data.data) })
      .catch(() => { if (alive) setData({ same_registrant: { total: 0, items: [] }, same_ingredient: { total: 0, items: [] } }) })
    return () => { alive = false }
  }, [pesticideId])

  //  Chưa bấm tab: mở tab có thuốc (công ty trước).
  const tab: Tab = picked
    ?? (data && data.same_registrant.total === 0 && data.same_ingredient.total > 0 ? 'ingredient' : 'registrant')
  const group = tab === 'registrant' ? data?.same_registrant : data?.same_ingredient
  const context = tab === 'registrant' ? registrant : data?.same_ingredient.label
  const items = group?.items ?? []
  const rows = items.slice((page - 1) * pageSize, page * pageSize)
  //  Tab công ty bỏ cột công ty — trùng nhau ở mọi dòng.
  const showCompany = tab === 'ingredient'
  const colCount = showCompany ? 5 : 4

  function pick(next: Tab) { setPicked(next); setPage(1) }

  return (
    <div className="card table-card" style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 16, padding: '14px 18px 8px' }}>
        <h3 className="sec-title" style={{ margin: 0 }}>Thuốc liên quan</h3>
        <div role="tablist" style={{ display: 'flex', gap: 4 }}>
          <TabButton active={tab === 'registrant'} onClick={() => pick('registrant')} label="Cùng công ty" count={data?.same_registrant.total} />
          <TabButton active={tab === 'ingredient'} onClick={() => pick('ingredient')} label="Cùng hoạt chất" count={data?.same_ingredient.total} />
        </div>
        {context && (
          <span title={context} style={{ minWidth: 0, color: 'var(--muted)', fontSize: 13, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {context}
          </span>
        )}
      </div>
      <TableScroll>
        <table>
          <thead>
            <tr>
              <th>Tên thuốc</th><th>Hoạt chất</th>{showCompany && <th>Công ty đăng ký</th>}<th>Phân nhóm</th><th>Tình trạng</th>
            </tr>
          </thead>
          <tbody>
            {!data && <tr><td colSpan={colCount} className="table-empty">Đang tải…</td></tr>}
            {data && rows.map((it) => (
              <tr key={it.id} style={{ cursor: 'pointer' }}
                //  Nút lùi ở trang thuốc kia quay về ĐÚNG thuốc đang xem.
                onClick={() => navigate(`/customs-prices/pesticides/${it.id}`, { state: { from: location.pathname + location.search } })}>
                <td style={{ fontWeight: 600 }}>{it.trade_name}</td>
                <td style={{ whiteSpace: 'normal' }}>{it.active_ingredient}</td>
                {showCompany && <td style={{ whiteSpace: 'normal' }}>{it.registrant}</td>}
                <td>{it.pest_group}</td>
                {/* Chỉ gắn nhãn khi KHÔNG còn hiệu lực — ô trống nghĩa là còn hiệu lực. */}
                <td>{it.status !== PESTICIDE_STATUS.active && it.status_label && (
                  <span className={'badge ' + pesticideStatusBadgeClass(it.status)}>{it.status_label}</span>
                )}</td>
              </tr>
            ))}
            {data && items.length === 0 && (
              <tr><td colSpan={colCount} className="table-empty">
                {tab === 'registrant' ? 'Công ty này chưa có thuốc nào khác trong danh mục.' : 'Chưa có thuốc nào khác cùng hoạt chất trong danh mục.'}
              </td></tr>
            )}
          </tbody>
        </table>
      </TableScroll>
      {items.length > 10 && (
        <Pagination page={page} pageSize={pageSize} total={items.length}
          onChange={(p, s) => { setPage(s !== pageSize ? 1 : p); setPageSize(s) }} />
      )}
    </div>
  )
}

function TabButton({ active, onClick, label, count }: { active: boolean; onClick: () => void; label: string; count?: number }) {
  return (
    <button type="button" role="tab" aria-selected={active} onClick={onClick}
      style={{
        background: active ? 'var(--info-bg)' : 'transparent', border: 'none', borderRadius: 6, padding: '6px 12px',
        cursor: 'pointer', fontSize: 14, color: active ? 'var(--teal)' : 'var(--muted)', fontWeight: active ? 600 : 400,
      }}>
      {label}{count !== undefined && <span style={{ marginLeft: 6, fontSize: 12, opacity: 0.8 }}>{count}</span>}
    </button>
  )
}
