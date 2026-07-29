import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import Pagination from '../components/Pagination'
import { askConfirm } from '../components/confirm'
import { useAuth } from '../auth/AuthContext'
import { toast } from '../components/toast'
import Select from 'react-select'
import ProductPicker from '../components/ProductPicker'

const API = '/api/survey-requests'

const fmtNum = (n: any) => {
  const v = Number(n || 0)
  return v ? v.toLocaleString('vi-VN') : '—'
}

const SR_STATUS: Record<string, { label: string; cls: string }> = {
  draft:        { label: 'Nháp',          cls: 'gray' },
  submitted:    { label: 'Chờ duyệt',     cls: 'warn' },
  approved:     { label: 'Đã duyệt',      cls: 'ok'   },
  rejected:     { label: 'Từ chối',       cls: 'err'  },
  processing:   { label: 'Đang xử lý',    cls: 'warn' },
  survey_done:  { label: 'Đã khảo sát',   cls: 'ok'   },
  pr_created:   { label: 'Đã tạo YCMH',   cls: 'warn' },
  done:         { label: 'Hoàn thành',    cls: 'ok'   },
}

const srBadge = (st: string) => {
  const s = SR_STATUS[String(st || '').toLowerCase()] || { label: st, cls: 'gray' }
  return <span className={'badge ' + s.cls}>{s.label}</span>
}

interface ProcessLine {
  id: number
  internal_line_code: string
  item_group: string
  requirement_detail: string
  other_requirement: string
  request_qty: number
  uom: string
  proposed_price: number
  assignee: string
  assignee_name: string
  options: ProcessOption[]
  can_process?: boolean   // dòng này người xem có được gắn/xóa phương án không (Admin TM đọc-chỉ -> false ở dòng người khác)
}

interface ProcessOption {
  id: number
  public_id: string
  display_label: string
  is_chosen: boolean
  system_product_code: string
  snap_product_name: string
  snap_spec: string
  snap_origin: string
  snap_quote_unit: string
  snap_moq: number
  snap_price_by_volume: number
  snap_volume_range: string
  snap_vat: number
  snap_delivery_time: string
  snap_delivery_place: string
  snap_shipping_cost: number
  snap_sample_ready: boolean
  snap_lab_result: string
  snap_internal_code: string
  supplier_code: string
  supplier_name: string
  nstm_note: string
  product_survey_line_id: number
}

interface AvailSurveyLine {
  id: number
  supplier_code: string
  supplier_name: string
  internal_code: string
  product_name: string
  spec: string
  origin: string
  quote_unit: string
  moq: number
  price_by_volume: number
  volume_range: string
  vat: number
  delivery_time: string
  delivery_place: string
  shipping_cost: number
  sample_ready: boolean
  lab_result: string
  nspt_reason: string
  line_approve: string
  survey_item_group?: string   // phân loại của Phiếu khảo sát cha (để cảnh báo khi khác phân loại dòng)
  survey_code?: string
}

interface ProcessData {
  id: number
  code: string
  status: string
  request_date: string
  department: string
  requester: string
  company_id: number
  lines: ProcessLine[]
}

interface Supplier {
  id: number
  code: string
  name: string
}

// Per-line local state for supplier selection + available survey lines
interface LineState {
  supplierCode: string
  filterGroup: string   // phân loại đang lọc (mặc định = phân loại dòng, đổi được)
  search: string        // tìm theo mã/tên SP
  availLines: AvailSurveyLine[]
  loading: boolean
  selectedAvailIds: Set<number>
  availPage: number   // trang hiện tại của danh sách dòng khảo sát khả dụng
}

const AVAIL_PAGE_SIZE = 8   // số dòng khảo sát khả dụng mỗi trang
const SEL_STYLES = {
  control: (b: any) => ({ ...b, minHeight: 40, borderRadius: 12, borderColor: '#E9EDF7' }),
  menu: (b: any) => ({ ...b, zIndex: 9999 }),
  menuPortal: (b: any) => ({ ...b, zIndex: 9999 }),
}

export default function SurveyRequestProcess() {
  const { id } = useParams()
  const { can } = useAuth()
  const navigate = useNavigate()

  const [data, setData]           = useState<ProcessData | null>(null)
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [groups, setGroups]       = useState<string[]>([])   // danh mục phân loại (cho bộ lọc)
  const [lineStates, setLineStates] = useState<LineState[]>([])
  const searchTimers = useRef<Record<number, any>>({})       // debounce ô tìm mỗi dòng
  const [err, setErr]             = useState('')
  const [msg, setMsg]             = useState('')
  const [forbidden, setForbidden] = useState(false)
  const [completing, setCompleting] = useState(false)
  const [attempted, setAttempted] = useState(false)
  const [emptyPrompt, setEmptyPrompt] = useState<ProcessLine[] | null>(null)   // dòng chưa có PA -> hỏi chốt rỗng
  const [emptyChecked, setEmptyChecked] = useState<Set<number>>(new Set())

  const supplierOptions = suppliers.map((s) => ({
    value: s.code,
    label: `${s.name} (${s.code})`,
  }))

  async function loadProcess() {
    try {
      const r = await api.get(`${API}/${id}/process`)
      const d: ProcessData = r.data.data
      setData(d)
      // Reset per-line state, giữ lại bộ lọc + kết quả đã tải (phân loại mặc định = phân loại dòng)
      setLineStates((prev) =>
        (d.lines || []).map((ln, i) => ({
          supplierCode: prev[i]?.supplierCode || '',
          filterGroup:  prev[i]?.filterGroup ?? (ln.item_group || ''),
          search:       prev[i]?.search || '',
          availLines:   prev[i]?.availLines   || [],
          loading:      false,
          selectedAvailIds: new Set<number>(),
          availPage:    prev[i]?.availPage || 0,
        }))
      )
    } catch (e: any) {
      if (e.response?.status === 403) setForbidden(true)
      else setErr(e.response?.data?.message || 'Lỗi tải dữ liệu')
    }
  }

  useEffect(() => {
    // Chỉ NCC SẢN PHẨM (goods) đang hoạt động — bỏ NCC vận chuyển (transport)
    api.get('/api/suppliers', { params: { page_size: 1000, supplier_type: 'goods', is_active: true } })
      .then((r) => setSuppliers((r.data.data.items || []).filter((s: any) => s.supplier_type === 'goods')))
      .catch(() => {})
    api.get('/api/item-groups', { params: { page_size: 1000 } })
      .then((r) => setGroups((r.data.data.items || []).map((x: any) => x.name))).catch(() => {})
    loadProcess()
  }, [id])

  // Lần đầu tải phiếu -> tự tìm kết quả khảo sát theo PHÂN LOẠI mặc định của từng dòng
  useEffect(() => {
    if (!data) return
    ;(data.lines || []).forEach((ln, i) => {
      if ((lineStates[i]?.availLines || []).length === 0)
        fetchAvail(i, ln.id, { filterGroup: ln.item_group || '' })
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.id])

  // Tìm dòng khảo sát khả dụng theo bộ lọc (NCC / phân loại / mã-tên SP). patch = phần filter thay đổi.
  async function fetchAvail(lineIdx: number, lineId: number, patch: Partial<Pick<LineState, 'supplierCode' | 'filterGroup' | 'search'>>) {
    const cur = lineStates[lineIdx] || ({} as LineState)
    const merged = {
      supplierCode: patch.supplierCode ?? cur.supplierCode ?? '',
      filterGroup: patch.filterGroup ?? cur.filterGroup ?? '',
      search: patch.search ?? cur.search ?? '',
    }
    setLineStates((prev) => prev.map((s, i) => i === lineIdx
      ? { ...s, ...patch, loading: true, availPage: 0, selectedAvailIds: new Set<number>() } : s))
    // Cần ít nhất 1 tiêu chí -> nếu rỗng hết thì xóa kết quả
    if (!merged.supplierCode && !merged.filterGroup && !merged.search.trim()) {
      setLineStates((prev) => prev.map((s, i) => i === lineIdx ? { ...s, availLines: [], loading: false } : s))
      return
    }
    try {
      const r = await api.get(`${API}/${id}/lines/${lineId}/available-survey-lines`, {
        params: { supplier_code: merged.supplierCode, item_group: merged.filterGroup, search: merged.search.trim() },
      })
      setLineStates((prev) => prev.map((s, i) => i === lineIdx ? { ...s, loading: false, availLines: r.data.data || [] } : s))
    } catch {
      setLineStates((prev) => prev.map((s, i) => i === lineIdx ? { ...s, loading: false, availLines: [] } : s))
    }
  }

  // Ô tìm có debounce 400ms (cập nhật input ngay, gọi API sau)
  function onSearchChange(lineIdx: number, lineId: number, val: string) {
    setLineStates((prev) => prev.map((s, i) => i === lineIdx ? { ...s, search: val } : s))
    clearTimeout(searchTimers.current[lineIdx])
    searchTimers.current[lineIdx] = setTimeout(() => fetchAvail(lineIdx, lineId, { search: val }), 400)
  }

  async function addOption(lineId: number, surveyLineId: number) {
    try {
      await api.post(`${API}/${id}/lines/${lineId}/options`, { product_survey_line_id: surveyLineId })
      await loadProcess()
      toast.success('Đã thêm phương án')
    } catch { /* lỗi đã hiện popup từ interceptor */ }
  }

  async function removeOption(lineId: number, optionId: number) {
    if (!(await askConfirm({ message: 'Xóa phương án này?' }))) return
    try {
      await api.delete(`${API}/${id}/lines/${lineId}/options/${optionId}`)
      await loadProcess()
      toast.success('Đã xóa phương án')
    } catch { /* lỗi đã hiện popup từ interceptor */ }
  }

  // Gắn/đổi Mã SP hệ thống cho option (chảy sang dòng PYC khi tạo yêu cầu mua)
  async function setOptionProduct(lineId: number, optionId: number, code: string) {
    try {
      await api.patch(`${API}/${id}/lines/${lineId}/options/${optionId}`, { system_product_code: code })
      await loadProcess()
      toast.success(code ? 'Đã gắn mã SP hệ thống' : 'Đã bỏ mã SP')
    } catch { /* interceptor toast */ }
  }

  async function complete() {
    setAttempted(true)
    const lines = data?.lines || []
    const missingOptions = lines.flatMap(l => l.options || []).filter(o => !o.system_product_code)
    if (missingOptions.length > 0) {
      toast.error('Vui lòng chọn Mã SP hệ thống cho tất cả Option trước khi chốt')
      return
    }
    // Dòng chưa có phương án -> hỏi chốt rỗng (không có NCC phù hợp)
    const emptyLines = lines.filter((l) => (l.options || []).length === 0)
    if (emptyLines.length > 0) {
      setEmptyChecked(new Set())
      setEmptyPrompt(emptyLines)
      return
    }
    if (!(await askConfirm({ title: 'Chốt hoàn thành', message: 'Chốt hoàn thành khảo sát?', confirmText: 'Chốt hoàn thành', danger: false }))) return
    await doComplete([])
  }

  async function doComplete(emptyLineIds: number[]) {
    setCompleting(true)
    try {
      const r = await api.post(`${API}/${id}/complete`, { empty_line_ids: emptyLineIds })
      toast.success(r.data?.message || 'Đã chốt hoàn thành khảo sát')
      setEmptyPrompt(null)
      navigate(`/survey-requests/${id}`)
    } catch { /* lỗi đã hiện popup từ interceptor */
    } finally {
      setCompleting(false)
    }
  }

  if (forbidden) {
    return (
      <div style={{ padding: 40, textAlign: 'center' }}>
        <i className="ti ti-lock" style={{ fontSize: 40, color: 'var(--muted)' }} />
        <p style={{ color: 'var(--muted)', marginTop: 12, fontSize: 15 }}>
          Bạn không có quyền xử lý khảo sát
        </p>
        <button className="btn ghost" style={{ marginTop: 16 }} onClick={() => navigate(`/survey-requests/${id}`)}>
          <i className="ti ti-arrow-left" /> Quay lại
        </button>
      </div>
    )
  }

  if (!data) {
    return (
      <div style={{ padding: 40, textAlign: 'center', color: 'var(--muted)' }}>
        {err ? <span style={{ color: 'var(--red)' }}>{err}</span> : 'Đang tải...'}
      </div>
    )
  }

  const lines = data.lines || []
  const allHaveOptions = lines.length > 0 && lines.every((l) => (l.options || []).length > 0)
  const canProcess = can('survey_request', 'process')   // NSTM/QL/Admin TM (người xử lý khảo sát)

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate(`/survey-requests/${id}`)}>
          <i className="ti ti-arrow-left" />
        </button>
        <h2 className="page-title" style={{ margin: 0 }}>
          {data.code || 'Xử lý Khảo sát'}
        </h2>
        {srBadge(data.status)}
        <span style={{ flex: 1 }} />
        {data.status === 'processing' && (
          <button className="btn ghost" onClick={async () => {
            try {
              const r = await api.post(`${API}/${id}/sync-options`)
              toast.success(r.data?.message || 'Đã lấy phương án từ khảo sát')
              loadProcess()
            } catch (e: any) { toast.error(e?.response?.data?.error?.message || 'Lỗi lấy phương án') }
          }}>
            <i className="ti ti-download" />Lấy từ khảo sát
          </button>
        )}
      </div>

      {/* Sub-header info */}
      <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 18, display: 'flex', gap: 20, flexWrap: 'wrap' }}>
        <span><i className="ti ti-calendar" style={{ marginRight: 4 }} />
          {data.request_date ? new Date(data.request_date).toLocaleDateString('vi-VN') : '—'}
        </span>
        <span><i className="ti ti-building" style={{ marginRight: 4 }} />{data.department || '—'}</span>
        <span><i className="ti ti-user" style={{ marginRight: 4 }} />{data.requester || '—'}</span>
      </div>

      {err && <div className="err" style={{ marginBottom: 12 }}>{err}</div>}
      {msg && <div style={{ color: 'var(--green)', fontSize: 13, marginBottom: 12 }}>{msg}</div>}

      {lines.length === 0 && (
        <div className="card" style={{ padding: 24, textAlign: 'center', color: 'var(--muted)' }}>
          Phiếu này chưa có dòng sản phẩm nào.
        </div>
      )}

      {lines.map((line, lineIdx) => {
        const ls = lineStates[lineIdx] || { supplierCode: '', filterGroup: line.item_group || '', search: '', availLines: [], loading: false, selectedAvailIds: new Set(), availPage: 0 }
        const shortName = line.requirement_detail
          ? (line.requirement_detail.length > 60 ? line.requirement_detail.slice(0, 57) + '...' : line.requirement_detail)
          : line.item_group || `Sản phẩm ${lineIdx + 1}`
        const options = line.options || []
        // Ẩn khỏi bảng trên những dòng khảo sát đã được gắn làm option (tránh trùng)
        const usedPsl = new Set(options.map((o: any) => o.product_survey_line_id))
        const availShown = (ls.availLines || []).filter((al: any) => !usedPsl.has(al.id))
        // Phân trang danh sách dòng khảo sát khả dụng
        const availTotalPages = Math.max(1, Math.ceil(availShown.length / AVAIL_PAGE_SIZE))
        const availPage = Math.min(ls.availPage || 0, availTotalPages - 1)
        const availPaged = availShown.slice(availPage * AVAIL_PAGE_SIZE, availPage * AVAIL_PAGE_SIZE + AVAIL_PAGE_SIZE)
        const setAvailPage = (p: number) => setLineStates((prev) => prev.map((s, i) => i === lineIdx ? { ...s, availPage: p } : s))

        return (
          <div key={line.id} className="card" style={{ padding: 18, marginBottom: 16 }}>
            {/* Card title */}
            <h3 className="sec-title" style={{ marginBottom: 6 }}>
              SẢN PHẨM {lineIdx + 1}: {shortName}
            </h3>
            <div style={{ fontSize: 12.5, color: 'var(--muted)', marginBottom: 4 }}>
              Phân loại: <b style={{ color: 'var(--navy)' }}>{line.item_group || '—'}</b>
              {' · '}SL dự kiến: <b style={{ color: 'var(--navy)' }}>{fmtNum(line.request_qty)} {line.uom || ''}</b>
              {' · '}Giá đề xuất: <b style={{ color: 'var(--navy)' }}>{fmtNum(line.proposed_price)}</b>
              {' · '}NSTM: <b style={{ color: 'var(--navy)' }}>{line.assignee_name || line.assignee || '—'}</b>
            </div>
            {(line.requirement_detail || line.other_requirement) && (
              <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 12 }}>
                {line.requirement_detail && <div><b>Thông số:</b> {line.requirement_detail}</div>}
                {line.other_requirement && <div><b>YC khác:</b> {line.other_requirement}</div>}
              </div>
            )}

            {!line.can_process && (
              <div style={{ fontSize: 12.5, color: 'var(--muted)', fontStyle: 'italic', margin: '4px 0 12px' }}>
                <i className="ti ti-lock" style={{ marginRight: 4 }} />Dòng do NSTM khác phụ trách — bạn chỉ xem, không gắn/xóa phương án.
              </div>
            )}
            {/* Bộ lọc: Phân loại + NCC + Tìm mã/tên SP — CHỈ dòng mình phụ trách mới gắn được option */}
            {line.can_process && (<div style={{ marginBottom: 14 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>
                <i className="ti ti-filter" style={{ marginRight: 4 }} />Tìm kết quả khảo sát để thêm option
              </div>
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
                <div style={{ width: 220 }}>
                  <Select
                    value={ls.filterGroup ? { value: ls.filterGroup, label: ls.filterGroup } : null}
                    options={groups.map((g) => ({ value: g, label: g }))}
                    onChange={(o: any) => fetchAvail(lineIdx, line.id, { filterGroup: o ? o.value : '' })}
                    isClearable placeholder="Phân loại..." styles={SEL_STYLES}
                    menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
                  />
                </div>
                <div style={{ width: 300 }}>
                  <Select
                    value={supplierOptions.find((o) => o.value === ls.supplierCode) || null}
                    options={supplierOptions}
                    onChange={(o: any) => fetchAvail(lineIdx, line.id, { supplierCode: o ? o.value : '' })}
                    isClearable placeholder="Nhà cung cấp (tùy chọn)..." styles={SEL_STYLES}
                    menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
                  />
                </div>
                <input value={ls.search || ''} onChange={(e) => onSearchChange(lineIdx, line.id, e.target.value)}
                  placeholder="Tìm mã / tên SP..." style={{ width: 220 }} />
                {ls.filterGroup !== (line.item_group || '') && (
                  <button className="btn ghost" style={{ height: 34, fontSize: 12, padding: '0 10px' }}
                    onClick={() => fetchAvail(lineIdx, line.id, { filterGroup: line.item_group || '' })}>
                    <i className="ti ti-rotate" />Về phân loại dòng
                  </button>
                )}
              </div>
            </div>)}

            {/* Bảng dòng khảo sát khả dụng theo bộ lọc — chỉ dòng mình phụ trách */}
            {line.can_process && (ls.supplierCode || ls.filterGroup || (ls.search || '').trim() || ls.loading || availShown.length > 0) && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
                  Kết quả khảo sát đã duyệt
                  {ls.filterGroup && <> · phân loại <span style={{ color: 'var(--teal)' }}>{ls.filterGroup}</span></>}
                  {ls.supplierCode && <> · NCC <span style={{ color: 'var(--teal)' }}>{ls.supplierCode}</span></>}:
                </div>
                {ls.loading ? (
                  <div style={{ color: 'var(--muted)', fontSize: 13 }}>Đang tải...</div>
                ) : availShown.length === 0 ? (
                  <div style={{ color: 'var(--muted)', fontSize: 13, fontStyle: 'italic' }}>
                    {ls.availLines.length > 0
                      ? 'Tất cả kết quả khớp đã được gắn.'
                      : 'Không tìm thấy kết quả khảo sát đã duyệt khớp bộ lọc.'}
                  </div>
                ) : (
                  <div className="items-scroll">
                    <table className="items-table" style={{ minWidth: 1092, tableLayout: 'fixed' }}>
                      <colgroup>
                        <col style={{ width: 40 }} />{/* chọn */}
                        <col style={{ width: 190 }} />{/* NCC */}
                        <col style={{ width: 230 }} />{/* Tên SP */}
                        <col style={{ width: 160 }} />{/* Spec */}
                        <col style={{ width: 90 }} />{/* Xuất xứ */}
                        <col style={{ width: 96 }} />{/* Giá */}
                        <col style={{ width: 80 }} />{/* MOQ */}
                        <col style={{ width: 64 }} />{/* ĐVT */}
                        <col style={{ width: 70 }} />{/* Lab */}
                        <col style={{ width: 72 }} />{/* Thêm */}
                      </colgroup>
                      <thead>
                        <tr>
                          <th></th>
                          <th style={{ textAlign: 'left' }}>NCC</th>
                          <th style={{ textAlign: 'left' }}>Tên SP</th>
                          <th style={{ textAlign: 'left' }}>Spec</th>
                          <th style={{ textAlign: 'left' }}>Xuất xứ</th>
                          <th style={{ textAlign: 'right' }}>Giá</th>
                          <th style={{ textAlign: 'right' }}>MOQ</th>
                          <th style={{ textAlign: 'left' }}>ĐVT</th>
                          <th style={{ textAlign: 'center' }}>Lab</th>
                          <th style={{ textAlign: 'center' }}>Thêm</th>
                        </tr>
                      </thead>
                      <tbody>
                        {availPaged.map((al) => (
                          <tr key={al.id}>
                            <td style={{ textAlign: 'center' }}>
                              <input
                                type="checkbox"
                                checked={ls.selectedAvailIds.has(al.id)}
                                onChange={(e) => {
                                  setLineStates((prev) =>
                                    prev.map((s, i) => {
                                      if (i !== lineIdx) return s
                                      const next = new Set(s.selectedAvailIds)
                                      if (e.target.checked) next.add(al.id)
                                      else next.delete(al.id)
                                      return { ...s, selectedAvailIds: next }
                                    })
                                  )
                                }}
                              />
                            </td>
                            <td title={al.supplier_name || al.supplier_code}>
                              {al.supplier_code || al.supplier_name ? (
                                <>
                                  <div style={{ fontWeight: 600, color: 'var(--navy)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{al.supplier_code || '—'}</div>
                                  {al.supplier_name && (
                                    <div style={{ fontSize: 11, color: 'var(--muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{al.supplier_name}</div>
                                  )}
                                </>
                              ) : '—'}
                            </td>
                            <td title={al.product_name}>
                              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'inline-block', maxWidth: '100%', verticalAlign: 'middle' }}>{al.product_name || '—'}</span>
                              {al.internal_code && <span style={{ color: 'var(--muted)', fontSize: 11, marginLeft: 4 }}>({al.internal_code})</span>}
                              {al.survey_item_group && al.survey_item_group !== line.item_group && (
                                <span className="badge warn" style={{ fontSize: 10, marginLeft: 6 }}
                                  title={`Khác phân loại dòng — khảo sát thuộc: ${al.survey_item_group}`}>≠ {al.survey_item_group}</span>
                              )}
                            </td>
                            <td title={al.spec}
                              style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {al.spec || '—'}
                            </td>
                            <td style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{al.origin || '—'}</td>
                            <td style={{ textAlign: 'right' }}>{fmtNum(al.price_by_volume)}</td>
                            <td style={{ textAlign: 'right' }}>{fmtNum(al.moq)}</td>
                            <td style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{al.quote_unit || '—'}</td>
                            <td style={{ textAlign: 'center' }}>
                              {al.lab_result
                                ? <span className="badge ok" style={{ fontSize: 11 }}>Có</span>
                                : <span className="badge gray" style={{ fontSize: 11 }}>—</span>}
                            </td>
                            <td style={{ textAlign: 'center' }}>
                              <button
                                className="btn ghost"
                                style={{ padding: '2px 8px', fontSize: 12, height: 26 }}
                                onClick={() => addOption(line.id, al.id)}
                              >
                                <i className="ti ti-plus" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    {availTotalPages > 1 && (
                      <div style={{ marginTop: 8 }}>
                        <Pagination page={availPage + 1} pageSize={AVAIL_PAGE_SIZE} total={availShown.length}
                          hideSize onChange={(p) => setAvailPage(p - 1)} />
                      </div>
                    )}
                  </div>
                )}

                {/* Thêm hàng loạt */}
                {availShown.length > 0 && ls.selectedAvailIds.size > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <button
                      className="btn"
                      style={{ fontSize: 13, height: 32, padding: '0 14px' }}
                      onClick={async () => {
                        for (const sid of Array.from(ls.selectedAvailIds)) {
                          await addOption(line.id, sid)
                        }
                        setLineStates((prev) =>
                          prev.map((s, i) => i === lineIdx ? { ...s, selectedAvailIds: new Set() } : s)
                        )
                      }}
                    >
                      <i className="ti ti-playlist-add" />
                      Thêm {ls.selectedAvailIds.size} dòng đã chọn làm option
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Options đã gắn */}
            <div>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>
                <i className="ti ti-list-check" style={{ marginRight: 4 }} />
                Options đã gắn ({options.length})
              </div>
              {options.length === 0 ? (
                <div style={{ color: 'var(--muted)', fontSize: 13, fontStyle: 'italic' }}>
                  Chưa có option nào — chọn NCC ở trên và thêm dòng khảo sát.
                </div>
              ) : (
                <div className="items-scroll">
                  <table className="items-table" style={{ minWidth: 1450, tableLayout: 'fixed' }}>
                    <colgroup>
                      <col style={{ width: 120 }} />{/* Option */}
                      <col style={{ width: 190 }} />{/* NCC (nội bộ) */}
                      <col style={{ width: 230 }} />{/* Tên SP */}
                      <col style={{ width: 160 }} />{/* Spec */}
                      <col style={{ width: 90 }} />{/* Xuất xứ */}
                      <col style={{ width: 96 }} />{/* Giá */}
                      <col style={{ width: 80 }} />{/* MOQ */}
                      <col style={{ width: 64 }} />{/* ĐVT */}
                      <col style={{ width: 230 }} />{/* Mã SP hệ thống */}
                      <col style={{ width: 130 }} />{/* Trạng thái */}
                      <col style={{ width: 60 }} />{/* Xóa */}
                    </colgroup>
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left' }}>Option</th>
                        <th style={{ textAlign: 'left' }}>NCC (nội bộ)</th>
                        <th style={{ textAlign: 'left' }}>Tên SP</th>
                        <th style={{ textAlign: 'left' }}>Spec</th>
                        <th style={{ textAlign: 'left' }}>Xuất xứ</th>
                        <th style={{ textAlign: 'right' }}>Giá</th>
                        <th style={{ textAlign: 'right' }}>MOQ</th>
                        <th style={{ textAlign: 'left' }}>ĐVT</th>
                        <th style={{ textAlign: 'left' }}>Mã SP hệ thống</th>
                        <th style={{ textAlign: 'center' }}>Trạng thái</th>
                        <th style={{ textAlign: 'center' }}>Xóa</th>
                      </tr>
                    </thead>
                    <tbody>
                      {options.map((opt) => (
                        <tr key={opt.id}>
                          <td style={{ whiteSpace: 'nowrap', fontSize: 12.5, color: 'var(--muted)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {opt.display_label || `Option #${opt.id}`}
                          </td>
                          <td>
                            <span
                              className="badge warn"
                              style={{ fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '100%', display: 'inline-block', verticalAlign: 'middle' }}
                              title="Thông tin nội bộ — không hiển thị với người YC"
                            >
                              {opt.supplier_name || opt.supplier_code || '—'}
                            </span>
                          </td>
                          <td title={opt.snap_product_name}
                            style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {opt.snap_product_name || '—'}
                          </td>
                          <td title={opt.snap_spec}
                            style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {opt.snap_spec || '—'}
                          </td>
                          <td style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{opt.snap_origin || '—'}</td>
                          <td style={{ textAlign: 'right' }}>{fmtNum(opt.snap_price_by_volume)}</td>
                          <td style={{ textAlign: 'right' }}>{fmtNum(opt.snap_moq)}</td>
                          <td style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{opt.snap_quote_unit || '—'}</td>
                          <td>
                            {line.can_process ? (
                              <div style={{ border: attempted && !opt.system_product_code ? '1px solid var(--red)' : 'none', borderRadius: 4 }}>
                                <ProductPicker code={opt.system_product_code}
                                  onPick={(prod) => setOptionProduct(line.id, opt.id, prod?.code || '')} />
                              </div>
                            ) : (
                              <span style={{ color: 'var(--muted)', fontSize: 12.5 }}>{opt.system_product_code || '—'}</span>
                            )}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            {opt.is_chosen
                              ? <span className="badge ok" style={{ fontSize: 11 }}>Người YC đã chọn</span>
                              : <span className="badge gray" style={{ fontSize: 11 }}>Chưa chọn</span>}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            {line.can_process ? (
                              <button
                                className="icon-btn"
                                title="Xóa option"
                                onClick={() => removeOption(line.id, opt.id)}
                              >
                                <i className="ti ti-trash" style={{ color: 'var(--red)' }} />
                              </button>
                            ) : <span style={{ color: 'var(--muted)' }}>—</span>}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )
      })}

      {/* Nút chốt hoàn thành — NSTM trực tiếp khảo sát (hoặc QL/Admin TM) */}
      {canProcess && lines.length > 0 && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 12, marginTop: 12, alignItems: 'center' }}>
          {!allHaveOptions && (
            <span style={{ fontSize: 13, color: 'var(--muted)' }}>
              Còn dòng chưa có phương án — khi chốt sẽ hỏi “chốt rỗng”
            </span>
          )}
          <button
            className="btn"
            disabled={completing}
            onClick={complete}
            style={{ opacity: completing ? 0.5 : 1 }}
          >
            <i className="ti ti-check" />
            Chốt hoàn thành khảo sát
          </button>
        </div>
      )}

      {/* Dialog: chốt rỗng các dòng chưa có phương án */}
      {emptyPrompt && (
        <div onClick={() => setEmptyPrompt(null)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(27,37,89,.3)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
          <div className="card" onClick={(e) => e.stopPropagation()} style={{ width: 520, maxWidth: '100%', padding: 20 }}>
            <h3 className="sec-title" style={{ marginTop: 0 }}>Chốt rỗng sản phẩm chưa có phương án</h3>
            <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
              Các sản phẩm sau <b>chưa có phương án</b>. Tick những sản phẩm <b>không tìm được NCC phù hợp</b> để <b>chốt rỗng</b> (coi như không có phương án).
              Sản phẩm KHÔNG tick + chưa có phương án sẽ chặn chốt (cần khảo sát tiếp).
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: '48vh', overflowY: 'auto' }}>
              {emptyPrompt.map((l) => (
                <label key={l.id} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '10px 12px', border: '1px solid var(--border)', borderRadius: 8, cursor: 'pointer' }}>
                  <input type="checkbox" style={{ marginTop: 3 }} checked={emptyChecked.has(l.id)}
                    onChange={(e) => setEmptyChecked((prev) => { const n = new Set(prev); if (e.target.checked) n.add(l.id); else n.delete(l.id); return n })} />
                  <span>
                    <div style={{ fontWeight: 600 }}>{l.item_group || 'Sản phẩm'}</div>
                    <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>{l.requirement_detail || '—'}</div>
                  </span>
                </label>
              ))}
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
              <button className="btn ghost" onClick={() => setEmptyPrompt(null)}>Hủy</button>
              <button className="btn" disabled={completing} onClick={() => doComplete([...emptyChecked])}>
                <i className="ti ti-check" />Chốt ({emptyChecked.size} chốt rỗng)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
