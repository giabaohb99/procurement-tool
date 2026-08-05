import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { api } from '../api/client'
import { toast } from '../components/toast'
import Pagination from '../components/Pagination'
import DateInput from '../components/DateInput'
import { fmtDateTime } from '../utils/datetime'

export const IMPORT_MODULE: Record<number, string> = { 1: 'Khảo sát', 2: 'Đơn mua hàng' }
export const IMPORT_MODE: Record<number, string> = { 0: 'Chạy thử', 1: 'Ghi' }
export const IMPORT_STATUS: Record<number, { l: string; c: string }> = {
  0: { l: 'Chờ', c: 'gray' }, 1: { l: 'Đang chạy', c: 'warn' }, 2: { l: 'Xong', c: 'ok' }, 3: { l: 'Lỗi', c: 'err' },
  4: { l: 'Đã hoàn tác', c: 'gray' },
}
export const statusBadge = (s: number) => {
  const x = IMPORT_STATUS[s] || { l: '?', c: 'gray' }
  return <span className={'badge ' + x.c}>{x.l}</span>
}

const MODE_BADGE: Record<number, { bg: string; color: string; label: string }> = {
  0: { bg: '#f0f4ff', color: '#3b82f6', label: 'Chạy thử' },
  1: { bg: '#fef3c7', color: '#d97706', label: 'Ghi' },
}

const MODULE_STYLE: Record<number, { bg: string; color: string }> = {
  1: { bg: '#ecfdf5', color: '#059669' },
  2: { bg: '#eff6ff', color: '#2563eb' },
}

export default function ImportBatches() {
  const navigate = useNavigate()
  const { can } = useAuth()
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [fModule, setFModule] = useState('')
  const [fStatus, setFStatus] = useState('')
  const [fMode, setFMode] = useState('')
  const [fDateFrom, setFDateFrom] = useState('')
  const [fDateTo, setFDateTo] = useState('')
  const [fCreator, setFCreator] = useState('')
  const [fFilename, setFFilename] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [upModule, setUpModule] = useState(1)
  const [upMode, setUpMode] = useState(0)
  const [busy, setBusy] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [creators, setCreators] = useState<string[]>([])

  async function load() {
    const params: any = { page, page_size: pageSize }
    if (fModule) params.module = fModule
    if (fStatus) params.status = fStatus
    if (fMode) params.mode = fMode
    if (fDateFrom) params.date_from = fDateFrom
    if (fDateTo) params.date_to = fDateTo
    if (fCreator) params.created_by_name = fCreator
    if (fFilename) params.filename = fFilename
    try {
      const r = await api.get('/api/imports', { params })
      const data = r.data.data
      setRows(data.items || []); setTotal(data.total || 0)
      if (data.creators) setCreators(data.creators)
    } catch { /* interceptor toast */ }
  }
  useEffect(() => { load() }, [page, pageSize, fModule, fStatus, fMode, fDateFrom, fDateTo, fCreator, fFilename])
  // Poll nhẹ khi có batch đang chạy (để thấy cập nhật khi worker xong)
  useEffect(() => {
    if (!rows.some((r) => r.status <= 1)) return
    const t = setInterval(load, 4000)
    return () => clearInterval(t)
  }, [rows])

  // Debounce filename search
  const [fnInput, setFnInput] = useState('')
  useEffect(() => {
    const t = setTimeout(() => { setFFilename(fnInput); setPage(1) }, 400)
    return () => clearTimeout(t)
  }, [fnInput])

  function handleFilePick(file: File | null) {
    if (file && !file.name.toLowerCase().endsWith('.xlsx')) {
      toast.error('Chỉ nhận file .xlsx'); return
    }
    setSelectedFile(file)
  }

  async function doUpload() {
    const file = selectedFile
    if (!file) { toast.error('Chọn file .xlsx'); return }
    const fd = new FormData()
    fd.append('file', file); fd.append('module', String(upModule)); fd.append('mode', String(upMode))
    setBusy(true)
    try {
      await api.post('/api/imports', fd)
      toast.success('Đã nhận file — đang import nền, sẽ báo khi xong')
      setShowModal(false); setSelectedFile(null)
      if (fileRef.current) fileRef.current.value = ''
      setPage(1); load()
    } catch { /* interceptor toast */ } finally { setBusy(false) }
  }

  function openModal() {
    setSelectedFile(null); setUpModule(1); setUpMode(0)
    setShowModal(true)
  }

  function clearFilters() {
    setFModule(''); setFStatus(''); setFMode(''); setFDateFrom(''); setFDateTo(''); setFCreator(''); setFnInput(''); setFFilename(''); setPage(1)
  }

  const hasActiveFilters = fModule || fStatus || fMode || fDateFrom || fDateTo || fCreator || fFilename

  return (
    <div>
      {/* ===== HEADER ===== */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18, flexWrap: 'wrap' }}>
        <h2 className="page-title" style={{ margin: 0 }}>Quản lý Import</h2>
        <span style={{ flex: 1 }} />
        {can('import', 'create') && (
          <button className="btn" onClick={openModal} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <i className="ti ti-upload" />Import mới
          </button>
        )}
      </div>

      {/* ===== FILTER BAR ===== */}
      <div className="card" style={{ padding: '12px 16px', marginBottom: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          {/* Chức năng */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <label style={{ fontSize: 12, color: 'var(--muted)', whiteSpace: 'nowrap' }}>Chức năng:</label>
            <select value={fModule} onChange={(e) => { setFModule(e.target.value); setPage(1) }} style={{ minWidth: 125 }}>
              <option value="">Tất cả</option>
              <option value="1">Khảo sát</option>
              <option value="2">Đơn mua hàng</option>
            </select>
          </div>
          {/* Trạng thái */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <label style={{ fontSize: 12, color: 'var(--muted)', whiteSpace: 'nowrap' }}>Trạng thái:</label>
            <select value={fStatus} onChange={(e) => { setFStatus(e.target.value); setPage(1) }} style={{ minWidth: 120 }}>
              <option value="">Tất cả</option>
              <option value="0">Chờ</option>
              <option value="1">Đang chạy</option>
              <option value="2">Xong</option>
              <option value="3">Lỗi</option>
              <option value="4">Đã hoàn tác</option>
            </select>
          </div>
          {/* Chế độ */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <label style={{ fontSize: 12, color: 'var(--muted)', whiteSpace: 'nowrap' }}>Chế độ:</label>
            <select value={fMode} onChange={(e) => { setFMode(e.target.value); setPage(1) }} style={{ minWidth: 105 }}>
              <option value="">Tất cả</option>
              <option value="0">Chạy thử</option>
              <option value="1">Ghi</option>
            </select>
          </div>
          {/* Người tạo */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <label style={{ fontSize: 12, color: 'var(--muted)', whiteSpace: 'nowrap' }}>Người tạo:</label>
            <select value={fCreator} onChange={(e) => { setFCreator(e.target.value); setPage(1) }} style={{ minWidth: 140 }}>
              <option value="">Tất cả</option>
              {creators.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          {/* Từ ngày */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <label style={{ fontSize: 12, color: 'var(--muted)', whiteSpace: 'nowrap' }}>Từ:</label>
            <DateInput value={fDateFrom} onChange={(v) => { setFDateFrom(v); setPage(1) }}
              style={{ width: 135, fontSize: 13 }} />
          </div>
          {/* Đến ngày */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <label style={{ fontSize: 12, color: 'var(--muted)', whiteSpace: 'nowrap' }}>Đến:</label>
            <DateInput value={fDateTo} onChange={(v) => { setFDateTo(v); setPage(1) }}
              style={{ width: 135, fontSize: 13 }} />
          </div>
          {/* Tên file */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
            <label style={{ fontSize: 12, color: 'var(--muted)', whiteSpace: 'nowrap' }}>File:</label>
            <input type="text" value={fnInput} onChange={(e) => setFnInput(e.target.value)}
              placeholder="Tìm tên file..." style={{ width: 150, fontSize: 13 }} />
          </div>

          {hasActiveFilters && (
            <button className="btn ghost" style={{ fontSize: 12, padding: '4px 10px', height: 30 }} onClick={clearFilters}>
              <i className="ti ti-x" /> Xoá lọc
            </button>
          )}

          <span style={{ flex: 1 }} />
          <span style={{ fontSize: 12.5, color: 'var(--muted)', whiteSpace: 'nowrap' }}>{total} kết quả</span>
        </div>
      </div>

      {/* ===== TABLE ===== */}
      <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              <th style={{ width: 46, textAlign: 'center' }}>#</th>
              <th>Thời gian</th>
              <th>Người import</th>
              <th>Chức năng</th>
              <th>Tên file</th>
              <th style={{ textAlign: 'center' }}>Chế độ</th>
              <th style={{ textAlign: 'center' }}>Trạng thái</th>
              <th style={{ textAlign: 'right' }}>Tạo</th>
              <th style={{ textAlign: 'right' }}>Cập nhật</th>
              <th style={{ textAlign: 'right' }}>Bỏ qua</th>
              <th style={{ textAlign: 'right' }}>Cảnh báo</th>
              <th style={{ textAlign: 'right' }}>Rà soát</th>
              <th style={{ textAlign: 'right' }}>Lỗi</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const mb = MODE_BADGE[r.mode] || { bg: '#f1f5f9', color: '#64748b', label: r.mode }
              const ms = MODULE_STYLE[r.module] || { bg: '#f1f5f9', color: '#64748b' }
              return (
              <tr key={r.id} className="clickable" onClick={() => navigate(`/import-batches/${r.id}`)}>
                <td style={{ textAlign: 'center', color: 'var(--muted)', fontSize: 12 }}>{r.id}</td>
                <td style={{ whiteSpace: 'nowrap' }}>{fmtDateTime(r.created_at)}</td>
                <td>{r.created_by_name}</td>
                <td>
                  <span style={{
                    padding: '2px 8px', borderRadius: 6, fontSize: 12.5, fontWeight: 600,
                    background: ms.bg, color: ms.color
                  }}>
                    {IMPORT_MODULE[r.module] || r.module}
                  </span>
                </td>
                <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={r.filename}>
                  {r.filename}
                </td>
                <td style={{ textAlign: 'center' }}>
                  <span style={{
                    display: 'inline-flex', alignItems: 'center', height: 22, padding: '0 8px',
                    borderRadius: 12, fontSize: 11, fontWeight: 600,
                    background: mb.bg, color: mb.color
                  }}>{mb.label}</span>
                </td>
                <td style={{ textAlign: 'center' }}>{statusBadge(r.status)}</td>
                <td style={{ textAlign: 'right', fontWeight: r.created_count ? 600 : 400, color: r.created_count ? '#15803d' : undefined }}>{r.created_count}</td>
                <td style={{ textAlign: 'right', fontWeight: r.updated_count ? 600 : 400, color: r.updated_count ? '#2563eb' : undefined }}>{r.updated_count}</td>
                <td style={{ textAlign: 'right' }}>{r.skipped_count}</td>
                <td style={{ textAlign: 'right', fontWeight: r.warning_count ? 600 : 400, color: r.warning_count ? '#d97706' : undefined }}>{r.warning_count}</td>
                <td style={{ textAlign: 'right', fontWeight: r.review_count ? 600 : 400, color: r.review_count ? '#7c3aed' : undefined }}>{r.review_count}</td>
                <td style={{ textAlign: 'right', fontWeight: r.error_count ? 600 : 400, color: r.error_count ? '#dc2626' : undefined }}>{r.error_count}</td>
              </tr>
            )})}
            {rows.length === 0 && <tr><td colSpan={13} style={{ textAlign: 'center', color: 'var(--muted)', padding: 28 }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <i className="ti ti-database-off" style={{ fontSize: 32, opacity: 0.4 }} />
                <span>Chưa có lần import nào</span>
                {can('import', 'create') && (
                  <button className="btn ghost" style={{ fontSize: 13 }} onClick={openModal}>
                    <i className="ti ti-upload" /> Tạo import đầu tiên
                  </button>
                )}
              </div>
            </td></tr>}
          </tbody>
        </table>
      </div>
      <Pagination page={page} pageSize={pageSize} total={total} onChange={(p, ps) => { setPage(p); setPageSize(ps) }} />

      {/* ===== MODAL IMPORT ===== */}
      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px', backdropFilter: 'blur(3px)' }}
          onClick={() => setShowModal(false)}>
          <div className="card" style={{ width: 540, maxWidth: '100%', padding: 0, overflow: 'hidden', borderRadius: 16, boxShadow: '0 20px 60px rgba(15,23,42,.18)' }}
            onClick={(e) => e.stopPropagation()}>

            {/* Header */}
            <div style={{ padding: '20px 24px 16px', borderBottom: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 40, height: 40, borderRadius: 12, background: 'linear-gradient(135deg, #0ea5e9, #06b6d4)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <i className="ti ti-file-upload" style={{ color: '#fff', fontSize: 20 }} />
              </div>
              <div>
                <h3 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: 'var(--navy)' }}>Import dữ liệu Excel</h3>
                <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2 }}>Tải lên file .xlsx để nhập dữ liệu vào hệ thống</div>
              </div>
              <span style={{ flex: 1 }} />
              <button onClick={() => setShowModal(false)} style={{ border: 'none', background: 'none', cursor: 'pointer', padding: 6, borderRadius: 8, color: 'var(--muted)', fontSize: 18 }}
                onMouseEnter={e => (e.currentTarget.style.background = '#f1f5f9')} onMouseLeave={e => (e.currentTarget.style.background = 'none')}>
                <i className="ti ti-x" />
              </button>
            </div>

            {/* Body */}
            <div style={{ padding: '20px 24px' }}>
              {/* Chức năng + Chế độ */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
                <div>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--navy)', marginBottom: 6 }}>Chức năng</label>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {[{ v: 1, l: 'Khảo sát', bg: '#ecfdf5', bc: '#059669' },
                      { v: 2, l: 'Đơn mua hàng', bg: '#eff6ff', bc: '#2563eb' }].map(opt => (
                      <button key={opt.v} onClick={() => setUpModule(opt.v)}
                        style={{
                          flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                          height: 40, borderRadius: 10, fontSize: 13, fontWeight: 600, cursor: 'pointer',
                          border: upModule === opt.v ? `2px solid ${opt.bc}` : '1.5px solid var(--border)',
                          background: upModule === opt.v ? opt.bg : '#fff',
                          color: upModule === opt.v ? opt.bc : 'var(--muted)',
                          transition: 'all 0.15s ease',
                        }}>
                        {opt.l}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--navy)', marginBottom: 6 }}>Chế độ</label>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {[{ v: 0, l: 'Chạy thử', c: '#3b82f6', bg: '#eff6ff' },
                      { v: 1, l: 'Ghi', c: '#d97706', bg: '#fef3c7' }].map(opt => (
                      <button key={opt.v} onClick={() => setUpMode(opt.v)}
                        style={{
                          flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
                          height: 40, borderRadius: 10, fontSize: 13, fontWeight: 600, cursor: 'pointer',
                          border: upMode === opt.v ? `2px solid ${opt.c}` : '1.5px solid var(--border)',
                          background: upMode === opt.v ? opt.bg : '#fff',
                          color: upMode === opt.v ? opt.c : 'var(--muted)',
                          transition: 'all 0.15s ease',
                        }}>
                        {opt.l}
                      </button>
                    ))}
                  </div>
                </div>
              </div>

              {/* Dropzone */}
              <label style={{ display: 'block', fontSize: 13, fontWeight: 600, color: 'var(--navy)', marginBottom: 6 }}>File Excel (.xlsx)</label>
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={(e) => { e.preventDefault(); setDragOver(false); handleFilePick(e.dataTransfer.files[0]) }}
                onClick={() => fileRef.current?.click()}
                style={{
                  border: dragOver ? '2px dashed var(--teal)' : selectedFile ? '2px solid #06b6d4' : '2px dashed #d1d5db',
                  borderRadius: 14, padding: selectedFile ? '16px 20px' : '28px 20px',
                  textAlign: 'center', cursor: 'pointer',
                  background: dragOver ? '#f0fdfa' : selectedFile ? '#f0fdfa' : '#fafbfc',
                  transition: 'all 0.2s ease',
                }}>
                <input type="file" accept=".xlsx" ref={fileRef} style={{ display: 'none' }}
                  onChange={(e) => handleFilePick(e.target.files?.[0] || null)} />
                {selectedFile ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div style={{ width: 44, height: 44, borderRadius: 12, background: '#dcfce7', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <i className="ti ti-file-check" style={{ fontSize: 22, color: '#16a34a' }} />
                    </div>
                    <div style={{ textAlign: 'left', flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--navy)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{selectedFile.name}</div>
                      <div style={{ fontSize: 12, color: 'var(--muted)' }}>{(selectedFile.size / 1024).toFixed(1)} KB</div>
                    </div>
                    <button onClick={(e) => { e.stopPropagation(); setSelectedFile(null); if (fileRef.current) fileRef.current.value = '' }}
                      style={{ border: 'none', background: '#fee2e2', color: '#dc2626', width: 30, height: 30, borderRadius: 8, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <i className="ti ti-x" style={{ fontSize: 15 }} />
                    </button>
                  </div>
                ) : (
                  <>
                    <div style={{ marginBottom: 8 }}>
                      <i className="ti ti-cloud-upload" style={{ fontSize: 34, color: dragOver ? 'var(--teal)' : '#94a3b8' }} />
                    </div>
                    <div style={{ fontSize: 13.5, fontWeight: 600, color: 'var(--navy)' }}>Kéo thả file vào đây hoặc bấm để chọn</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>Chỉ nhận file .xlsx (Excel)</div>
                  </>
                )}
              </div>

              {/* Ghi chú chế độ */}
              {upMode === 0 && (
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginTop: 14, padding: '10px 14px', background: '#eff6ff', borderRadius: 10, border: '1px solid #bfdbfe' }}>
                  <i className="ti ti-info-circle" style={{ color: '#3b82f6', fontSize: 16, marginTop: 1, flexShrink: 0 }} />
                  <div style={{ fontSize: 12.5, color: '#1e40af', lineHeight: 1.5 }}>
                    <b>Chạy thử (Dry-run):</b> Hệ thống sẽ kiểm tra toàn bộ dữ liệu trong file nhưng <b>chưa ghi vào CSDL</b>. Bạn có thể xem báo cáo cảnh báo/lỗi trước khi quyết định ghi thật.
                  </div>
                </div>
              )}
              {upMode === 1 && (
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginTop: 14, padding: '10px 14px', background: '#fef3c7', borderRadius: 10, border: '1px solid #fcd34d' }}>
                  <i className="ti ti-alert-triangle" style={{ color: '#d97706', fontSize: 16, marginTop: 1, flexShrink: 0 }} />
                  <div style={{ fontSize: 12.5, color: '#92400e', lineHeight: 1.5 }}>
                    <b>Chế độ Ghi:</b> Dữ liệu sẽ được <b>ghi thực tế</b> vào hệ thống. Nên chạy thử trước để kiểm tra cảnh báo. Có thể hoàn tác sau khi import.
                  </div>
                </div>
              )}
            </div>

            {/* Footer */}
            <div style={{ padding: '14px 24px 20px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <button className="btn ghost" onClick={() => setShowModal(false)} style={{ height: 40, padding: '0 18px', borderRadius: 10 }}>Huỷ</button>
              <button className="btn" disabled={busy || !selectedFile} onClick={doUpload}
                style={{ height: 40, padding: '0 22px', borderRadius: 10, display: 'flex', alignItems: 'center', gap: 6, opacity: !selectedFile ? 0.5 : 1 }}>
                <i className="ti ti-upload" />{busy ? 'Đang gửi...' : 'Bắt đầu import'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
