import { useEffect, useMemo, useState } from 'react'
import { useAuth } from '../../auth/AuthContext'
import Pagination from '../../components/Pagination'
import TableToolbar from '../../components/TableToolbar'
import { toast } from '../../components/toast'
import PackagingLastPricesTable from '../../components/packaging/PackagingLastPricesTable'
import PackagingLastPricesToolbar from '../../components/packaging/PackagingLastPricesToolbar'
import { downloadExport, fetchLastPrices } from '../../api/packaging-cost'
import { useDebouncedValue } from '../../hooks/use-debounced-value'
import { useLatestQuery } from '../../hooks/use-latest-query'
import {
  buildLastPricesParams, EMPTY_LAST_PRICES_FILTERS, nextSort, sortKeyOutsideN, type LastPricesFilters,
} from '../../utils/packaging-query'
import { LAST_PRICES_URL_KEYS, lastPricesScreenToSearch, searchToLastPricesScreen } from '../../utils/packaging-prices-screen-url'
import { useSearchSyncToUrl } from '../../hooks/useSearchSyncToUrl'
import '../../components/packaging/packaging.css'

/**
 * Màn GIÁ MUA GẦN NHẤT: mỗi mã VTBB một dòng với ngày mua, nhà cung cấp, đơn giá của n lần mua có giá gần nhất
 * (n = 3 / 5 / 10; xanh = đắt hơn lần cũ kế bên, đỏ = rẻ hơn), biến động lần 1 so lần 2 / lần n và giá trung bình.
 * Lọc + xếp + phân trang tại MÁY CHỦ; tham số đi kèm Xuất Excel để ra đúng thứ tự.
 */
export default function PackagingLastPrices() {
  const { can } = useAuth()
  //  Trạng thái ban đầu đọc từ URL (F5 / link được chia sẻ vẫn giữ bộ lọc, số lần, cột xếp, trang).
  const [initial] = useState(() => searchToLastPricesScreen(window.location.search))
  const [filters, setFilters] = useState<LastPricesFilters>(initial.filters)
  const [sortBy, setSortBy] = useState(initial.sortBy)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(initial.sortDir)
  const [page, setPage] = useState(initial.page)
  const [pageSize, setPageSize] = useState(initial.pageSize)
  const [exporting, setExporting] = useState(false)
  const q = useDebouncedValue(filters.q, 350)

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo(() => buildLastPricesParams(filters, q, { by: sortBy, dir: sortDir }), [filters, q, sortBy, sortDir])
  const params = useMemo(() => ({ ...filterParams, page, page_size: pageSize }), [filterParams, page, pageSize])
  const list = useLatestQuery(() => fetchLastPrices(params), JSON.stringify(params))

  const urlSearch = useMemo(
    () => lastPricesScreenToSearch({ filters, sortBy, sortDir, page, pageSize }), [filters, sortBy, sortDir, page, pageSize])
  useSearchSyncToUrl(urlSearch, LAST_PRICES_URL_KEYS)
  //  Trang từ URL (hoặc sau khi lọc ra ít dòng) vượt số trang thật thì lùi về trang cuối.
  const listTotal = list.data?.total
  useEffect(() => {
    if (listTotal == null) return
    const last = Math.max(1, Math.ceil(listTotal / pageSize))
    if (page > last) setPage(last)
  }, [listTotal, pageSize, page])

  const changeFilters = (next: LastPricesFilters) => {
    //  Bớt số lần mà đang xếp theo một lần đã biến mất → bỏ xếp, khỏi xếp theo cột không còn thấy.
    if (sortBy && sortKeyOutsideN(sortBy, next.n)) setSortBy('')
    //  "Hiện số lượng" chỉ đổi cột hiện, không đổi kết quả → giữ nguyên trang.
    if (next.showQty === filters.showQty) setPage(1)
    setFilters(next)
  }
  const onSort = (key: string) => { const s = nextSort(sortBy, sortDir, key); setSortBy(s.by); setSortDir(s.dir); setPage(1) }
  const reset = { ...EMPTY_LAST_PRICES_FILTERS, n: filters.n, showQty: filters.showQty }
  const filtersActive = JSON.stringify({ ...filters, n: 0, showQty: false }) !== JSON.stringify({ ...reset, n: 0, showQty: false })

  async function exportExcel() {
    if (exporting) return
    setExporting(true)
    try { await downloadExport('last-prices', { ...filterParams, show_qty: filters.showQty || undefined }, 'gia-mua-gan-nhat.xlsx') }
    catch (e: any) { toast.error(e?.message || 'Không xuất được tệp Excel') }
    finally { setExporting(false) }
  }

  const rows = list.data?.items ?? []
  return (
    <div>
      <div className="pkg-head" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <h2 className="page-title" style={{ margin: 0 }}>Giá mua gần nhất</h2>
          <div className="pkg-hint">Đơn giá của n lần mua có giá gần nhất của từng mã vật tư bao bì (VNĐ, chưa VAT). Lần 1 là lần mua mới nhất; dòng đơn giá 0 bị bỏ qua.</div>
        </div>
        {can('packaging_cost', 'export') && (
          <button className="btn outline" disabled={exporting} onClick={exportExcel} title="Xuất Excel" aria-label="Xuất Excel">
            <i className="ti ti-file-spreadsheet" /><span className="pkg-btn-label">{exporting ? 'Đang xuất…' : 'Xuất Excel'}</span>
          </button>
        )}
      </div>

      <div className="card table-card">
        <PackagingLastPricesToolbar filters={filters} onChange={changeFilters}
          groups={list.data?.groups ?? []} suppliers={list.data?.suppliers ?? []} />
        <div className="table-tools tt-compact" style={{ marginTop: -4 }}>
          <span className="pkg-hint" style={{ marginRight: 'auto' }}>{list.data ? `${list.data.total} mã` : ''}</span>
          {filtersActive && <button className="btn ghost" onClick={() => changeFilters(reset)}><i className="ti ti-rotate" />Xóa lọc</button>}
          <button className="btn ghost" onClick={list.reload} disabled={list.loading} title="Tải lại dữ liệu">
            <i className={'ti ti-refresh' + (list.loading ? ' spin' : '')} /><span className="tt-label">Tải lại</span>
          </button>
        </div>
        <PackagingLastPricesTable rows={rows} n={filters.n} showQty={filters.showQty}
          sortBy={sortBy} sortDir={sortDir} onSort={onSort}
          empty={list.failed ? 'Không tải được dữ liệu — thử tải lại.' : list.loading ? 'Đang tải…'
            : filtersActive ? 'Không có mã nào khớp bộ lọc.' : 'Chưa có mã vật tư bao bì nào có giá.'} />
        <div className="table-foot">
          <Pagination page={page} pageSize={pageSize} total={list.data?.total ?? 0} onChange={(p, s) => { setPage(p); setPageSize(s) }} />
        </div>
      </div>
    </div>
  )
}
