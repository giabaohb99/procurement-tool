import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api/client'
import { askConfirm } from './confirm'
import { toast } from './toast'
import { useAuth } from '../auth/AuthContext'
import { fmtDateStr } from '../utils/datetime'
import SearchSelect from './SearchSelect'
import DateInput from './DateInput'
import {
  COMMON_ROW_ID, REPORT_DOC_DOING, REPORT_DOC_DONE, REPORT_DOC_IDLE, REPORT_DOC_STATUS_BADGE,
  REPORT_DOC_STATUS_LABELS, REPORT_FILTER_ALL, REPORT_STATUS_FILTER_ALL,
  currentReportPhaseId, expiryTone, filterReportDocs, isReportDocDone, isReportDocLocked,
  matchReportDoc, nameInitials, nearestExpiry, pendingDepends, reportDocsById, reportPercent,
  trackingMarkers,
  type SurveyReportDoc, type SurveyReportDocPayload, type SurveyReportItem, type SurveyReportPhase,
  type SurveyRequestReport,
} from '../utils/surveyReportHelpers'

/**
 * bao-CR-390: khối «Báo cáo thực hiện» trên chi tiết YCBG — bản v1 (`frontend/`).
 * Chép hành vi của `frontend-v2/.../survey-report/survey-report-card.tsx` sang phong
 * cách v1 (CSS thuần `.srp-*`, tabler icons, askConfirm/toast). Backend dùng chung,
 * mọi mutation trả về NGUYÊN KHỐI mới nên state chỉ thay một lượt, không refetch.
 *
 * Người có `survey_request.process` mới sửa được (`canEdit`); ai xem được phiếu thì
 * xem được báo cáo — phiếu CHƯA có báo cáo thì khối tự ẩn với người chỉ xem.
 */

type ViewMode = 'phase' | 'item'
const VIEW_KEY = 'erp.survey-report.view'
const EXPIRY_SOON_DAYS = 7

type Props = {
  surveyRequestId: number
  canEdit: boolean
  /** Gọi sau mỗi lần ghi — cha nạp lại Lịch sử thao tác. */
  onChanged?: () => void
}

type DocDialogState = { doc: SurveyReportDoc | null; defaults?: Partial<SurveyReportDocPayload> }
type ItemDialogState = { item: SurveyReportItem | null }
type PhaseDialogState = { phase: SurveyReportPhase | null }

function todayIso(): string {
  const d = new Date()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${mm}-${dd}`
}

function isLink(text: string): boolean {
  return /^https?:\/\//i.test(text.trim())
}

function readViewMode(): ViewMode {
  try { return localStorage.getItem(VIEW_KEY) === 'item' ? 'item' : 'phase' } catch { return 'phase' }
}

export default function SurveyReportCard({ surveyRequestId, canEdit, onChanged }: Props) {
  const { user } = useAuth()
  const base = `/api/survey-requests/${surveyRequestId}/report`

  const [report, setReport] = useState<SurveyRequestReport | null>(null)
  const [loaded, setLoaded] = useState(false)
  const [busy, setBusy] = useState(false)
  const [open, setOpen] = useState(false)
  const [viewMode, setViewModeState] = useState<ViewMode>(readViewMode)
  const [itemFilter, setItemFilter] = useState<number>(REPORT_FILTER_ALL)
  const [statusFilter, setStatusFilter] = useState<number>(REPORT_STATUS_FILTER_ALL)
  const [search, setSearch] = useState('')
  const [collapsedPhases, setCollapsedPhases] = useState<Set<number>>(new Set())
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set())
  const [docDialog, setDocDialog] = useState<DocDialogState | null>(null)
  const [itemDialog, setItemDialog] = useState<ItemDialogState | null>(null)
  const [phaseDialog, setPhaseDialog] = useState<PhaseDialogState | null>(null)

  function setViewMode(mode: ViewMode) {
    setViewModeState(mode)
    try { localStorage.setItem(VIEW_KEY, mode) } catch { /* private mode */ }
  }

  // --- nạp khối ---
  useEffect(() => {
    if (!surveyRequestId) return
    let alive = true
    api.get(base, { _silent: true } as any)
      .then((r) => {
        if (!alive) return
        const data: SurveyRequestReport = r.data.data
        setReport(data)
        // Thẻ gấp mặc định; phiếu chưa có gì thì mở sẵn để người thực hiện thấy nút Khởi tạo
        setOpen(!data.phases.length && !data.docs.length)
      })
      .catch(() => { if (alive) setReport(null) })
      .finally(() => { if (alive) setLoaded(true) })
    return () => { alive = false }
  }, [surveyRequestId])

  /** Chạy một mutation: khối mới thay vào state, toast, báo cha nạp lại lịch sử. */
  async function mutate(run: () => Promise<any>, message?: string | ((next: SurveyRequestReport) => string | null)): Promise<boolean> {
    if (busy) return false
    setBusy(true)
    try {
      const r = await run()
      const next: SurveyRequestReport = r.data.data
      setReport(next)
      const text = typeof message === 'function' ? message(next) : message
      if (text) toast.success(text)
      onChanged?.()
      return true
    } catch {
      return false   // client.ts đã toast lỗi cho request không phải GET
    } finally {
      setBusy(false)
    }
  }

  // --- hành động ---
  const initReport = () => mutate(() => api.post(`${base}/init`), 'Đã khởi tạo báo cáo theo mẫu chung')
  const restoreReport = () => mutate(() => api.post(`${base}/restore`), 'Đã hoàn tác — khôi phục báo cáo thực hiện')
  async function applyTemplate(itemId: number, phaseId: number | null) {
    const before = report?.docs.length ?? 0
    await mutate(
      () => api.post(`${base}/apply-template`, { item_id: itemId, phase_id: phaseId }),
      (next) => {
        const added = next.docs.length - before
        if (added > 0) return `Đã tạo ${added} hồ sơ theo mẫu chung`
        toast.info('Mẫu chung đã có đủ ở đây — không thêm hồ sơ nào')
        return null
      },
    )
  }
  async function deleteReport() {
    const ok = await askConfirm({
      title: 'Xóa báo cáo thực hiện',
      message: 'Xóa toàn bộ giai đoạn, nút dòng hàng và hồ sơ của phiếu này? Có thể hoàn tác ở Lịch sử thao tác.',
      confirmText: 'Xóa', danger: true,
    })
    if (!ok) return
    await mutate(() => api.delete(base), 'Đã xóa báo cáo thực hiện — có thể hoàn tác ở Lịch sử thao tác')
  }
  async function toggleDone(doc: SurveyReportDoc) {
    const status = isReportDocDone(doc) ? REPORT_DOC_DOING : REPORT_DOC_DONE
    await mutate(() => api.patch(`${base}/docs/${doc.id}`, { status }))
  }
  async function saveDoc(docId: number | null, payload: SurveyReportDocPayload): Promise<boolean> {
    return mutate(
      () => docId ? api.patch(`${base}/docs/${docId}`, payload) : api.post(`${base}/docs`, payload),
      'Đã lưu hồ sơ',
    )
  }
  async function deleteDoc(doc: SurveyReportDoc): Promise<boolean> {
    const ok = await askConfirm({ title: 'Xóa hồ sơ', message: `Xóa hồ sơ "${doc.title}"?`, confirmText: 'Xóa', danger: true })
    if (!ok) return false
    return mutate(() => api.delete(`${base}/docs/${doc.id}`), 'Đã xóa hồ sơ')
  }
  async function saveItem(itemId: number | null, name: string): Promise<boolean> {
    return mutate(
      () => itemId ? api.patch(`${base}/items/${itemId}`, { name }) : api.post(`${base}/items`, { name }),
      'Đã lưu nút dòng hàng',
    )
  }
  async function deleteItem(item: SurveyReportItem): Promise<boolean> {
    const ok = await askConfirm({
      title: 'Xóa nút dòng hàng',
      message: `Xóa nút "${item.name}"? Hồ sơ đang gắn nút này sẽ chuyển về Chung, không bị xóa.`,
      confirmText: 'Xóa', danger: true,
    })
    if (!ok) return false
    return mutate(() => api.delete(`${base}/items/${item.id}`), 'Đã xóa nút — hồ sơ gắn nút chuyển về Chung')
  }
  async function savePhase(phaseId: number | null, name: string, location: string): Promise<boolean> {
    return mutate(
      () => phaseId ? api.patch(`${base}/phases/${phaseId}`, { name, location }) : api.post(`${base}/phases`, { name, location }),
      'Đã lưu giai đoạn',
    )
  }
  async function deletePhase(phase: SurveyReportPhase): Promise<boolean> {
    const count = report?.docs.filter((d) => d.phase_id === phase.id).length ?? 0
    if (count > 0) {
      toast.error(`Giai đoạn còn ${count} hồ sơ — chuyển hoặc xóa hồ sơ trước rồi mới xóa giai đoạn`)
      return false
    }
    const ok = await askConfirm({ title: 'Xóa giai đoạn', message: `Xóa giai đoạn "${phase.name}"?`, confirmText: 'Xóa', danger: true })
    if (!ok) return false
    return mutate(() => api.delete(`${base}/phases/${phase.id}`), 'Đã xóa giai đoạn')
  }

  // --- dữ liệu dẫn xuất ---
  const docsById = useMemo(() => (report ? reportDocsById(report) : new Map<number, SurveyReportDoc>()), [report])
  const itemNameById = useMemo(() => {
    const m = new Map<number, string>()
    report?.items.forEach((it) => m.set(it.id, it.name))
    return m
  }, [report])
  const itemName = (id: number) => (id === COMMON_ROW_ID ? '' : itemNameById.get(id) || '')
  const filtering = !!search.trim() || statusFilter !== REPORT_STATUS_FILTER_ALL
  const today = todayIso()

  /** Hồ sơ theo nút đang lọc (dùng cho tóm tắt + tiến độ — cố ý KHÔNG theo từ khóa). */
  const scopedDocs = useMemo(() => (report ? filterReportDocs(report.docs, itemFilter) : []), [report, itemFilter])
  /** Hồ sơ hiện ra dòng: thêm lọc trạng thái + tìm kiếm. */
  const visibleDocs = useMemo(() => scopedDocs.filter((d) =>
    (statusFilter === REPORT_STATUS_FILTER_ALL || d.status === statusFilter) && matchReportDoc(d, search, itemName(d.item_id)),
  ), [scopedDocs, statusFilter, search, itemNameById])

  if (!loaded || !report) return null
  const isEmpty = !report.phases.length && !report.docs.length
  // Người chỉ xem: phiếu chưa có báo cáo thì không bày một thẻ trắng
  if (!canEdit && isEmpty && !report.restorable) return null

  const total = scopedDocs.length
  const done = scopedDocs.filter(isReportDocDone).length
  const percent = reportPercent(scopedDocs)
  const expiry = nearestExpiry(scopedDocs)

  function togglePhase(id: number) {
    setCollapsedPhases((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n })
  }
  function toggleItem(id: number) {
    setExpandedItems((s) => { const n = new Set(s); n.has(id) ? n.delete(id) : n.add(id); return n })
  }
  const allCollapsed = report.phases.length > 0 && report.phases.every((p) => collapsedPhases.has(p.id))
  function toggleAll() {
    if (viewMode === 'item') {
      setExpandedItems(expandedItems.size ? new Set() : new Set([COMMON_ROW_ID, ...report!.items.map((i) => i.id)]))
      return
    }
    setCollapsedPhases(allCollapsed ? new Set() : new Set(report!.phases.map((p) => p.id)))
  }

  const openCreateDoc = (defaults: Partial<SurveyReportDocPayload>) => setDocDialog({ doc: null, defaults })
  const openEditDoc = (doc: SurveyReportDoc) => setDocDialog({ doc })

  // --- một dòng hồ sơ ---
  function renderDoc(doc: SurveyReportDoc, showItemTag: boolean) {
    const isDone = isReportDocDone(doc)
    const locked = isReportDocLocked(doc, docsById)
    const pending = pendingDepends(doc, docsById)
    const tone = expiryTone(doc.expires_at, today)
    const dateTitle = [doc.start_date && `Bắt đầu: ${fmtDateStr(doc.start_date)}`, doc.expires_at && `Hết hiệu lực: ${fmtDateStr(doc.expires_at)}`].filter(Boolean).join(' · ')
    return (
      <div key={doc.id} className={`srp-doc${isDone ? ' done' : ''}${locked ? ' locked' : ''}`}>
        <button
          type="button"
          className={`srp-check${isDone ? ' done' : ''}`}
          disabled={!canEdit || locked || busy}
          title={locked ? 'Đang chờ hồ sơ tiên quyết' : isDone ? 'Đánh dấu Đang làm' : 'Đánh dấu Hoàn thành'}
          onClick={() => toggleDone(doc)}
        >
          <i className="ti ti-check" />
        </button>
        <span className="srp-title" title={doc.title}>{doc.title}</span>
        {showItemTag && (
          <span className="badge gray" style={{ textTransform: 'none', fontSize: 11 }}>{itemName(doc.item_id) || 'Chung'}</span>
        )}
        {doc.required && <span className="badge err">Bắt buộc</span>}
        <span className="srp-desc" title={doc.description}>{doc.description}</span>
        {locked && (
          <i className="ti ti-lock" style={{ color: 'var(--amber)', fontSize: 15 }}
            title={`Chờ hồ sơ tiên quyết: ${pending.map((p) => p.title).join(', ')}`} />
        )}
        {doc.file_note && (isLink(doc.file_note) ? (
          <a href={doc.file_note} target="_blank" rel="noopener noreferrer" className="srp-ibtn" title={doc.file_note}>
            <i className="ti ti-paperclip" />
          </a>
        ) : (
          <span className="srp-ibtn" title={doc.file_note} style={{ cursor: 'default' }}><i className="ti ti-paperclip" /></span>
        ))}
        {doc.expires_at && (
          <span className={`srp-date ${tone}`} title={dateTitle}>
            <i className="ti ti-calendar" /> {fmtDateStr(doc.expires_at)}
          </span>
        )}
        {doc.assignee_name && (
          <span className="srp-avatar" title={`Thực hiện: ${doc.assignee_name}`}>{nameInitials(doc.assignee_name)}</span>
        )}
        <span className={`badge ${REPORT_DOC_STATUS_BADGE[doc.status] || 'gray'}`}>{doc.status_label || REPORT_DOC_STATUS_LABELS[doc.status]}</span>
        {canEdit && (
          <>
            <button type="button" className="srp-ibtn" title="Sửa hồ sơ" onClick={() => openEditDoc(doc)}><i className="ti ti-pencil" /></button>
            <button type="button" className="srp-ibtn danger" title="Xóa hồ sơ" disabled={busy} onClick={() => deleteDoc(doc)}><i className="ti ti-trash" /></button>
          </>
        )}
      </div>
    )
  }

  // --- khung nhìn THEO GIAI ĐOẠN ---
  function renderPhaseView() {
    return (
      <div>
        {report!.phases.map((phase, idx) => {
          const phaseAll = scopedDocs.filter((d) => d.phase_id === phase.id)
          const phaseVisible = visibleDocs.filter((d) => d.phase_id === phase.id)
          const phaseDone = phaseAll.filter(isReportDocDone).length
          const collapsed = collapsedPhases.has(phase.id) && !filtering
          const finished = phaseAll.length > 0 && phaseDone === phaseAll.length
          return (
            <div key={phase.id} className="srp-phase">
              <div className="srp-phase-head">
                <button type="button" className="srp-ibtn" onClick={() => togglePhase(phase.id)} title={collapsed ? 'Mở' : 'Thu gọn'}>
                  <i className={`ti ti-chevron-${collapsed ? 'right' : 'down'}`} />
                </button>
                <span className={`srp-num${finished ? ' done' : ''}`}>{idx + 1}</span>
                <span style={{ fontWeight: 700, color: 'var(--navy)' }}>{phase.name}</span>
                {phase.location && <span style={{ color: 'var(--muted)', fontSize: 12.5 }}>{phase.location}</span>}
                <span style={{ flex: 1 }} />
                <span style={{ fontSize: 12, color: 'var(--muted)', whiteSpace: 'nowrap' }}>{phaseDone}/{phaseAll.length} hồ sơ · {reportPercent(phaseAll)}%</span>
                <span className="srp-bar" style={{ width: 80 }}><i style={{ width: `${reportPercent(phaseAll)}%` }} /></span>
                {canEdit && (
                  <>
                    <button type="button" className="srp-ibtn" title="Thêm hồ sơ vào giai đoạn" onClick={() => openCreateDoc({ phase_id: phase.id, item_id: itemFilter === REPORT_FILTER_ALL ? COMMON_ROW_ID : itemFilter })}><i className="ti ti-plus" /></button>
                    <button type="button" className="srp-ibtn" title="Tạo mẫu chung vào giai đoạn này" disabled={busy} onClick={() => applyTemplate(COMMON_ROW_ID, phase.id)}><i className="ti ti-sparkles" /></button>
                    <button type="button" className="srp-ibtn" title="Sửa giai đoạn" onClick={() => setPhaseDialog({ phase })}><i className="ti ti-pencil" /></button>
                  </>
                )}
              </div>
              {!collapsed && (
                phaseVisible.length ? phaseVisible.map((d) => renderDoc(d, true)) : (
                  <div className="srp-empty">
                    {phaseAll.length ? 'Không có hồ sơ khớp bộ lọc.' : 'Chưa có hồ sơ.'}
                    {canEdit && !phaseAll.length && (
                      <>
                        <button type="button" className="btn ghost sm" onClick={() => openCreateDoc({ phase_id: phase.id })}><i className="ti ti-plus" /> Thêm hồ sơ</button>
                        <button type="button" className="btn ghost sm" disabled={busy} onClick={() => applyTemplate(COMMON_ROW_ID, phase.id)}><i className="ti ti-sparkles" /> Tạo theo mẫu</button>
                      </>
                    )}
                  </div>
                )
              )}
            </div>
          )
        })}
      </div>
    )
  }

  // --- khung nhìn THEO DÒNG HÀNG ---
  function renderItemRow(id: number, name: string, item: SurveyReportItem | null) {
    const rowAll = report!.docs.filter((d) => d.item_id === id)
    const rowVisible = visibleDocs.filter((d) => d.item_id === id)
    const rowDone = rowAll.filter(isReportDocDone).length
    const expanded = expandedItems.has(id) || filtering
    const exp = nearestExpiry(rowAll)
    const tone = expiryTone(exp, today)
    return (
      <>
        <tr key={`row-${id}`}>
          <td style={{ width: 36 }}>
            <button type="button" className="srp-ibtn" onClick={() => toggleItem(id)}><i className={`ti ti-chevron-${expanded ? 'down' : 'right'}`} /></button>
          </td>
          <td>
            <span style={{ fontWeight: 600, color: 'var(--navy)' }}>{name}</span>
            {canEdit && item && (
              <button type="button" className="srp-ibtn" style={{ marginLeft: 4 }} title="Đổi tên / xóa nút" onClick={() => setItemDialog({ item })}><i className="ti ti-pencil" /></button>
            )}
          </td>
          <td>{rowAll.length}</td>
          <td>{rowDone}</td>
          <td>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="srp-bar" style={{ width: 90 }}><i style={{ width: `${reportPercent(rowAll)}%` }} /></span>
              <span style={{ fontSize: 12, color: 'var(--muted)' }}>{reportPercent(rowAll)}%</span>
            </div>
          </td>
          <td>{exp ? <span className={`srp-date ${tone}`}><i className="ti ti-calendar" /> {fmtDateStr(exp)}</span> : <span style={{ color: 'var(--muted)' }}>—</span>}</td>
        </tr>
        {expanded && (
          <tr key={`detail-${id}`}>
            <td colSpan={6} className="srp-item-detail">
              {report!.phases.map((phase) => {
                const docs = rowVisible.filter((d) => d.phase_id === phase.id)
                if (!docs.length) return null
                return (
                  <div key={phase.id} style={{ marginBottom: 6 }}>
                    <div style={{ fontSize: 11.5, fontWeight: 700, color: '#8592ae', textTransform: 'uppercase', letterSpacing: '.04em', padding: '4px 0' }}>{phase.name}</div>
                    {docs.map((d) => renderDoc(d, false))}
                  </div>
                )
              })}
              {!rowVisible.length && (
                <div style={{ color: 'var(--muted)', fontSize: 12.5, padding: '4px 0' }}>
                  {rowAll.length ? 'Không có hồ sơ khớp bộ lọc.' : 'Chưa có hồ sơ.'}
                </div>
              )}
              {canEdit && (
                <div style={{ display: 'flex', gap: 8, marginTop: 6, flexWrap: 'wrap' }}>
                  <button type="button" className="btn ghost sm" disabled={!report!.phases.length} onClick={() => openCreateDoc({ item_id: id })}><i className="ti ti-plus" /> Thêm hồ sơ cho {name}</button>
                  <button type="button" className="btn ghost sm" disabled={busy || !report!.phases.length} onClick={() => applyTemplate(id, null)}><i className="ti ti-sparkles" /> Tạo mẫu cho {name}</button>
                </div>
              )}
            </td>
          </tr>
        )}
      </>
    )
  }

  function renderItemView() {
    const commonDocs = report!.docs.filter((d) => d.item_id === COMMON_ROW_ID)
    const showCommon = commonDocs.length > 0 || !report!.items.length
    const orphanPhases = report!.phases.filter((p) => !report!.docs.some((d) => d.phase_id === p.id))
    return (
      <div className="items-scroll">
        <table className="srp-item-table">
          <thead>
            <tr>
              <th style={{ width: 36 }} />
              <th>Dòng hàng</th>
              <th style={{ width: 70 }}>Hồ sơ</th>
              <th style={{ width: 80 }}>Đã xong</th>
              <th style={{ width: 150 }}>Tiến độ</th>
              <th style={{ width: 120 }}>Hạn gần nhất</th>
            </tr>
          </thead>
          <tbody>
            {showCommon && renderItemRow(COMMON_ROW_ID, 'Chung (cả phiếu)', null)}
            {report!.items.map((it) => renderItemRow(it.id, it.name, it))}
            {canEdit && (
              <tr>
                <td colSpan={6}>
                  <button type="button" className="btn ghost sm" onClick={() => setItemDialog({ item: null })}><i className="ti ti-plus" /> Thêm nút dòng hàng</button>
                </td>
              </tr>
            )}
          </tbody>
          <tfoot>
            <tr>
              <td />
              <td style={{ fontWeight: 700, color: 'var(--navy)' }}>Tổng cả phiếu</td>
              <td>{report!.docs.length}</td>
              <td>{report!.docs.filter(isReportDocDone).length}</td>
              <td style={{ fontSize: 12, color: 'var(--muted)' }}>{reportPercent(report!.docs)}%</td>
              <td>{nearestExpiry(report!.docs) ? fmtDateStr(nearestExpiry(report!.docs)) : '—'}</td>
            </tr>
          </tfoot>
        </table>
        {orphanPhases.length > 0 && (
          <div style={{ marginTop: 8, fontSize: 12.5, color: 'var(--muted)', display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
            Giai đoạn chưa có hồ sơ:
            {orphanPhases.map((p) => <span key={p.id} className="badge gray" style={{ textTransform: 'none' }}>{p.name}</span>)}
          </div>
        )}
      </div>
    )
  }

  // --- khung TIẾN TRÌNH ---
  function renderTracking() {
    const markers = trackingMarkers(report!, itemFilter)
    const markerByPhase = new Map(markers.map((m) => [m.phaseId, m]))
    return (
      <div className="srp-tracking">
        <div style={{ fontSize: 12, fontWeight: 700, color: '#8592ae', textTransform: 'uppercase', letterSpacing: '.04em', marginBottom: 10 }}>Tiến trình</div>
        {report!.phases.map((phase) => {
          const docs = scopedDocs.filter((d) => d.phase_id === phase.id)
          const finished = docs.length > 0 && docs.every(isReportDocDone)
          const marker = markerByPhase.get(phase.id)
          return (
            <div key={phase.id} className="srp-track-row">
              <span className={`srp-dot${finished ? ' done' : marker ? ' now' : ''}`} title={marker?.names.join(', ') || ''}>
                {finished ? <i className="ti ti-check" /> : marker?.label || ''}
              </span>
              <div style={{ minWidth: 0 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--navy)' }}>{phase.name}</div>
                <div style={{ fontSize: 11.5, color: 'var(--muted)' }}>
                  {docs.length ? `${docs.filter(isReportDocDone).length}/${docs.length} hồ sơ · ${reportPercent(docs)}%` : 'Chưa có hồ sơ'}
                </div>
                {marker && marker.names.length > 0 && (
                  <div style={{ fontSize: 11.5, color: 'var(--amber)' }}>{marker.names.join(', ')}</div>
                )}
              </div>
            </div>
          )
        })}
        {!report!.phases.length && <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>Chưa có giai đoạn.</div>}
      </div>
    )
  }

  const currentPhaseId = currentReportPhaseId(report, itemFilter)
  const currentPhaseName = report.phases.find((p) => p.id === currentPhaseId)?.name

  return (
    <div className="card" style={{ padding: 18 }}>
      <div className="srp-head" onClick={() => setOpen((o) => !o)}>
        <i className={`ti ti-chevron-${open ? 'down' : 'right'}`} style={{ color: '#94a3b8' }} />
        <h3 className="sec-title" style={{ margin: 0, border: 0, padding: 0 }}><i className="ti ti-list-check" /> Báo cáo thực hiện</h3>
        {!isEmpty && (
          <span style={{ fontSize: 12.5, color: 'var(--muted)' }}>
            {done}/{total} hồ sơ · {percent}%{currentPhaseName ? ` · đang ở: ${currentPhaseName}` : ''}
          </span>
        )}
        <span style={{ flex: 1 }} />
        {canEdit && !isEmpty && (
          <button type="button" className="srp-ibtn danger" title="Xóa toàn bộ báo cáo (hoàn tác được)" disabled={busy}
            onClick={(e) => { e.stopPropagation(); deleteReport() }}>
            <i className="ti ti-trash" />
          </button>
        )}
      </div>

      {open && isEmpty && (
        <div style={{ padding: '14px 0 4px', color: 'var(--muted)', fontSize: 13 }}>
          <div style={{ marginBottom: 10 }}>Phiếu này chưa có báo cáo thực hiện.</div>
          {canEdit && (
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {report.restorable && (
                <button type="button" className="btn secondary" disabled={busy} onClick={restoreReport}><i className="ti ti-arrow-back-up" /> Hoàn tác xóa</button>
              )}
              <button type="button" className="btn" disabled={busy} onClick={initReport}><i className="ti ti-sparkles" /> Khởi tạo báo cáo mẫu</button>
              <button type="button" className="btn ghost" onClick={() => setPhaseDialog({ phase: null })}><i className="ti ti-plus" /> Thêm giai đoạn</button>
            </div>
          )}
        </div>
      )}

      {open && !isEmpty && (
        <div style={{ paddingTop: 14 }}>
          <div className="srp-toolbar">
            <span className="srp-seg">
              <button type="button" className={viewMode === 'phase' ? 'on' : ''} onClick={() => setViewMode('phase')}><i className="ti ti-layout-list" /> Xem tổng</button>
              <button type="button" className={viewMode === 'item' ? 'on' : ''} onClick={() => setViewMode('item')}><i className="ti ti-table" /> Theo dòng hàng</button>
            </span>
            <input
              placeholder="Tìm hồ sơ (bỏ dấu được)…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ width: 220 }}
            />
            <select value={statusFilter} onChange={(e) => setStatusFilter(Number(e.target.value))} style={{ width: 150 }}>
              <option value={REPORT_STATUS_FILTER_ALL}>Mọi trạng thái</option>
              {[REPORT_DOC_IDLE, REPORT_DOC_DOING, 2, REPORT_DOC_DONE].map((s) => (
                <option key={s} value={s}>{REPORT_DOC_STATUS_LABELS[s]}</option>
              ))}
            </select>
            <button type="button" className="btn ghost sm" onClick={toggleAll}>
              <i className={`ti ti-${viewMode === 'item' ? (expandedItems.size ? 'fold' : 'fold-down') : (allCollapsed ? 'fold-down' : 'fold')}`} />
              {viewMode === 'item' ? (expandedItems.size ? 'Thu gọn' : 'Mở tất cả') : (allCollapsed ? 'Mở tất cả' : 'Thu gọn')}
            </button>
            <span style={{ flex: 1 }} />
            {canEdit && (
              <>
                <button type="button" className="btn ghost sm" onClick={() => setPhaseDialog({ phase: null })}><i className="ti ti-plus" /> Thêm giai đoạn</button>
                <button type="button" className="btn secondary sm" disabled={!report.phases.length} title={report.phases.length ? '' : 'Thêm giai đoạn trước'}
                  onClick={() => openCreateDoc({ item_id: itemFilter === REPORT_FILTER_ALL ? COMMON_ROW_ID : itemFilter })}>
                  <i className="ti ti-plus" /> Thêm hồ sơ
                </button>
              </>
            )}
          </div>

          {viewMode === 'phase' && report.items.length > 0 && (
            <div className="srp-chips" style={{ marginBottom: 12 }}>
              <button type="button" className={`srp-chip${itemFilter === REPORT_FILTER_ALL ? ' on' : ''}`} onClick={() => setItemFilter(REPORT_FILTER_ALL)}>Tất cả</button>
              {report.items.map((it, idx) => (
                <button key={it.id} type="button" className={`srp-chip${itemFilter === it.id ? ' on' : ''}`} onClick={() => setItemFilter(it.id)}>
                  {idx + 1}. {it.name}
                </button>
              ))}
              {canEdit && (
                <button type="button" className="srp-chip" title="Thêm nút dòng hàng" onClick={() => setItemDialog({ item: null })}><i className="ti ti-plus" /></button>
              )}
              {canEdit && itemFilter !== REPORT_FILTER_ALL && (
                <button type="button" className="srp-chip" title="Đổi tên / xóa nút đang chọn"
                  onClick={() => { const it = report.items.find((x) => x.id === itemFilter); if (it) setItemDialog({ item: it }) }}>
                  <i className="ti ti-pencil" />
                </button>
              )}
            </div>
          )}

          <div className="srp-layout">
            <div style={{ minWidth: 0 }}>
              <div className="srp-summary">
                <div className="srp-tile">
                  <div className="lbl">Tổng hồ sơ</div>
                  <div className="val">{total}</div>
                </div>
                <div className="srp-tile">
                  <div className="lbl">Đã hoàn thành</div>
                  <div className="val">{done}/{total} <span style={{ fontSize: 12.5, color: 'var(--muted)', fontWeight: 500 }}>({percent}%)</span></div>
                  <div className="srp-bar" style={{ marginTop: 6 }}><i style={{ width: `${percent}%` }} /></div>
                </div>
                <div className="srp-tile">
                  <div className="lbl">Hết hiệu lực gần nhất</div>
                  <div className="val" style={{ color: expiryTone(expiry, today) === 'overdue' ? 'var(--red)' : expiryTone(expiry, today) === 'soon' ? 'var(--amber)' : undefined }}>
                    {expiry ? fmtDateStr(expiry) : '—'}
                  </div>
                  {expiry && expiryTone(expiry, today) !== 'normal' && (
                    <div style={{ fontSize: 11.5, color: 'var(--muted)' }}>{expiryTone(expiry, today) === 'overdue' ? 'Đã quá hạn' : `Trong ${EXPIRY_SOON_DAYS} ngày tới`}</div>
                  )}
                </div>
              </div>

              {viewMode === 'phase' ? renderPhaseView() : renderItemView()}

              {!visibleDocs.length && scopedDocs.length > 0 && filtering && viewMode === 'phase' && (
                <div style={{ color: 'var(--muted)', fontSize: 12.5, marginTop: 6 }}>Không có hồ sơ nào khớp bộ lọc / từ khóa.</div>
              )}
              <div style={{ color: '#8592ae', fontSize: 11.5, marginTop: 8 }}>
                <i className="ti ti-lock" /> hồ sơ khóa = chờ hồ sơ tiên quyết hoàn thành trước
              </div>
            </div>
            {renderTracking()}
          </div>
        </div>
      )}

      {docDialog && (
        <DocDialog
          report={report}
          doc={docDialog.doc}
          defaults={docDialog.defaults}
          defaultAssigneeId={Number((user as any)?.employee_id || 0)}
          busy={busy}
          onSave={async (payload) => { const ok = await saveDoc(docDialog.doc?.id ?? null, payload); if (ok) setDocDialog(null); return ok }}
          onDelete={docDialog.doc ? async () => { const ok = await deleteDoc(docDialog.doc!); if (ok) setDocDialog(null) } : undefined}
          onClose={() => setDocDialog(null)}
        />
      )}
      {itemDialog && (
        <ItemDialog
          item={itemDialog.item}
          busy={busy}
          onSave={async (name) => { const ok = await saveItem(itemDialog.item?.id ?? null, name); if (ok) setItemDialog(null) }}
          onDelete={itemDialog.item ? async () => { const ok = await deleteItem(itemDialog.item!); if (ok) { setItemDialog(null); if (itemFilter === itemDialog.item!.id) setItemFilter(REPORT_FILTER_ALL) } } : undefined}
          onClose={() => setItemDialog(null)}
        />
      )}
      {phaseDialog && (
        <PhaseDialog
          phase={phaseDialog.phase}
          busy={busy}
          onSave={async (name, location) => { const ok = await savePhase(phaseDialog.phase?.id ?? null, name, location); if (ok) setPhaseDialog(null) }}
          onDelete={phaseDialog.phase ? async () => { const ok = await deletePhase(phaseDialog.phase!); if (ok) setPhaseDialog(null) } : undefined}
          onClose={() => setPhaseDialog(null)}
        />
      )}
    </div>
  )
}

// ============================================================================
// Hộp thoại dùng chung (C-01: chỉ đóng bằng Hủy / X; form dở thì hỏi xác nhận;
// KHÔNG bọc <form> để Enter trong ô con không submit form cha của trang)
// ============================================================================

function ReportModal({ title, dirty, width = 680, onClose, footer, children }: {
  title: string
  dirty: boolean
  width?: number
  onClose: () => void
  footer: React.ReactNode
  children: React.ReactNode
}) {
  async function requestClose() {
    if (dirty) {
      const ok = await askConfirm({ title: 'Đóng hộp thoại', message: 'Bạn có thay đổi chưa lưu. Đóng và bỏ thay đổi?', confirmText: 'Đóng', danger: true })
      if (!ok) return
    }
    onClose()
  }
  return (
    <div className="srp-modal-overlay">
      <div className="card srp-modal" style={{ width }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 className="sec-title" style={{ margin: 0, border: 0, padding: 0 }}>{title}</h3>
          <span className="clickable" style={{ color: '#94a3b8', fontSize: 18 }} onClick={requestClose}><i className="ti ti-x" /></span>
        </div>
        {children}
        <div className="srp-modal-foot">
          {footer}
        </div>
      </div>
    </div>
  )
}

function useCancel(dirty: boolean, onClose: () => void) {
  return async () => {
    if (dirty) {
      const ok = await askConfirm({ title: 'Đóng hộp thoại', message: 'Bạn có thay đổi chưa lưu. Đóng và bỏ thay đổi?', confirmText: 'Đóng', danger: true })
      if (!ok) return
    }
    onClose()
  }
}

// --- Hồ sơ ---
function DocDialog({ report, doc, defaults, defaultAssigneeId, busy, onSave, onDelete, onClose }: {
  report: SurveyRequestReport
  doc: SurveyReportDoc | null
  defaults?: Partial<SurveyReportDocPayload>
  defaultAssigneeId: number
  busy: boolean
  onSave: (payload: SurveyReportDocPayload) => Promise<boolean>
  onDelete?: () => Promise<void>
  onClose: () => void
}) {
  const initial: SurveyReportDocPayload = useMemo(() => doc ? {
    title: doc.title, description: doc.description, phase_id: doc.phase_id, item_id: doc.item_id,
    required: doc.required, status: doc.status, file_note: doc.file_note, depends: [...doc.depends],
    start_date: doc.start_date || '', expires_at: doc.expires_at || '', assignee_id: doc.assignee_id || 0,
  } : {
    title: '', description: '', phase_id: defaults?.phase_id ?? (report.phases[0]?.id ?? 0),
    item_id: defaults?.item_id ?? COMMON_ROW_ID, required: false, status: REPORT_DOC_IDLE, file_note: '',
    depends: [], start_date: '', expires_at: '', assignee_id: defaultAssigneeId,
  }, [])
  const [form, setForm] = useState<SurveyReportDocPayload>(initial)
  const [employees, setEmployees] = useState<{ value: string; label: string }[]>([])
  const dirty = JSON.stringify(form) !== JSON.stringify(initial)
  const cancel = useCancel(dirty, onClose)
  const savingRef = useRef(false)

  useEffect(() => {
    api.get('/api/employees', { params: { page_size: 1000, is_active: true }, _silent: true } as any)
      .then((r) => setEmployees((r.data.data.items || []).map((e: any) => ({ value: String(e.id), label: e.full_name + (e.code ? ` · ${e.code}` : '') }))))
      .catch(() => {})
  }, [])

  const set = <K extends keyof SurveyReportDocPayload>(k: K, v: SurveyReportDocPayload[K]) => setForm((f) => ({ ...f, [k]: v }))
  const others = report.docs.filter((d) => d.id !== doc?.id)
  const itemLabel = (id: number) => (id === COMMON_ROW_ID ? 'Chung' : report.items.find((i) => i.id === id)?.name || '')

  async function save() {
    if (savingRef.current) return
    if (!form.title.trim()) { toast.error('Nhập tiêu đề hồ sơ'); return }
    if (!form.phase_id) { toast.error('Chọn giai đoạn'); return }
    savingRef.current = true
    try { await onSave({ ...form, title: form.title.trim() }) } finally { savingRef.current = false }
  }

  // Ép nhân sự đang gắn vào danh sách nếu API không trả (ngoài phạm vi) — để không mất tên
  const assigneeOptions = useMemo(() => {
    const opts = [...employees]
    if (doc?.assignee_id && !opts.some((o) => o.value === String(doc.assignee_id))) opts.push({ value: String(doc.assignee_id), label: doc.assignee_name || `#${doc.assignee_id}` })
    return opts
  }, [employees, doc])

  return (
    <ReportModal
      title={doc ? 'Sửa hồ sơ' : 'Thêm hồ sơ'}
      dirty={dirty}
      onClose={onClose}
      footer={
        <>
          <span>
            {onDelete && <button type="button" className="btn err" disabled={busy} onClick={onDelete}><i className="ti ti-trash" /> Xóa</button>}
          </span>
          <span style={{ display: 'flex', gap: 8 }}>
            <button type="button" className="btn ghost" onClick={cancel}>Hủy</button>
            <button type="button" className="btn" disabled={busy} onClick={save}><i className="ti ti-device-floppy" /> Lưu</button>
          </span>
        </>
      }
    >
      <div className="form-grid">
        <div className="form-row full">
          <label>Tiêu đề <span className="req">*</span></label>
          <input value={form.title} autoFocus placeholder="Vd: Giấy phép nhập khẩu — Bộ Công Thương" onChange={(e) => set('title', e.target.value)} />
        </div>
        <div className="form-row full">
          <label>Mô tả</label>
          <textarea rows={3} style={{ minHeight: 64 }} value={form.description} placeholder="Diễn giải, nơi nộp, ghi chú…" onChange={(e) => set('description', e.target.value)} />
        </div>
        <div className="form-row">
          <label>Dòng hàng</label>
          <select value={form.item_id} onChange={(e) => set('item_id', Number(e.target.value))}>
            <option value={COMMON_ROW_ID}>Chung (cả phiếu)</option>
            {report.items.map((it) => <option key={it.id} value={it.id}>{it.name}</option>)}
          </select>
        </div>
        <div className="form-row">
          <label>Giai đoạn <span className="req">*</span></label>
          <select value={form.phase_id} onChange={(e) => set('phase_id', Number(e.target.value))}>
            {!form.phase_id && <option value={0}>— Chọn giai đoạn —</option>}
            {report.phases.map((p, idx) => <option key={p.id} value={p.id}>{idx + 1}. {p.name}</option>)}
          </select>
        </div>
        <div className="form-row">
          <label>Trạng thái</label>
          <select value={form.status} onChange={(e) => set('status', Number(e.target.value))}>
            {[REPORT_DOC_IDLE, REPORT_DOC_DOING, 2, REPORT_DOC_DONE].map((s) => <option key={s} value={s}>{REPORT_DOC_STATUS_LABELS[s]}</option>)}
          </select>
        </div>
        <div className="form-row">
          <label>Bắt buộc?</label>
          <select value={form.required ? 1 : 0} onChange={(e) => set('required', e.target.value === '1')}>
            <option value={0}>Không</option>
            <option value={1}>Bắt buộc</option>
          </select>
        </div>
        <div className="form-row">
          <label>Ngày bắt đầu</label>
          <DateInput value={form.start_date} onChange={(v) => set('start_date', v)} />
        </div>
        <div className="form-row">
          <label>Ngày hết hiệu lực</label>
          <DateInput value={form.expires_at} onChange={(v) => set('expires_at', v)} />
        </div>
        <div className="form-row">
          <label>Nhân sự thực hiện</label>
          <SearchSelect
            value={form.assignee_id ? String(form.assignee_id) : ''}
            options={assigneeOptions}
            placeholder="Chọn/tìm nhân sự…"
            autoSelectSingle={false}
            onChange={(v) => set('assignee_id', Number(v) || 0)}
          />
        </div>
        <div className="form-row">
          <label>Tệp đính kèm / link</label>
          <input value={form.file_note} placeholder="Tên tệp hoặc link Drive…" onChange={(e) => set('file_note', e.target.value)} />
        </div>
        <div className="form-row full">
          <label>Hồ sơ tiên quyết (phải hoàn thành trước)</label>
          {others.length ? (
            <div className="srp-deps">
              {others.map((d) => (
                <label key={d.id}>
                  <input
                    type="checkbox"
                    checked={form.depends.includes(d.id)}
                    onChange={(e) => set('depends', e.target.checked ? [...form.depends, d.id] : form.depends.filter((x) => x !== d.id))}
                  />
                  <span>{d.title}</span>
                  <span style={{ color: 'var(--muted)', fontSize: 11.5 }}>· {itemLabel(d.item_id)}{isReportDocDone(d) ? ' · đã xong' : ''}</span>
                </label>
              ))}
            </div>
          ) : (
            <div style={{ color: 'var(--muted)', fontSize: 12.5 }}>Chưa có hồ sơ khác để chọn.</div>
          )}
        </div>
      </div>
    </ReportModal>
  )
}

// --- Nút dòng hàng ---
function ItemDialog({ item, busy, onSave, onDelete, onClose }: {
  item: SurveyReportItem | null
  busy: boolean
  onSave: (name: string) => Promise<void>
  onDelete?: () => Promise<void>
  onClose: () => void
}) {
  const [name, setName] = useState(item?.name || '')
  const dirty = name !== (item?.name || '')
  const cancel = useCancel(dirty, onClose)
  const savingRef = useRef(false)
  async function save() {
    if (savingRef.current) return
    if (!name.trim()) { toast.error('Nhập tên nút dòng hàng'); return }
    savingRef.current = true
    try { await onSave(name.trim()) } finally { savingRef.current = false }
  }
  return (
    <ReportModal
      title={item ? 'Sửa nút dòng hàng' : 'Thêm nút dòng hàng'}
      dirty={dirty}
      width={460}
      onClose={onClose}
      footer={
        <>
          <span>{onDelete && <button type="button" className="btn err" disabled={busy} onClick={onDelete}><i className="ti ti-trash" /> Xóa</button>}</span>
          <span style={{ display: 'flex', gap: 8 }}>
            <button type="button" className="btn ghost" onClick={cancel}>Hủy</button>
            <button type="button" className="btn" disabled={busy} onClick={save}><i className="ti ti-device-floppy" /> Lưu</button>
          </span>
        </>
      }
    >
      <div className="form-row">
        <label>Tên nút <span className="req">*</span></label>
        <input value={name} autoFocus placeholder="Vd: KNO₃" onChange={(e) => setName(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') save() }} />
      </div>
      {item && <div style={{ color: 'var(--muted)', fontSize: 12.5, marginTop: 8 }}>Xóa nút: hồ sơ đang gắn nút này sẽ chuyển về Chung, không bị xóa.</div>}
    </ReportModal>
  )
}

// --- Giai đoạn ---
function PhaseDialog({ phase, busy, onSave, onDelete, onClose }: {
  phase: SurveyReportPhase | null
  busy: boolean
  onSave: (name: string, location: string) => Promise<void>
  onDelete?: () => Promise<void>
  onClose: () => void
}) {
  const [name, setName] = useState(phase?.name || '')
  const [location, setLocation] = useState(phase?.location || '')
  const dirty = name !== (phase?.name || '') || location !== (phase?.location || '')
  const cancel = useCancel(dirty, onClose)
  const savingRef = useRef(false)
  async function save() {
    if (savingRef.current) return
    if (!name.trim()) { toast.error('Nhập tên giai đoạn'); return }
    savingRef.current = true
    try { await onSave(name.trim(), location.trim()) } finally { savingRef.current = false }
  }
  return (
    <ReportModal
      title={phase ? 'Sửa giai đoạn' : 'Thêm giai đoạn'}
      dirty={dirty}
      width={520}
      onClose={onClose}
      footer={
        <>
          <span>{onDelete && <button type="button" className="btn err" disabled={busy} onClick={onDelete}><i className="ti ti-trash" /> Xóa</button>}</span>
          <span style={{ display: 'flex', gap: 8 }}>
            <button type="button" className="btn ghost" onClick={cancel}>Hủy</button>
            <button type="button" className="btn" disabled={busy} onClick={save}><i className="ti ti-device-floppy" /> Lưu</button>
          </span>
        </>
      }
    >
      <div className="form-grid">
        <div className="form-row full">
          <label>Tên giai đoạn <span className="req">*</span></label>
          <input value={name} autoFocus placeholder="Vd: Pháp lý & Giấy phép" onChange={(e) => setName(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') save() }} />
        </div>
        <div className="form-row full">
          <label>Diễn giải / nơi thực hiện</label>
          <input value={location} placeholder="Vd: Bộ Công Thương · Hải quan cảng…" onChange={(e) => setLocation(e.target.value)} />
        </div>
      </div>
    </ReportModal>
  )
}
