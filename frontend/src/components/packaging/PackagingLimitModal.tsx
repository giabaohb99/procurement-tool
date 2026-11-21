import { useEffect, useState } from 'react'
import NumberInput from '../NumberInput'
import { toast } from '../toast'
import { fetchPriceLimit, savePriceLimit } from '../../api/packaging-cost'
import type { PackagingPriceLimit } from '../../api/packaging-cost-types'
import { PRICE_DECIMALS } from '../../utils/money'
import PackagingModal from './PackagingModal'

/**
 * Hộp thoại đặt ngưỡng giá SÀN / TRẦN cho một mã (một dòng mỗi mã). Ô bỏ trống = không đặt phía đó.
 * Tra ngưỡng hiện có bằng ĐÚNG mã (bộ lọc của danh sách là LIKE) — xem `fetchPriceLimit`.
 */
export default function PackagingLimitModal({
  code, name, onClose, onSaved,
}: {
  code: string
  name?: string
  onClose: () => void
  onSaved: () => void
}) {
  const [existing, setExisting] = useState<PackagingPriceLimit | null>(null)
  const [loading, setLoading] = useState(true)
  const [floor, setFloor] = useState(0)
  const [ceiling, setCeiling] = useState(0)
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let alive = true
    fetchPriceLimit(code)
      .then((lim) => {
        if (!alive) return
        setExisting(lim)
        setFloor(Number(lim?.floor_price ?? 0))
        setCeiling(Number(lim?.ceiling_price ?? 0))
        setNote(lim?.note ?? '')
      })
      .catch(() => { if (alive) setError('Không tải được ngưỡng hiện có — thử đóng rồi mở lại.') })
      .finally(() => { if (alive) setLoading(false) })
    return () => { alive = false }
  }, [code])

  async function submit() {
    if (busy || loading) return
    //  Ô xóa trắng trả 0 → coi là "không đặt" (gửi null), không phải ngưỡng 0 đồng.
    const floorPrice = floor > 0 ? floor : null
    const ceilingPrice = ceiling > 0 ? ceiling : null
    if (floorPrice != null && ceilingPrice != null && floorPrice > ceilingPrice) {
      return setError('Giá sàn không được lớn hơn giá trần.')
    }
    setError('')
    setBusy(true)
    try {
      await savePriceLimit(existing?.id ?? null, {
        product_code: code, floor_price: floorPrice, ceiling_price: ceilingPrice, note: note.trim(),
      })
      toast.success('Đã lưu ngưỡng giá')
      onSaved()
      onClose()
    } catch { /* interceptor đã hiện thông báo lỗi */ } finally { setBusy(false) }
  }

  return (
    <PackagingModal title={`Ngưỡng giá ${code}`} onClose={onClose} busy={busy} maxWidth={440}
      subtitle={name || 'Đặt giá sàn / trần để cảnh báo khi giá mua hoặc báo giá ra ngoài khoảng.'}
      footer={<>
        <button className="btn ghost" onClick={onClose} disabled={busy}>Hủy</button>
        <button className="btn" onClick={submit} disabled={busy || loading}>{busy ? 'Đang lưu…' : 'Lưu ngưỡng'}</button>
      </>}>
      {loading ? <div className="pkg-hint">Đang tải…</div> : (
        <form className="pkg-form" onSubmit={(e) => { e.preventDefault(); submit() }}>
          <div>
            <label>Giá sàn</label>
            <NumberInput value={floor} placeholder="Không đặt" maxDecimals={PRICE_DECIMALS} onChange={setFloor} />
          </div>
          <div>
            <label>Giá trần</label>
            <NumberInput value={ceiling} placeholder="Không đặt" maxDecimals={PRICE_DECIMALS} onChange={setCeiling} />
          </div>
          <div className="full">
            <label>Ghi chú</label>
            <textarea value={note} onChange={(e) => setNote(e.target.value)} />
          </div>
          {error && <div className="full pkg-err">{error}</div>}
        </form>
      )}
      {loading && error && <div className="pkg-err">{error}</div>}
    </PackagingModal>
  )
}
