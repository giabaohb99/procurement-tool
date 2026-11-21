import { useState } from 'react'
import NumberInput from '../NumberInput'
import { toast } from '../toast'
import { createQuote } from '../../api/packaging-cost'
import { PRICE_DECIMALS } from '../../utils/money'
import PackagingModal from './PackagingModal'

/** Ngày hôm nay theo giờ máy (YYYY-MM-DD) cho ô ngày hiệu lực. */
function todayIso(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/**
 * Hộp thoại "Báo giá mới" của một mã VTBB (mở từ dòng Bảng giá, hoặc từ nút "Báo giá mới" — khi đó chưa khóa mã).
 * Giá VNĐ chưa VAT. Báo giá có ngày hiệu lực ở tương lai VẪN tính ngay là giá mới (để xem trước tác động).
 */
export default function PackagingQuoteModal({
  defaultCode, onClose, onSaved,
}: {
  defaultCode?: string
  onClose: () => void
  onSaved: () => void
}) {
  const [code, setCode] = useState(defaultCode ?? '')
  const [supplier, setSupplier] = useState('')
  const [price, setPrice] = useState(0)
  const [vat, setVat] = useState(0)
  const [validFrom, setValidFrom] = useState(todayIso())
  const [note, setNote] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const locked = !!defaultCode

  async function submit() {
    if (busy) return
    if (!code.trim()) return setError('Nhập mã vật tư bao bì.')
    if (!(price > 0)) return setError('Nhập đơn giá báo giá (lớn hơn 0).')
    if (!validFrom) return setError('Chọn ngày hiệu lực.')
    setError('')
    setBusy(true)
    try {
      await createQuote({
        product_code: code.trim().toUpperCase(), supplier_code: supplier.trim().toUpperCase(),
        price, vat, valid_from: validFrom, note: note.trim(),
      })
      toast.success('Đã lưu báo giá')
      onSaved()
      onClose()
    } catch { /* interceptor đã hiện thông báo lỗi */ } finally { setBusy(false) }
  }

  return (
    <PackagingModal title="Báo giá mới" onClose={onClose} busy={busy}
      subtitle="Giá VNĐ chưa VAT theo đơn vị tính của danh mục. Báo giá mới nhất của một mã là giá mới ở màn Tác động."
      footer={<>
        <button className="btn ghost" onClick={onClose} disabled={busy}>Hủy</button>
        <button className="btn" onClick={submit} disabled={busy}>{busy ? 'Đang lưu…' : 'Lưu báo giá'}</button>
      </>}>
      <form className="pkg-form" onSubmit={(e) => { e.preventDefault(); submit() }}>
        <div>
          <label>Mã VTBB *</label>
          {locked ? <div className="pkg-ro">{code.toUpperCase()}</div>
            : <input value={code} placeholder="Vd: NAP0085" onChange={(e) => setCode(e.target.value)} />}
        </div>
        <div>
          <label>Mã NCC</label>
          <input value={supplier} placeholder="Bỏ trống nếu chưa rõ" onChange={(e) => setSupplier(e.target.value)} />
        </div>
        <div>
          <label>Đơn giá (VNĐ, chưa VAT) *</label>
          <NumberInput value={price} maxDecimals={PRICE_DECIMALS} onChange={setPrice} />
        </div>
        <div>
          <label>VAT (%)</label>
          <NumberInput value={vat} max={99.99} maxDecimals={2} onChange={setVat} />
        </div>
        <div>
          <label>Ngày hiệu lực *</label>
          <input type="date" value={validFrom} onChange={(e) => setValidFrom(e.target.value)} />
        </div>
        <div className="full">
          <label>Ghi chú</label>
          <textarea value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        {error && <div className="full pkg-err">{error}</div>}
      </form>
    </PackagingModal>
  )
}
