import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

const LINE_APPROVE_COLOR: Record<string, string> = {
  'Chờ duyệt': '#d97706',
  'Đã duyệt': '#16a34a',
  'Không duyệt': '#b91c1c',
  'Thiếu thông tin': '#ea580c',
}

function lineApproveBadge(st: string) {
  const c = LINE_APPROVE_COLOR[st] || '#64748b'
  return (
    <span className="badge" style={{ background: `${c}1a`, color: c, border: `1px solid ${c}55` }}>
      {st || '—'}
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
  date_from: string
  date_to: string
}

const EMPTY_FILTERS: FiltersState = {
  kind: '', line_approve: '', item_group: '', supplier: '', code: '', nspt: '', date_from: '', date_to: '',
}

const SUMMARY_KEYS: (keyof SummaryMap)[] = ['Chờ duyệt', 'Đã duyệt', 'Không duyệt', 'Thiếu thông tin']

export default function SurveyReport() {
  const [items, setItems] = useState<SurveyReportItem[]>([])
  const [total, setTotal] = useState(0)
  const [summary, setSummary] = useState<SummaryMap>({ 'Chờ duyệt': 0, 'Đã duyệt': 0, 'Không duyệt': 0, 'Thiếu thông tin': 0 })
  const [filters, setFilters] = useState<FiltersState>(EMPTY_FILTERS)
  const [draft, setDraft] = useState<FiltersState>(EMPTY_FILTERS)
  const [page, setPage] = useState(1)
  const [busy, setBusy] = useState(false)
  const [itemGroups, setItemGroups] = useState<string[]>([])

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
      if (f.date_from) params.date_from = f.date_from
      if (f.date_to) params.date_to = f.date_to
      const r = await api.get('/api/survey-report/lines', { params })
      const d = r.data.data || {}
      setItems(d.items || [])
      setTotal(d.total || 0)
      setSummary(d.summary || { 'Chờ duyệt': 0, 'Đã duyệt': 0, 'Không duyệt': 0, 'Thiếu thông tin': 0 })
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => { load(filters, page) }, [filters, page])

  function applyFilters() {
    setFilters({ ...draft })
    setPage(1)
  }

  function resetFilters() {
    setDraft(EMPTY_FILTERS)
    setFilters(EMPTY_FILTERS)
    setPage(1)
  }

  function toggleStatusCard(st: string) {
    const newApprove = filters.line_approve === st ? '' : st
    const newFilters = { ...filters, line_approve: newApprove }
    setFilters(newFilters)
    setDraft((d) => ({ ...d, line_approve: newApprove }))
    setPage(1)
  }

  function exportCsv() {
    if (items.length === 0) { alert('Không có dữ liệu để xuất.'); return }
    const headers = ['Mã phiếu', 'Loại', 'Nội dung', 'Phân loại', 'NSPT', 'Ngày', 'Trạng thái duyệt', 'Ghi chú duyệt']
    const rows = items.map((it) => [
      it.survey_code, KIND_LABEL[it.kind] || it.kind, it.content || '',
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

  const CARD_STYLE_BASE: React.CSSProperties = { flex: 1, minWidth: 150, padding: '14px 18px', cursor: 'pointer', borderRadius: 10, border: '2px solid transparent', transition: 'all .15s' }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Báo cáo khảo sát</h2>
        <button className="btn ghost" onClick={exportCsv}><i className="ti ti-download" />Xuất CSV</button>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
        {SUMMARY_KEYS.map((st) => {
          const c = LINE_APPROVE_COLOR[st] || '#64748b'
          const active = filters.line_approve === st
          return (
            <div key={st} className="card" onClick={() => toggleStatusCard(st)}
              style={{ ...CARD_STYLE_BASE, borderColor: active ? c : 'transparent', boxShadow: active ? `0 0 0 1px ${c}55` : undefined }}>
              <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>{st}</div>
              <div style={{ fontSize: 22, fontWeight: 700, color: c }}>{summary[st]}</div>
            </div>
          )
        })}
      </div>

      {/* Filters */}
      <div className="card" style={{ padding: '14px 18px', marginBottom: 14 }}>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          <div>
            <label style={{ fontSize: 12, color: 'var(--muted)', display: 'block', marginBottom: 3 }}>Loại dòng</label>
            <select value={draft.kind} onChange={(e) => setDraft((d) => ({ ...d, kind: e.target.value }))} style={{ height: 36, borderRadius: 8, border: '1px solid #E9EDF7', padding: '0 10px', fontSize: 13 }}>
              <option value="">Tất cả</option>
              <option value="supplier">NCC</option>
              <option value="product">Sản phẩm</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: 12, color: 'var(--muted)', display: 'block', marginBottom: 3 }}>Trạng thái dòng</label>
            <select value={draft.line_approve} onChange={(e) => setDraft((d) => ({ ...d, line_approve: e.target.value }))} style={{ height: 36, borderRadius: 8, border: '1px solid #E9EDF7', padding: '0 10px', fontSize: 13 }}>
              <option value="">Tất cả</option>
              <option value="Chờ duyệt">Chờ duyệt</option>
              <option value="Đã duyệt">Đã duyệt</option>
              <option value="Không duyệt">Không duyệt</option>
              <option value="Thiếu thông tin">Thiếu thông tin</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: 12, color: 'var(--muted)', display: 'block', marginBottom: 3 }}>Phân loại</label>
            <select value={draft.item_group} onChange={(e) => setDraft((d) => ({ ...d, item_group: e.target.value }))} style={{ height: 36, borderRadius: 8, border: '1px solid #E9EDF7', padding: '0 10px', fontSize: 13 }}>
              <option value="">Tất cả</option>
              {itemGroups.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontSize: 12, color: 'var(--muted)', display: 'block', marginBottom: 3 }}>NCC</label>
            <input value={draft.supplier} placeholder="Mã / tên NCC" onChange={(e) => setDraft((d) => ({ ...d, supplier: e.target.value }))} style={{ height: 36, borderRadius: 8, border: '1px solid #E9EDF7', padding: '0 10px', fontSize: 13, width: 130 }} />
          </div>
          <div>
            <label style={{ fontSize: 12, color: 'var(--muted)', display: 'block', marginBottom: 3 }}>Mã phiếu</label>
            <input value={draft.code} placeholder="Mã khảo sát" onChange={(e) => setDraft((d) => ({ ...d, code: e.target.value }))} style={{ height: 36, borderRadius: 8, border: '1px solid #E9EDF7', padding: '0 10px', fontSize: 13, width: 130 }} />
          </div>
          <div>
            <label style={{ fontSize: 12, color: 'var(--muted)', display: 'block', marginBottom: 3 }}>NSPT</label>
            <input value={draft.nspt} placeholder="NSPT" onChange={(e) => setDraft((d) => ({ ...d, nspt: e.target.value }))} style={{ height: 36, borderRadius: 8, border: '1px solid #E9EDF7', padding: '0 10px', fontSize: 13, width: 110 }} />
          </div>
          <div>
            <label style={{ fontSize: 12, color: 'var(--muted)', display: 'block', marginBottom: 3 }}>Từ ngày</label>
            <input type="date" value={draft.date_from} onChange={(e) => setDraft((d) => ({ ...d, date_from: e.target.value }))} style={{ height: 36, borderRadius: 8, border: '1px solid #E9EDF7', padding: '0 8px', fontSize: 13 }} />
          </div>
          <div>
            <label style={{ fontSize: 12, color: 'var(--muted)', display: 'block', marginBottom: 3 }}>Đến ngày</label>
            <input type="date" value={draft.date_to} onChange={(e) => setDraft((d) => ({ ...d, date_to: e.target.value }))} style={{ height: 36, borderRadius: 8, border: '1px solid #E9EDF7', padding: '0 8px', fontSize: 13 }} />
          </div>
          <button className="btn" disabled={busy} onClick={applyFilters}>Lọc</button>
          <button className="btn ghost" onClick={resetFilters}>Xóa lọc</button>
        </div>
      </div>

      {/* Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div className="items-scroll">
          <table className="items-table" style={{ minWidth: 900 }}>
            <thead>
              <tr>
                <th style={{ width: 130, textAlign: 'left' }}>Mã phiếu</th>
                <th style={{ width: 70, textAlign: 'center' }}>Loại</th>
                <th style={{ textAlign: 'left', minWidth: 200 }}>Nội dung</th>
                <th style={{ width: 130, textAlign: 'left' }}>Phân loại</th>
                <th style={{ width: 120, textAlign: 'left' }}>NSPT</th>
                <th style={{ width: 100, textAlign: 'center' }}>Ngày</th>
                <th style={{ width: 130, textAlign: 'center' }}>Trạng thái duyệt</th>
                <th style={{ minWidth: 160, textAlign: 'left' }}>Ghi chú duyệt</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={`${it.survey_id}-${it.kind}-${it.line_id}`}>
                  <td>
                    <Link to={`/surveys/${it.survey_id}`} style={{ color: 'var(--teal)', fontWeight: 500, textDecoration: 'none' }}>
                      {it.survey_code}
                    </Link>
                  </td>
                  <td style={{ textAlign: 'center' }}>{kindBadge(it.kind)}</td>
                  <td style={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={it.content}>{it.content || '—'}</td>
                  <td>{it.item_group || '—'}</td>
                  <td>{it.nspt || '—'}</td>
                  <td style={{ textAlign: 'center' }}>{it.date || '—'}</td>
                  <td style={{ textAlign: 'center' }}>{lineApproveBadge(it.line_approve)}</td>
                  <td style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={it.line_approve_note}>{it.line_approve_note || '—'}</td>
                </tr>
              ))}
              {items.length === 0 && (
                <tr>
                  <td colSpan={8} style={{ textAlign: 'center', color: '#999', padding: 24 }}>
                    {busy ? 'Đang tải...' : 'Không có dữ liệu'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 18px', borderTop: '1px solid var(--border)' }}>
            <span style={{ fontSize: 13, color: 'var(--muted)' }}>
              Tổng {total} dòng · Trang {page}/{totalPages}
            </span>
            <div style={{ display: 'flex', gap: 6 }}>
              <button className="btn ghost" disabled={page <= 1} onClick={() => setPage(1)} style={{ padding: '0 10px', height: 32, fontSize: 12 }}>«</button>
              <button className="btn ghost" disabled={page <= 1} onClick={() => setPage(page - 1)} style={{ padding: '0 10px', height: 32, fontSize: 12 }}>‹</button>
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const start = Math.max(1, Math.min(page - 2, totalPages - 4))
                const pg = start + i
                if (pg > totalPages) return null
                return (
                  <button key={pg} className={'btn' + (pg === page ? '' : ' ghost')} onClick={() => setPage(pg)} style={{ padding: '0 10px', height: 32, fontSize: 12, minWidth: 32 }}>{pg}</button>
                )
              })}
              <button className="btn ghost" disabled={page >= totalPages} onClick={() => setPage(page + 1)} style={{ padding: '0 10px', height: 32, fontSize: 12 }}>›</button>
              <button className="btn ghost" disabled={page >= totalPages} onClick={() => setPage(totalPages)} style={{ padding: '0 10px', height: 32, fontSize: 12 }}>»</button>
            </div>
          </div>
        )}
        {totalPages <= 1 && total > 0 && (
          <div style={{ padding: '8px 18px', borderTop: '1px solid var(--border)', fontSize: 13, color: 'var(--muted)' }}>
            Tổng {total} dòng
          </div>
        )}
      </div>
    </div>
  )
}
