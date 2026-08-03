import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import Pagination from '../components/Pagination'
import { toast } from '../components/toast'
import { useResizableColumns, ResizeHandle } from '../hooks/useResizableColumns'

const LINE_APPROVE_COLOR: Record<string, string> = {
  'Chờ duyệt': '#d97706',
  'Đã duyệt': '#16a34a',
  'Không duyệt': '#b91c1c',
  'Thiếu thông tin': '#ea580c',
}

const STATUS_COLORS: Record<string, { main: string; bg: string; icon: string }> = {
  'Chờ duyệt': { main: '#d97706', bg: 'rgba(217,119,6,0.08)', icon: 'ti-clock' },
  'Đã duyệt': { main: '#16a34a', bg: 'rgba(22,163,74,0.08)', icon: 'ti-circle-check' },
  'Không duyệt': { main: '#b91c1c', bg: 'rgba(185,28,28,0.08)', icon: 'ti-circle-x' },
  'Thiếu thông tin': { main: '#ea580c', bg: 'rgba(234,88,12,0.08)', icon: 'ti-alert-circle' },
}

function lineApproveBadge(st: string) {
  const c = LINE_APPROVE_COLOR[st] || '#64748b'
  return (
    <span className="badge" style={{ background: `${c}1a`, color: c, border: `1px solid ${c}55` }}>
      {st || ''}
    </span>
  )
}

const KIND_LABEL: Record<string, string> = { supplier: 'NCC', product: 'SP' }

function kindBadge(kind: string) {
  const isSupplier = kind === 'supplier'
  return (
    <span className="badge" style={{ background: isSupplier ? '#e0f2fe' : '#f0fdf4', color: isSupplier ? '#0369a1' : '#15803d', border: `1px solid ${isSupplier ? '#bae6fd' : '#bbf7d0'}` }}>
      {KIND_LABEL[kind] || kind}
    </span>
  )
}

const PAGE_SIZE = 20

interface SurveyReportItem {
  survey_id: number
  survey_code: string
  kind: string
  line_id: number
  content: string
  supplier_code: string
  item_group: string
  nspt: string
  item_code: string
  main_content: string
  date: string
  line_approve: string
  line_approve_note: string
  survey_status: string
}

interface SummaryMap {
  'Chờ duyệt': number
  'Đã duyệt': number
  'Không duyệt': number
  'Thiếu thông tin': number
}

interface FiltersState {
  kind: string
  line_approve: string
  item_group: string
  supplier: string
  code: string
  nspt: string
  item_code: string
  main_content: string
  date_from: string
  date_to: string
}

const EMPTY_FILTERS: FiltersState = {
  kind: '', line_approve: '', item_group: '', supplier: '', code: '', nspt: '',
  item_code: '', main_content: '', date_from: '', date_to: '',
}

const SUMMARY_KEYS: (keyof SummaryMap)[] = ['Chờ duyệt', 'Đã duyệt', 'Không duyệt', 'Thiếu thông tin']

export default function SurveyReport() {
  const [items, setItems] = useState<SurveyReportItem[]>([])
  const [total, setTotal] = useState(0)
  const [summary, setSummary] = useState<SummaryMap>({ 'Chờ duyệt': 0, 'Đã duyệt': 0, 'Không duyệt': 0, 'Thiếu thông tin': 0 })
  const [filters, setFilters] = useState<FiltersState>(EMPTY_FILTERS)
  const [debouncedFilters, setDebouncedFilters] = useState<FiltersState>(EMPTY_FILTERS)
  const [page, setPage] = useState(1)
  const [busy, setBusy] = useState(false)
  const [itemGroups, setItemGroups] = useState<string[]>([])
  const [sortBy, setSortBy] = useState('')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const { startResize, thStyle } = useResizableColumns('colw:survey-report')

  function handleSort(field: string) {
    if (sortBy === field) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortBy(field); setSortDir('asc') }
    setPage(1)
  }
  const arrow = (f: string) => (sortBy === f ? (sortDir === 'asc' ? ' ▲' : ' ▼') : ' ↕')

  function hCol(idx: number, field: string, label: string,
                opts: { w?: number; minW?: number; center?: boolean; sortable?: boolean } = {}) {
    const sortable = opts.sortable !== false
    const style: React.CSSProperties = {
      position: 'relative', paddingRight: 12,
      ...(opts.w ? { width: opts.w } : {}),
      ...(opts.minW ? { minWidth: opts.minW } : {}),
      ...(opts.center ? { textAlign: 'center' } : { textAlign: 'left' }),
      ...(sortable ? { cursor: 'pointer', userSelect: 'none' } : {}),
      ...thStyle(idx),
    }
    return (
      <th style={style} onClick={sortable ? () => handleSort(field) : undefined}>
        {label}{sortable ? arrow(field) : ''}
        <ResizeHandle onMouseDown={(e) => startResize(idx, e)} />
      </th>
    )
  }

  useEffect(() => {
    api.get('/api/item-groups', { params: { page_size: 500 } })
      .then((r) => setItemGroups(r.data.data.items.map((x: any) => x.name)))
      .catch(() => {})
  }, [])

  async function load(f: FiltersState, pg: number) {
    setBusy(true)
    try {
      const params: Record<string, any> = { page: pg, page_size: PAGE_SIZE }
      if (f.kind) params.kind = f.kind
      if (f.line_approve) params.line_approve = f.line_approve
      if (f.item_group) params.item_group = f.item_group
      if (f.supplier) params.supplier = f.supplier
      if (f.code) params.code = f.code
      if (f.nspt) params.nspt = f.nspt
      if (f.item_code) params.item_code = f.item_code
      if (f.main_content) params.main_content = f.main_content
      if (f.date_from) params.date_from = f.date_from
      if (f.date_to) params.date_to = f.date_to
      if (sortBy) { params.sort_by = sortBy; params.sort_dir = sortDir }
      const r = await api.get('/api/survey-report/lines', { params })
      const d = r.data.data || {}
      setItems(d.items || [])
      setTotal(d.total || 0)
      setSummary(d.summary || { 'Chờ duyệt': 0, 'Đã duyệt': 0, 'Không duyệt': 0, 'Thiếu thông tin': 0 })
    } finally {
      setBusy(false)
    }
  }

  // Debounce filter updates to automatically reload the page
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedFilters(filters)
    }, 300)
    return () => clearTimeout(handler)
  }, [filters])

  useEffect(() => {
    load(debouncedFilters, page)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedFilters, page, sortBy, sortDir])

  function resetFilters() {
    setFilters(EMPTY_FILTERS)
    setPage(1)
  }

  function toggleStatusCard(st: string) {
    const newApprove = filters.line_approve === st ? '' : st
    setFilters((f) => ({ ...f, line_approve: newApprove }))
    setPage(1)
  }

  function exportCsv() {
    if (items.length === 0) { toast.error('Không có dữ liệu để xuất.'); return }
    const headers = ['Mã phiếu', 'Loại', 'Nội dung', 'Mã hàng', 'Nội dung chính', 'Phân loại', 'NSPT', 'Ngày', 'Trạng thái duyệt', 'Ghi chú duyệt']
    const rows = items.map((it) => [
      it.survey_code, KIND_LABEL[it.kind] || it.kind, it.content || '',
      it.item_code || '', it.main_content || '',
      it.item_group || '', it.nspt || '', it.date || '',
      it.line_approve || '', it.line_approve_note || '',
    ])
    const csv = [headers, ...rows].map((row) => row.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(',')).join('\n')
    const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a'); a.href = url; a.download = `bao-cao-khao-sat-${new Date().toISOString().slice(0, 10)}.csv`
    a.click(); URL.revokeObjectURL(url)
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  const CARD_STYLE_BASE: React.CSSProperties = {
    flex: '1 1 200px',
    padding: '16px 20px',
    cursor: 'pointer',
    borderRadius: 16,
    border: '1px solid #E9EDF7',
    transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#fff',
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Báo cáo khảo sát</h2>
        <button className="btn ghost" onClick={exportCsv}><i className="ti ti-download" />Xuất CSV</button>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
        {SUMMARY_KEYS.map((st) => {
          const sc = STATUS_COLORS[st] || { main: '#64748b', bg: 'rgba(100,116,139,0.08)', icon: 'ti-info-circle' }
          const active = filters.line_approve === st
          return (
            <div key={st} className="card status-summary-card" onClick={() => toggleStatusCard(st)}
              style={{ 
                ...CARD_STYLE_BASE, 
                borderColor: active ? sc.main : '#E9EDF7', 
                boxShadow: active ? `0 10px 20px ${sc.bg}, 0 0 0 3px ${sc.bg}` : 'none',
                transform: active ? 'translateY(-2px)' : 'none',
              }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--muted)', marginBottom: 4 }}>{st}</div>
                <div style={{ fontSize: 26, fontWeight: 800, color: sc.main }}>{summary[st]}</div>
              </div>
              <div className="icon-container" style={{
                width: 44,
                height: 44,
                borderRadius: 12,
                backgroundColor: sc.bg,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: sc.main,
                fontSize: 22,
                transition: 'transform 0.2s ease',
              }}>
                <i className={`ti ${sc.icon}`} />
              </div>
            </div>
          )
        })}
      </div>

      {/* Filters */}
      <div className="card" style={{ padding: 18, marginBottom: 14 }}>
        <div className="toolbar" style={{ marginBottom: 0 }}>
          <div className="toolbar-filter-item">
            <label>Loại dòng</label>
            <select value={filters.kind} onChange={(e) => { setFilters((d) => ({ ...d, kind: e.target.value })); setPage(1); }}>
              <option value="">Tất cả</option>
              <option value="supplier">NCC</option>
              <option value="product">Sản phẩm</option>
            </select>
          </div>
          <div className="toolbar-filter-item">
            <label>Trạng thái dòng</label>
            <select value={filters.line_approve} onChange={(e) => { setFilters((d) => ({ ...d, line_approve: e.target.value })); setPage(1); }}>
              <option value="">Tất cả</option>
              <option value="Chờ duyệt">Chờ duyệt</option>
              <option value="Đã duyệt">Đã duyệt</option>
              <option value="Không duyệt">Không duyệt</option>
              <option value="Thiếu thông tin">Thiếu thông tin</option>
            </select>
          </div>
          <div className="toolbar-filter-item">
            <label>Phân loại</label>
            <select value={filters.item_group} onChange={(e) => { setFilters((d) => ({ ...d, item_group: e.target.value })); setPage(1); }}>
              <option value="">Tất cả</option>
              {itemGroups.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>
          <div className="toolbar-filter-item">
            <label>NCC</label>
            <input value={filters.supplier} placeholder="Mã / tên NCC" onChange={(e) => { setFilters((d) => ({ ...d, supplier: e.target.value })); setPage(1); }} />
          </div>
          <div className="toolbar-filter-item">
            <label>Mã phiếu</label>
            <input value={filters.code} placeholder="Mã khảo sát" onChange={(e) => { setFilters((d) => ({ ...d, code: e.target.value })); setPage(1); }} />
          </div>
          <div className="toolbar-filter-item">
            <label>NSPT</label>
            <input value={filters.nspt} placeholder="NSPT" onChange={(e) => { setFilters((d) => ({ ...d, nspt: e.target.value })); setPage(1); }} />
          </div>
          <div className="toolbar-filter-item">
            <label>Mã hàng</label>
            <input value={filters.item_code} placeholder="Mã hàng hóa" onChange={(e) => { setFilters((d) => ({ ...d, item_code: e.target.value })); setPage(1); }} />
          </div>
          <div className="toolbar-filter-item">
            <label>Nội dung chính</label>
            <input value={filters.main_content} placeholder="Tìm nội dung chính" onChange={(e) => { setFilters((d) => ({ ...d, main_content: e.target.value })); setPage(1); }} />
          </div>
          <div className="toolbar-filter-item">
            <label>Từ ngày</label>
            <input type="date" value={filters.date_from} onChange={(e) => { setFilters((d) => ({ ...d, date_from: e.target.value })); setPage(1); }} />
          </div>
          <div className="toolbar-filter-item">
            <label>Đến ngày</label>
            <input type="date" value={filters.date_to} onChange={(e) => { setFilters((d) => ({ ...d, date_to: e.target.value })); setPage(1); }} />
          </div>
          
          {Object.values(filters).some((v) => v) && (
            <button className="btn ghost" onClick={resetFilters} style={{ height: 40, borderRadius: 12 }}>
              Xóa lọc
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="items-scroll">
          <table className="items-table" style={{ minWidth: 900 }}>
            <thead>
              <tr>
                {hCol(0, '', 'STT', { w: 48, center: true, sortable: false })}
                {hCol(1, 'survey_code', 'Mã phiếu', { w: 130 })}
                {hCol(2, 'kind', 'Loại', { w: 70, center: true })}
                {hCol(3, 'content', 'Nội dung', { minW: 200 })}
                {hCol(4, 'item_code', 'Mã hàng', { w: 120 })}
                {hCol(5, 'item_group', 'Phân loại', { w: 130 })}
                {hCol(6, 'nspt', 'NSPT', { w: 120 })}
                {hCol(7, 'date', 'Ngày', { w: 100, center: true })}
                {hCol(8, 'line_approve', 'Trạng thái duyệt', { w: 130, center: true })}
                {hCol(9, 'line_approve_note', 'Ghi chú duyệt', { minW: 160 })}
              </tr>
            </thead>
            <tbody>
              {items.map((it, i) => (
                <tr key={`${it.survey_id}-${it.kind}-${it.line_id}`}>
                  <td style={{ textAlign: 'center', color: 'var(--muted)' }}>{(page - 1) * PAGE_SIZE + i + 1}</td>
                  <td>
                    <Link to={`/surveys/${it.survey_id}`} style={{ color: 'var(--teal)', fontWeight: 500, textDecoration: 'none' }}>
                      {it.survey_code}
                    </Link>
                  </td>
                  <td style={{ textAlign: 'center' }}>{kindBadge(it.kind)}</td>
                  <td style={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={it.content}>{it.content || ''}</td>
                  <td title={it.main_content}>{it.item_code || ''}</td>
                  <td>{it.item_group || ''}</td>
                  <td>{it.nspt || ''}</td>
                  <td style={{ textAlign: 'center' }}>{it.date || ''}</td>
                  <td style={{ textAlign: 'center' }}>{lineApproveBadge(it.line_approve)}</td>
                  <td style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={it.line_approve_note}>{it.line_approve_note || ''}</td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', color: '#999', padding: 24 }}>
                    {busy ? 'Đang tải...' : 'Không có dữ liệu'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {total > 0 && (
          <div style={{ padding: '10px 18px', borderTop: '1px solid var(--border)' }}>
            <Pagination page={page} pageSize={PAGE_SIZE} total={total} hideSize onChange={(p) => setPage(p)} />
          </div>
        )}
      </div>
    </div>
  )
}
