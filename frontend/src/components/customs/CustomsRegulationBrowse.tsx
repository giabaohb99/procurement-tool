// duoc-CR-490 — thẻ «Pháp lý» của Tra cứu thị trường (bê từ bản v2 `customs-regulation-tab.tsx`):
// bảng DUYỆT toàn bộ danh mục hóa chất theo văn bản — hoạt chất BVTV cấm (TT 75/2025), NĐ
// 24/2026 phụ lục I–IV, hóa chất phải công bố theo lô (TT 01/2026). Trước đây chỉ tra được từng
// từ trong thẻ «Pháp lý & thuế»; thẻ đó nay chỉ còn phần thuế (`CustomsTabs.tsx` → `CustomsTariff`).
//
// Bộ lọc là state CỤC BỘ: ô tìm `q` trên URL là của thanh lọc dòng hàng hải quan, dùng chung thì
// đổi thẻ là ô tìm hóa chất bị ghi đè bằng tên hàng. Riêng thẻ cảnh báo trên đầu vẫn đọc từ khóa
// dòng hàng đang tra (`filters.q`) — dải cảnh báo ở các thẻ khác bảo «xem thẻ Pháp lý» là trỏ vào đây.
import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import Pagination from '../Pagination'
import SearchSelect from '../SearchSelect'
import TableScroll from '../TableScroll'
import { CustomsFilters } from './customs-shared'
import CustomsBannedPesticideModal from './CustomsBannedPesticideModal'
import CustomsRegulationAlertTable from './CustomsRegulationAlertTable'
import {
  buildRegulationParams, formatBannedLabel, formatThresholdKg, regulationBadgeClass,
  resolveRegulationEmptyMessage,
} from '../../utils/customs-regulation'

const ALL = ''
const PAGE_SIZE = 50

export default function CustomsRegulationBrowse({ filters, alerts }: { filters: CustomsFilters; alerts: any[] }) {
  const [search, setSearch] = useState('')
  const [applied, setApplied] = useState('')
  const [listCode, setListCode] = useState(ALL)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(PAGE_SIZE)
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [options, setOptions] = useState<any>(null)
  const [pesticidesOf, setPesticidesOf] = useState<any | null>(null)

  useEffect(() => {
    api.get('/api/customs/regulations/options').then((r) => setOptions(r.data.data))
  }, [])

  // Gõ xong ngưng 350ms mới lọc, cùng nhịp mọi ô tìm khác trên màn.
  useEffect(() => {
    const t = setTimeout(() => { setApplied(search.trim()); setPage(1) }, 350)
    return () => clearTimeout(t)
  }, [search])

  useEffect(() => {
    setLoading(true)
    api.get('/api/customs/regulations', { params: { ...buildRegulationParams(applied, listCode), page, page_size: pageSize } })
      .then((r) => { setRows(r.data.data.items); setTotal(r.data.data.total) })
      .finally(() => setLoading(false))
  }, [applied, listCode, page, pageSize])

  const filtersActive = !!applied || listCode !== ALL
  function resetFilters() {
    setSearch(''); setApplied(''); setListCode(ALL); setPage(1)
  }
  function pickListCode(v: string) {
    setListCode(v); setPage(1)
  }

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      <div style={{ fontSize: 12, color: 'var(--muted)' }}>
        Tra cứu tham khảo từ văn bản đã nạp (NĐ 24/2026/NĐ-CP · TT 75/2025/TT-BNNMT · TT 01/2026/TT-BCT).
        Không thay cho ý kiến pháp chế — đối chiếu văn bản gốc trước khi quyết định.
      </div>

      {alerts.length > 0 && (
        <div className="card" style={{ padding: 12 }}>
          <div style={{ fontWeight: 600, marginBottom: 6 }}>Cảnh báo cho từ khóa đang tra «{filters.q}»</div>
          <CustomsRegulationAlertTable items={alerts} />
        </div>
      )}

      <div className="card" style={{ padding: 12 }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center', marginBottom: 10 }}>
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Tên, số CAS hoặc công thức (vd H2SO4)…" style={{ width: 280 }} />
          <div style={{ width: 260 }}>
            <SearchSelect value={listCode} placeholder="Tất cả văn bản" autoSelectSingle={false}
              options={(options?.lists || []).map((l: any) => ({ value: String(l.value), label: `${l.label} (${l.count})` }))}
              onChange={pickListCode} />
          </div>
          {filtersActive && (
            <button className="btn ghost" onClick={resetFilters}><i className="ti ti-rotate" />Xóa lọc</button>
          )}
        </div>

        <TableScroll>
          <table>
            <thead><tr>
              <th>Danh mục</th><th>Tên</th><th>Số CAS</th><th>Ngưỡng / Mức cấm</th><th>Lưu ý</th><th>Thuốc BVTV chứa</th>
            </tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <span className={`badge ${regulationBadgeClass(r.list_code)}`}>{r.list_label}</span>
                  </td>
                  <td>{r.name}{r.name_vi && r.name_vi !== r.name ? <div style={{ fontSize: 12, color: 'var(--muted)' }}>{r.name_vi}</div> : null}</td>
                  <td>{r.cas_no || '—'}</td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    {r.list_code === 10
                      ? <span className="badge err" style={{ fontWeight: 700 }}>{formatBannedLabel(r.banned_year)}</span>
                      : formatThresholdKg(r.threshold_kg)
                        ? <span style={{ fontSize: 15, fontWeight: 700, color: '#c2410c', fontVariantNumeric: 'tabular-nums' }}>{formatThresholdKg(r.threshold_kg)}</span>
                        : null}
                  </td>
                  <td style={{ fontSize: 13 }}>{r.obligation}</td>
                  <td>{r.list_code === 10 && <PesticideCountCell row={r} onOpen={() => setPesticidesOf(r)} />}</td>
                </tr>
              ))}
              {!loading && rows.length === 0 && (
                <tr><td colSpan={6} className="table-empty">{resolveRegulationEmptyMessage(options?.total ?? 0)}</td></tr>
              )}
            </tbody>
          </table>
        </TableScroll>
        <div className="table-foot">
          <Pagination page={page} pageSize={pageSize} total={total} onChange={(p, s) => { setPage(p); setPageSize(s) }} />
        </div>
      </div>

      <CustomsBannedPesticideModal regulation={pesticidesOf} onClose={() => setPesticidesOf(null)} />
    </div>
  )
}

/**
 * Cột «Thuốc BVTV chứa» — chỉ dòng TT 75 (cấm) có số. `null` = danh mục thuốc CHƯA nạp (khác
 * "0 thuốc" — phải nói ra, không thì đọc thành "đã đối chiếu, sạch"). Tên cấm không rút ra được
 * khóa so khớp nào (chữ tiếng Việt có dấu…) cũng phải nói ra, cùng lý do. Bấm số → danh sách.
 */
function PesticideCountCell({ row, onOpen }: { row: any; onOpen: () => void }) {
  if (row.pesticide_matchable === false) {
    return <span style={{ fontSize: 12, color: 'var(--muted)', fontStyle: 'italic' }}>Tên không đối chiếu được</span>
  }
  if (row.pesticide_count === null || row.pesticide_count === undefined) {
    return <span style={{ fontSize: 12, color: 'var(--muted)', fontStyle: 'italic' }}>Chưa nạp danh mục thuốc</span>
  }
  if (row.pesticide_count === 0) {
    return <span style={{ color: 'var(--muted)' }}>0</span>
  }
  return (
    <button type="button" className="btn ghost" style={{ padding: 0, height: 'auto', color: '#b91c1c', fontWeight: 700 }}
      onClick={onOpen}>
      {row.pesticide_count.toLocaleString('vi-VN')} thuốc
    </button>
  )
}
