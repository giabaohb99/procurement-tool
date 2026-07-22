import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { toast } from '../components/toast'

// Trang chi tiết chứng từ: gom TOÀN BỘ chuỗi của 1 đơn mua hàng
// (PO → PYC → PKS → YCKS) từ /api/attachments/chain, nhóm theo nguồn rồi theo loại.
// Hỗ trợ: xem (ảnh/PDF inline), tải từng file, tải tất cả dạng .zip.
type ChainItem = {
  link_id: number; source: string; source_code: string; entity: string; entity_id: number
  doc_type: string; doc_type_label: string; filename: string; url: string; content_type: string; size: number
}

const SRC_ORDER = ['PO', 'PYC', 'PKS', 'YCKS']
const SRC_LABEL: Record<string, string> = {
  PO: 'Đơn mua hàng', PYC: 'Yêu cầu mua hàng', PKS: 'Phiếu khảo sát', YCKS: 'Yêu cầu báo giá',
}
const isImage = (it: ChainItem) => /^image\//.test(it.content_type || '')
const isPdf = (it: ChainItem) => it.content_type === 'application/pdf' || /\.pdf$/i.test(it.filename)
const fmtSize = (n: number) => (n > 1024 * 1024 ? (n / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(n / 1024)) + ' KB')

// Icon + màu theo định dạng file → nhận diện nhanh
function fileIcon(it: ChainItem): { icon: string; color: string } {
  const n = it.filename.toLowerCase()
  if (isPdf(it)) return { icon: 'ti-file-type-pdf', color: '#dc2626' }
  if (/\.(xlsx?|csv)$/.test(n)) return { icon: 'ti-file-type-xls', color: '#16a34a' }
  if (/\.(docx?)$/.test(n)) return { icon: 'ti-file-type-docx', color: '#2563eb' }
  return { icon: 'ti-file', color: 'var(--muted)' }
}

function groupBy<T>(arr: T[], key: (x: T) => string): Record<string, T[]> {
  return arr.reduce((acc, x) => { const k = key(x); (acc[k] ||= []).push(x); return acc }, {} as Record<string, T[]>)
}

function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; document.body.appendChild(a); a.click()
  a.remove(); URL.revokeObjectURL(url)
}

export default function Documents() {
  const [sp] = useSearchParams()
  const navigate = useNavigate()
  const po = sp.get('po')
  const [rows, setRows] = useState<ChainItem[]>([])
  const [loading, setLoading] = useState(false)
  const [preview, setPreview] = useState<ChainItem | null>(null)
  const [zipping, setZipping] = useState(false)

  useEffect(() => {
    if (!po) return
    setLoading(true)
    api.get('/api/attachments/chain', { params: { entity: 'purchase_order', entity_id: po } })
      .then((r) => setRows(r.data.data || []))
      .catch(() => setRows([]))
      .finally(() => setLoading(false))
  }, [po])

  async function downloadFile(it: ChainItem) {
    try {
      const r = await api.get(`/api/attachments/${it.link_id}/download`, { responseType: 'blob' })
      saveBlob(r.data, it.filename)
    } catch { toast.error('Tải file thất bại') }
  }

  async function downloadZip() {
    if (!po) return
    setZipping(true)
    try {
      const r = await api.get('/api/attachments/chain/zip', { params: { entity: 'purchase_order', entity_id: po }, responseType: 'blob' })
      const cd = String(r.headers['content-disposition'] || '')
      const m = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(cd)
      const name = m ? decodeURIComponent(m[1]) : `chung-tu-${po}.zip`
      saveBlob(r.data, name)
    } catch { toast.error('Tải ZIP thất bại (đơn có thể chưa có chứng từ)') }
    finally { setZipping(false) }
  }

  if (!po) {
    return (
      <div className="page">
        <div className="page-head"><h1>Chứng từ</h1></div>
        <div className="card" style={{ padding: 24, color: 'var(--muted)' }}>
          Chọn một đơn mua hàng để xem chứng từ (mở từ nút <b>Chi tiết</b> ở trang đơn mua hàng).
        </div>
      </div>
    )
  }

  const poCode = rows.find((r) => r.source === 'PO')?.source_code || `#${po}`
  const bySource = groupBy(rows, (r) => r.source)
  const sources = SRC_ORDER.filter((s) => bySource[s]?.length)

  return (
    <div className="page">
      <div className="page-head" style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 18 }}>
        <button className="btn ghost" onClick={() => navigate(`/purchase-orders/${po}`)}><i className="ti ti-arrow-left" /> Về đơn</button>
        <h1 style={{ margin: 0 }}>Chứng từ đơn {poCode}</h1>
        <span style={{ color: 'var(--muted)', fontSize: 13 }}>{rows.length} file</span>
        {rows.length > 0 && (
          <button className="btn" style={{ marginLeft: 'auto' }} onClick={downloadZip} disabled={zipping}>
            <i className="ti ti-file-zip" /> {zipping ? 'Đang nén…' : 'Tải tất cả (.zip)'}
          </button>
        )}
      </div>

      {loading && <div className="card" style={{ padding: 24 }}>Đang tải…</div>}
      {!loading && rows.length === 0 && <div className="card" style={{ padding: 24, color: 'var(--muted)' }}>Chưa có chứng từ nào trong chuỗi đơn này.</div>}

      {!loading && sources.map((src) => {
        const byType = groupBy(bySource[src], (r) => r.doc_type_label || '—')
        const code = bySource[src][0]?.source_code
        return (
          <div key={src} className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title"><i className="ti ti-folder" /> {SRC_LABEL[src] || src} {code && <span style={{ color: 'var(--muted)', fontWeight: 400 }}>· {code}</span>}</h3>
            {Object.entries(byType).map(([label, items]) => (
              <div key={label} style={{ marginTop: 14 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                  <span className="badge" style={{ background: '#eef2ff', color: '#3730a3', fontSize: 11.5, fontWeight: 600, padding: '2px 9px', borderRadius: 999 }}>{label}</span>
                  <span style={{ color: 'var(--muted)', fontSize: 12 }}>{items.length} file</span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {items.map((f) => {
                    const ic = fileIcon(f)
                    return (
                      <div key={f.link_id} className="doc-file-row">
                        {isImage(f)
                          ? <img src={f.url} alt="" onClick={() => setPreview(f)} style={{ width: 40, height: 40, objectFit: 'cover', borderRadius: 6, cursor: 'pointer', flexShrink: 0, border: '1px solid var(--border)' }} />
                          : <i className={'ti ' + ic.icon} style={{ fontSize: 24, color: ic.color, flexShrink: 0 }} />}
                        <span style={{ flex: 1, minWidth: 0, fontSize: 13, fontWeight: 500, color: 'var(--navy)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.filename}</span>
                        <span style={{ color: 'var(--muted)', fontSize: 12, flexShrink: 0 }}>{fmtSize(f.size)}</span>
                        <button className="btn ghost" style={{ padding: '3px 10px', flexShrink: 0 }} onClick={() => setPreview(f)}><i className="ti ti-eye" /> Xem</button>
                        <button className="btn ghost" style={{ padding: '3px 10px', flexShrink: 0 }} onClick={() => downloadFile(f)}><i className="ti ti-download" /> Tải</button>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        )
      })}

      {preview && (
        <div onClick={() => setPreview(null)} style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.7)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
          <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width: 900, maxWidth: '96vw', height: '90vh', background: '#fff', borderRadius: 12, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 16px', borderBottom: '1px solid var(--border)' }}>
              <span style={{ flex: 1, minWidth: 0, fontWeight: 600, color: 'var(--navy)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{preview.filename}</span>
              <button className="btn ghost" style={{ padding: '4px 10px' }} onClick={() => downloadFile(preview)}><i className="ti ti-download" /> Tải</button>
              <button className="icon-btn" onClick={() => setPreview(null)}><i className="ti ti-x" style={{ fontSize: 18 }} /></button>
            </div>
            <div style={{ flex: 1, background: '#f1f5f9', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'auto' }}>
              {isImage(preview) && <img src={preview.url} style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain' }} />}
              {!isImage(preview) && isPdf(preview) && <iframe src={preview.url} title={preview.filename} style={{ width: '100%', height: '100%', border: 'none' }} />}
              {!isImage(preview) && !isPdf(preview) && (
                <div style={{ textAlign: 'center', color: 'var(--muted)', padding: 24 }}>
                  <i className="ti ti-file-off" style={{ fontSize: 40 }} />
                  <div style={{ marginTop: 10, fontSize: 14 }}>Không xem trước được định dạng này.</div>
                  <button className="btn" style={{ marginTop: 12 }} onClick={() => downloadFile(preview)}><i className="ti ti-download" /> Tải về</button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
