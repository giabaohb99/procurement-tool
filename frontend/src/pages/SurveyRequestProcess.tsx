import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { toast } from '../components/toast'
import Select from 'react-select'

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
}

interface ProcessOption {
  id: number
  public_id: string
  display_label: string
  is_chosen: boolean
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
  availLines: AvailSurveyLine[]
  loading: boolean
  selectedAvailIds: Set<number>
}

export default function SurveyRequestProcess() {
  const { id } = useParams()
  const { can } = useAuth()
  const navigate = useNavigate()

  const [data, setData]           = useState<ProcessData | null>(null)
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [lineStates, setLineStates] = useState<LineState[]>([])
  const [err, setErr]             = useState('')
  const [msg, setMsg]             = useState('')
  const [forbidden, setForbidden] = useState(false)
  const [completing, setCompleting] = useState(false)

  const supplierOptions = suppliers.map((s) => ({
    value: s.code,
    label: `${s.name} (${s.code})`,
  }))

  async function loadProcess() {
    try {
      const r = await api.get(`${API}/${id}/process`)
      const d: ProcessData = r.data.data
      setData(d)
      // Reset per-line state, preserving supplier selection
      setLineStates((prev) =>
        (d.lines || []).map((_, i) => ({
          supplierCode: prev[i]?.supplierCode || '',
          availLines:   prev[i]?.availLines   || [],
          loading:      false,
          selectedAvailIds: new Set<number>(),
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
    loadProcess()
  }, [id])

  async function fetchAvailLines(lineIdx: number, lineId: number, supplierCode: string) {
    if (!supplierCode) {
      setLineStates((prev) =>
        prev.map((s, i) => i === lineIdx ? { ...s, availLines: [], supplierCode: '' } : s)
      )
      return
    }
    setLineStates((prev) =>
      prev.map((s, i) => i === lineIdx ? { ...s, loading: true, supplierCode, availLines: [], selectedAvailIds: new Set() } : s)
    )
    try {
      const r = await api.get(`${API}/${id}/lines/${lineId}/available-survey-lines`, {
        params: { supplier_code: supplierCode },
      })
      setLineStates((prev) =>
        prev.map((s, i) => i === lineIdx ? { ...s, loading: false, availLines: r.data.data || [] } : s)
      )
    } catch {
      setLineStates((prev) =>
        prev.map((s, i) => i === lineIdx ? { ...s, loading: false, availLines: [] } : s)
      )
    }
  }

  async function addOption(lineId: number, surveyLineId: number) {
    try {
      await api.post(`${API}/${id}/lines/${lineId}/options`, { product_survey_line_id: surveyLineId })
      await loadProcess()
      toast.success('Đã thêm phương án')
    } catch { /* lỗi đã hiện popup từ interceptor */ }
  }

  async function removeOption(lineId: number, optionId: number) {
    if (!confirm('Xóa phương án này?')) return
    try {
      await api.delete(`${API}/${id}/lines/${lineId}/options/${optionId}`)
      await loadProcess()
      toast.success('Đã xóa phương án')
    } catch { /* lỗi đã hiện popup từ interceptor */ }
  }

  async function complete() {
    if (!confirm('Chốt hoàn thành khảo sát? Hành động này không thể hoàn tác.')) return
    setCompleting(true)
    try {
      await api.post(`${API}/${id}/complete`)
      toast.success('Đã chốt hoàn thành khảo sát')
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
        const ls = lineStates[lineIdx] || { supplierCode: '', availLines: [], loading: false, selectedAvailIds: new Set() }
        const shortName = line.requirement_detail
          ? (line.requirement_detail.length > 60 ? line.requirement_detail.slice(0, 57) + '...' : line.requirement_detail)
          : line.item_group || `Sản phẩm ${lineIdx + 1}`
        const options = line.options || []
        // Ẩn khỏi bảng trên những dòng khảo sát đã được gắn làm option (tránh trùng)
        const usedPsl = new Set(options.map((o: any) => o.product_survey_line_id))
        const availShown = (ls.availLines || []).filter((al: any) => !usedPsl.has(al.id))

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

            {/* Chọn NCC */}
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 6 }}>
                <i className="ti ti-building-store" style={{ marginRight: 4 }} />Chọn Nhà cung cấp để thêm option
              </div>
              <div style={{ maxWidth: 420 }}>
                <Select
                  value={supplierOptions.find((o) => o.value === ls.supplierCode) || null}
                  options={supplierOptions}
                  onChange={(o: any) => fetchAvailLines(lineIdx, line.id, o ? o.value : '')}
                  isClearable
                  placeholder="Tìm / chọn NCC..."
                  styles={{
                    control: (b) => ({ ...b, minHeight: 40, borderRadius: 12, borderColor: '#E9EDF7' }),
                    menu: (b) => ({ ...b, zIndex: 9999 }),
                    menuPortal: (b) => ({ ...b, zIndex: 9999 }),
                  }}
                  menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
                />
              </div>
            </div>

            {/* Bảng dòng khảo sát có sẵn từ NCC đã chọn */}
            {ls.supplierCode && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 6 }}>
                  Dòng khảo sát đã duyệt của NCC{' '}
                  <span style={{ color: 'var(--teal)' }}>{ls.supplierCode}</span>:
                </div>
                {ls.loading ? (
                  <div style={{ color: 'var(--muted)', fontSize: 13 }}>Đang tải...</div>
                ) : availShown.length === 0 ? (
                  <div style={{ color: 'var(--muted)', fontSize: 13, fontStyle: 'italic' }}>
                    {ls.availLines.length > 0
                      ? 'Tất cả dòng khảo sát của NCC này đã được gắn.'
                      : 'Chưa có dòng khảo sát đã duyệt cho NCC này.'}
                  </div>
                ) : (
                  <div className="items-scroll">
                    <table className="items-table" style={{ minWidth: 780 }}>
                      <thead>
                        <tr>
                          <th style={{ width: 36 }}></th>
                          <th style={{ textAlign: 'left' }}>Tên SP</th>
                          <th style={{ textAlign: 'left' }}>Spec</th>
                          <th style={{ textAlign: 'left' }}>Xuất xứ</th>
                          <th style={{ textAlign: 'right' }}>Giá</th>
                          <th style={{ textAlign: 'right' }}>MOQ</th>
                          <th style={{ textAlign: 'left' }}>ĐVT</th>
                          <th style={{ textAlign: 'center' }}>Lab</th>
                          <th style={{ width: 80, textAlign: 'center' }}>Thêm</th>
                        </tr>
                      </thead>
                      <tbody>
                        {availShown.map((al) => (
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
                            <td title={al.product_name}
                              style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {al.product_name || '—'}
                            </td>
                            <td title={al.spec}
                              style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                              {al.spec || '—'}
                            </td>
                            <td>{al.origin || '—'}</td>
                            <td style={{ textAlign: 'right' }}>{fmtNum(al.price_by_volume)}</td>
                            <td style={{ textAlign: 'right' }}>{fmtNum(al.moq)}</td>
                            <td>{al.quote_unit || '—'}</td>
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
                  <table className="items-table" style={{ minWidth: 760 }}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left' }}>Option</th>
                        <th style={{ textAlign: 'left' }}>Tên SP</th>
                        <th style={{ textAlign: 'left' }}>Spec</th>
                        <th style={{ textAlign: 'right' }}>Giá</th>
                        <th style={{ textAlign: 'right' }}>MOQ</th>
                        <th style={{ textAlign: 'left' }}>NCC (nội bộ)</th>
                        <th style={{ textAlign: 'center' }}>Trạng thái</th>
                        <th style={{ width: 60, textAlign: 'center' }}>Xóa</th>
                      </tr>
                    </thead>
                    <tbody>
                      {options.map((opt) => (
                        <tr key={opt.id}>
                          <td style={{ whiteSpace: 'nowrap', fontSize: 12.5, color: 'var(--muted)' }}>
                            {opt.display_label || `Option #${opt.id}`}
                          </td>
                          <td title={opt.snap_product_name}
                            style={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {opt.snap_product_name || '—'}
                          </td>
                          <td title={opt.snap_spec}
                            style={{ maxWidth: 130, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                            {opt.snap_spec || '—'}
                          </td>
                          <td style={{ textAlign: 'right' }}>{fmtNum(opt.snap_price_by_volume)}</td>
                          <td style={{ textAlign: 'right' }}>{fmtNum(opt.snap_moq)}</td>
                          <td>
                            <span
                              className="badge warn"
                              style={{ fontSize: 11 }}
                              title="Thông tin nội bộ — không hiển thị với người YC"
                            >
                              {opt.supplier_name || opt.supplier_code || '—'}
                            </span>
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            {opt.is_chosen
                              ? <span className="badge ok" style={{ fontSize: 11 }}>Người YC đã chọn</span>
                              : <span className="badge gray" style={{ fontSize: 11 }}>Chưa chọn</span>}
                          </td>
                          <td style={{ textAlign: 'center' }}>
                            <button
                              className="icon-btn"
                              title="Xóa option"
                              onClick={() => removeOption(line.id, opt.id)}
                            >
                              <i className="ti ti-trash" style={{ color: 'var(--red)' }} />
                            </button>
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
              Còn dòng sản phẩm chưa có option
            </span>
          )}
          <button
            className="btn"
            disabled={!allHaveOptions || completing}
            onClick={complete}
            style={{ opacity: allHaveOptions ? 1 : 0.5 }}
          >
            <i className="ti ti-check" />
            Chốt hoàn thành khảo sát
          </button>
        </div>
      )}
    </div>
  )
}
