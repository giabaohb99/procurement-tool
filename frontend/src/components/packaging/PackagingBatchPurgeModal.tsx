import { useEffect, useState } from 'react'
import { fetchBatchPurgePreview, purgeBatchData } from '../../api/packaging-cost'
import type { PackagingBatchPurgePreview } from '../../api/packaging-cost-types'
import { toast } from '../toast'

/**
 * duoc-CR-784 phase 07 — hộp thoại "Xóa dữ liệu của lô này" (lô Định mức bao bì / Báo giá VTBB / Sổ Misa): xem trước số dòng sẽ xóa,
 * dòng đã sửa tay sau khi nhập tách riêng (mặc định giữ lại), rồi mới xóa. Chữ khớp bản v2 (`import-batch-purge-dialog.tsx`).
 */
export default function PackagingBatchPurgeModal({ batchId, open, onClose, onDone }: {
  batchId: number | string; open: boolean; onClose: () => void; onDone: () => void
}) {
  const [data, setData] = useState<PackagingBatchPurgePreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [failed, setFailed] = useState(false)
  const [includeEdited, setIncludeEdited] = useState(false)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!open) return
    setData(null); setFailed(false); setIncludeEdited(false); setLoading(true)
    fetchBatchPurgePreview(batchId).then(setData).catch(() => setFailed(true)).finally(() => setLoading(false))
  }, [open, batchId])

  if (!open) return null
  const willDelete = data ? data.untouched + (includeEdited ? data.edited : 0) : 0

  async function run() {
    setBusy(true)
    try {
      const res = await purgeBatchData(batchId, includeEdited)
      toast.success(`Đã xóa ${res.deleted} dòng của lô nhập`)
      onDone()
    } catch { /* interceptor đã hiện thông báo lỗi */ } finally { setBusy(false) }
  }

  return (
    <div className="confirm-modal-overlay" onClick={() => !busy && onClose()}>
      <div className="confirm-modal" onClick={(e) => e.stopPropagation()}>
        <div className="confirm-modal-icon" style={{ color: '#ef4444' }}><i className="ti ti-alert-triangle" /></div>
        <h3 className="confirm-modal-title">Xóa dữ liệu của lô này?</h3>
        <div className="confirm-modal-message" style={{ textAlign: 'left' }}>
          {loading && <p>Đang đếm số dòng…</p>}
          {failed && <p style={{ color: '#dc2626' }}>Không xem trước được số dòng của lô.</p>}
          {data && data.total === 0 && <p>Lô này không còn dòng dữ liệu nào để xóa.</p>}
          {data && data.total > 0 && (
            <>
              <p>Sẽ xóa <b>{data.untouched}</b> {data.target_label} do lô này nhập.</p>
              {data.edited > 0 && (
                <div style={{ border: '1px solid #fcd34d', background: '#fffbeb', borderRadius: 8, padding: 8, margin: '8px 0' }}>
                  <p style={{ margin: 0 }}>Có <b>{data.edited}</b> dòng đã được sửa tay sau khi nhập — mặc định được <b>giữ lại</b>.</p>
                  <label style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 6, cursor: 'pointer' }}>
                    <input type="checkbox" checked={includeEdited} onChange={(e) => setIncludeEdited(e.target.checked)} />
                    Xóa luôn {data.edited} dòng đã sửa tay
                  </label>
                </div>
              )}
              {data.recomputes_cutoff && <p>Mốc sổ Misa sẽ được tính lại theo các dòng còn lại.</p>}
              <p>Hành động này không thể đảo ngược.</p>
            </>
          )}
        </div>
        <div className="confirm-modal-actions">
          <button className="btn secondary" style={{ color: 'var(--muted)', borderColor: '#e2e8f0' }} disabled={busy} onClick={onClose}>Hủy</button>
          <button className="btn" style={{ background: '#e11d48', borderColor: '#e11d48', color: '#fff' }}
            disabled={busy || willDelete === 0} onClick={run}>
            {busy ? 'Đang xóa…' : willDelete > 0 ? `Xóa ${willDelete} dòng` : 'Xóa'}
          </button>
        </div>
      </div>
    </div>
  )
}
