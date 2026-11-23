import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useAuth } from '../../auth/AuthContext'
import DateRangePicker from '../../components/DateRangePicker'
import { toast } from '../../components/toast'
import PackagingCodePicker from '../../components/packaging/PackagingCodePicker'
import PackagingImpactSummary from '../../components/packaging/PackagingImpactSummary'
import PackagingImpactProductsTable from '../../components/packaging/PackagingImpactProductsTable'
import PackagingImpactSelectedTable from '../../components/packaging/PackagingImpactSelectedTable'
import { exportImpact, fetchCodeOptions, fetchImpact } from '../../api/packaging-cost'
import type { PackagingCodeOption, PackagingImpactRequest } from '../../api/packaging-cost-types'
import { useDebouncedValue } from '../../hooks/use-debounced-value'
import { useLatestQuery } from '../../hooks/use-latest-query'
import { impactPrintHref } from '../../utils/packaging-print'
import { nextSort, sortCodeOptions } from '../../utils/packaging-query'
import { EMPTY_IMPACT_FILTERS, countImpactFilters, impactFiltersToRequest } from '../../utils/packaging-impact-filters'
import type { ImpactAdvancedFilters } from '../../utils/packaging-impact-filters'
import '../../components/packaging/packaging.css'

/** Chỉ gửi giả định của mã còn đang chọn — bỏ mã khỏi danh sách là bỏ luôn giá giả định của nó. */
function pickAssumed(codes: string[], assumed: Record<string, number>): Record<string, number> | undefined {
  const picked = Object.fromEntries(codes.filter((c) => assumed[c] != null).map((c) => [c, assumed[c]]))
  return Object.keys(picked).length ? picked : undefined
}

/**
 * Màn TÁC ĐỘNG TĂNG GIÁ BAO BÌ: chọn một hoặc nhiều mã chai / nắp / nhãn / nhãn thùng / thùng → bảng mã đã chọn
 * (giá cũ, mới, ô giá giả định), ba thẻ số liệu, và bảng mọi sản phẩm dùng ít nhất một mã đó với chi phí bao bì /chai,
 * /thùng cũ và mới. Giá giả định trễ 400 ms rồi mới tính lại; bảng sản phẩm phân trang / tìm / lọc nâng cao / xếp tại MÁY CHỦ.
 */
export default function PackagingImpact() {
  const { can } = useAuth()
  const [options, setOptions] = useState<PackagingCodeOption[]>([])
  const [optionsLoading, setOptionsLoading] = useState(true)
  const [codes, setCodes] = useState<string[]>([])
  const [assumed, setAssumed] = useState<Record<string, number>>({})
  const [range, setRange] = useState({ from: '', to: '' })
  const [keyword, setKeyword] = useState('')
  const [filters, setFilters] = useState<ImpactAdvancedFilters>(EMPTY_IMPACT_FILTERS)
  const [sortBy, setSortBy] = useState('')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)
  const [exporting, setExporting] = useState(false)
  const debouncedAssumed = useDebouncedValue(assumed, 400)
  const query = useDebouncedValue(keyword, 250).trim()
  const productsRef = useRef<HTMLDivElement>(null)
  /** Đang lọc bằng từ khóa / lọc nâng cao → thẻ "Sản phẩm bị ảnh hưởng" ghi "Đang lọc: x / M". */
  const filtersActive = keyword !== '' || countImpactFilters(filters) > 0

  useEffect(() => {
    fetchCodeOptions().then((d) => setOptions(sortCodeOptions(d)))
      .catch(() => toast.error('Không nạp được danh sách mã bao bì'))
      .finally(() => setOptionsLoading(false))
  }, [])

  /** Phần thân dùng chung cho tính toán và Xuất Excel (cùng bộ lọc + thứ tự); chưa kèm trang. */
  const filterBody = useMemo<PackagingImpactRequest>(() => ({
    codes,
    assumed_prices: pickAssumed(codes, debouncedAssumed),
    date_from: range.from || undefined,
    date_to: range.to || undefined,
    q: query || undefined,
    ...impactFiltersToRequest(filters),
    //  Chưa chọn cột xếp thì KHÔNG gửi — máy chủ xếp mặc định theo mã HH.
    ...(sortBy ? { sort_by: sortBy, sort_dir: sortDir } : {}),
  }), [codes, debouncedAssumed, range, query, filters, sortBy, sortDir])
  const body = useMemo<PackagingImpactRequest>(() => ({ ...filterBody, page, page_size: pageSize }), [filterBody, page, pageSize])
  const impact = useLatestQuery(() => fetchImpact(body), JSON.stringify(body), codes.length > 0)
  const data = codes.length ? impact.data : null

  //  Đổi danh sách mã / khoảng ngày / từ khóa / cột xếp / cỡ trang → về trang 1 (đổi giá giả định thì KHÔNG: người xem không bị nhảy trang).
  const changeCodes = (next: string[]) => { setCodes(next); setPage(1) }
  const changeKeyword = (v: string) => { setKeyword(v); setPage(1) }
  const changeFilters = (next: ImpactAdvancedFilters) => { setFilters(next); setPage(1) }
  const resetFilters = () => { setKeyword(''); setFilters(EMPTY_IMPACT_FILTERS); setPage(1) }
  const changeSort = (key: string) => { const s = nextSort(sortBy, sortDir, key); setSortBy(s.by); setSortDir(s.dir); setPage(1) }
  const changeAssumed = useCallback((code: string, price: number | null) => {
    setAssumed((prev) => {
      const next = { ...prev }
      if (price == null) delete next[code]
      else next[code] = price
      return next
    })
  }, [])
  /** Bấm thẻ "Tăng nhiều nhất /thùng": xếp bảng sản phẩm theo chênh /thùng giảm dần rồi cuộn tới bảng. */
  const showTopIncrease = () => {
    setSortBy('diff_carton'); setSortDir('desc'); setPage(1)
    productsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
  const removeCode = useCallback((code: string) => { setCodes((prev) => prev.filter((c) => c !== code)); setPage(1) }, [])

  async function exportExcel() {
    if (exporting) return
    setExporting(true)
    try {
      //  Xuất theo giá giả định ĐANG GÕ, không đợi nhịp trễ — người bấm Xuất muốn đúng số trên ô.
      await exportImpact({ ...filterBody, assumed_prices: pickAssumed(codes, assumed) })
    } catch (e: any) {
      toast.error(e?.message || 'Không xuất được tệp Excel')
    } finally {
      setExporting(false)
    }
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <h2 className="page-title" style={{ margin: 0 }}>Tác động tăng giá bao bì</h2>
          <div className="pkg-hint">Chọn mã bao bì, nhập giá giả định để xem sản phẩm nào tăng chi phí bao nhiêu trước khi NCC chốt giá.</div>
        </div>
        <div style={{ width: 280 }}>
          <DateRangePicker block value={range} placeholder="Khoảng ngày tính min – max"
            onChange={(v) => { setRange(v); setPage(1) }} />
        </div>
        {/* In = xem (quyền đọc). Mở tab mới, mã + giá giả định ĐANG GÕ + từ khóa / lọc nâng cao / cột xếp của bảng; trang in tự nạp đủ mọi sản phẩm. */}
        {can('packaging_cost', 'read') && (
          <button className="btn outline" disabled={!codes.length} title={codes.length ? undefined : 'Chọn ít nhất một mã để in'}
            onClick={() => window.open(impactPrintHref({ ...filterBody, assumed_prices: pickAssumed(codes, assumed) }), '_blank')}>
            <i className="ti ti-printer" />In
          </button>
        )}
        {can('packaging_cost', 'export') && (
          <button className="btn outline" disabled={!codes.length || exporting} onClick={exportExcel}>
            <i className="ti ti-file-spreadsheet" />{exporting ? 'Đang xuất…' : 'Xuất Excel'}
          </button>
        )}
      </div>

      <div className="card pkg-card" style={{ marginBottom: 14, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <PackagingCodePicker options={options} value={codes} onChange={changeCodes} loading={optionsLoading} />
        {codes.length === 0 ? (
          <div className="pkg-hint">
            Bấm vào ô trên để chọn một hoặc nhiều mã. Gõ tên nhóm (<b>chai</b>, <b>nắp</b>, <b>nhãn</b>…) rồi bấm <b>Chọn tất cả</b> để chọn cả nhóm.
          </div>
        ) : (
          <>
            <PackagingImpactSummary kpis={data?.kpis} filteredTotal={filtersActive ? data?.products_total : undefined}
              onShowTopIncrease={showTopIncrease} />
            <PackagingImpactSelectedTable rows={data?.selected} loading={impact.loading} failed={impact.failed}
              assumed={assumed} onAssumedChange={changeAssumed} onRemove={removeCode} />
          </>
        )}
      </div>

      {codes.length > 0 && (
        <div ref={productsRef} className="card pkg-card" style={{ scrollMarginTop: 12 }}>
          <PackagingImpactProductsTable rows={data?.products} total={data?.products_total ?? 0} affected={data?.kpis.affected_products}
            loading={impact.loading} failed={impact.failed}
            keyword={keyword} onKeyword={changeKeyword} filters={filters} filterCount={countImpactFilters(filters)}
            onFilters={changeFilters} onResetFilters={resetFilters} sortBy={sortBy} sortDir={sortDir} onSort={changeSort}
            page={page} pageSize={pageSize} onPage={(p, s) => { setPage(p); setPageSize(s) }} />
        </div>
      )}
    </div>
  )
}
