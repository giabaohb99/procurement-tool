import { useMemo, useState } from 'react'
import { api } from '../api/client'
import { toast } from './toast'
import { fmtPrice } from '../utils/money'

// bao-CR-794 — Sửa giá SAU DUYỆT trên đơn mua hàng. Đơn giữ nguyên trạng thái (không về Nháp);
// máy chủ tính lại công nợ, lịch sử mua hàng và sổ giá theo giá mới. Chỉ người có quyền duyệt
// mới thấy nút mở hộp này; máy chủ chặn lại lần nữa (đơn có YCTT đã gửi duyệt, công nợ đã trả…).

const LOCKED_PROGRESS = ['completed', 'cancelled']
const fmtVND = (n: number) => Math.round(n || 0).toLocaleString('vi-VN')

/** Dòng còn sửa giá được: chưa Hoàn thành, chưa Hủy và đã lưu (có id). */
export function priceAdjustableItems(items: any[]): any[] {
  return (items || []).filter((it) => it.id && !LOCKED_PROGRESS.includes(it.progress_status || ''))
}

interface Props {
  poId: number | string
  poCode: string
  items: any[]
  onClose: () => void
  onSaved: () => void
}

export default function PoPriceAdjustModal({ poId, poCode, items, onClose, onSaved }: Props) {
  const rows = useMemo(() => priceAdjustableItems(items), [items])
  const [prices, setPrices] = useState<Record<number, string>>(
    () => Object.fromEntries(rows.map((it) => [it.id, String(Number(it.price || 0))])))
  const [reason, setReason] = useState('')
  const [saving, setSaving] = useState(false)

  const newPriceOf = (it: any) => Number(String(prices[it.id] ?? '').replace(',', '.'))
  const isChanged = (it: any) => Math.abs(newPriceOf(it) - Number(it.price || 0)) > 1e-6
  const changed = rows.filter(isChanged)
  const invalid = changed.some((it) => !(newPriceOf(it) > 0))
  const canSave = changed.length > 0 && !invalid && reason.trim().length > 0 && !saving

  async function save() {
    if (!canSave) return
    setSaving(true)
    try {
      const res = await api.post(`/api/purchase-orders/${poId}/adjust-prices`, {
        reason: reason.trim(),
        items: changed.map((it) => ({ id: it.id, price: newPriceOf(it) })),
      })
      toast.success(res.data?.message || 'Đã sửa giá')
      onSaved()
    } catch { /* interceptor đã toast lỗi của máy chủ; giữ hộp mở để sửa tiếp */ }
    finally { setSaving(false) }
  }

  const cell: React.CSSProperties = { padding: '6px 8px', borderBottom: '1px solid var(--border)', fontSize: 13 }
  const right: React.CSSProperties = { ...cell, textAlign: 'right', whiteSpace: 'nowrap' }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 110, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 12 }} onClick={onClose}>
      <div className="modal-card" style={{ width: 860, maxWidth: '96vw', maxHeight: '90vh', background: '#fff', borderRadius: 12, boxShadow: '0 20px 25px -5px rgba(0,0,0,.15)', display: 'flex', flexDirection: 'column', overflow: 'hidden' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
          <h3 style={{ margin: 0, fontSize: 16, color: 'var(--navy)' }}>Sửa giá sau duyệt — {poCode}</h3>
          <button className="icon-btn" onClick={onClose} aria-label="Đóng"><i className="ti ti-x" style={{ fontSize: 18 }} /></button>
        </div>
        <div style={{ padding: '12px 18px', overflow: 'auto' }}>
          <p style={{ fontSize: 13, color: 'var(--muted)', margin: '0 0 10px' }}>
            Đơn giữ nguyên trạng thái. Công nợ, lịch sử mua hàng và sổ giá được tính lại theo giá mới.
            Đơn đã có yêu cầu thanh toán gửi duyệt hoặc đã trả tiền thì không sửa giá được.
          </p>
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#f8fafc', fontSize: 12.5, color: 'var(--muted)' }}>
                  <th style={{ ...cell, textAlign: 'left' }}>Mã hàng</th>
                  <th style={{ ...cell, textAlign: 'left' }}>Tên hàng</th>
                  <th style={right}>SL đặt</th>
                  <th style={right}>SL đã nhận</th>
                  <th style={right}>Đơn giá hiện tại</th>
                  <th style={right}>Đơn giá mới</th>
                  <th style={right}>Chênh lệch (chưa VAT)</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((it) => {
                  const received = Number(it.qty_received || 0)
                  const diff = received * (newPriceOf(it) - Number(it.price || 0)) * Number(it.exchange_rate || 1)
                  const touched = isChanged(it)
                  const bad = touched && !(newPriceOf(it) > 0)
                  return (
                    <tr key={it.id} style={touched ? { background: '#fffbeb' } : undefined}>
                      <td style={cell}>{it.product_code}</td>
                      <td style={cell}>{it.product_name}</td>
                      <td style={right}>{fmtPrice(it.qty_order)}</td>
                      <td style={right}>{fmtPrice(received)}</td>
                      <td style={right}>{fmtPrice(it.price)}{it.currency && it.currency !== 'VND' ? ` ${it.currency}` : ''}</td>
                      <td style={right}>
                        <input type="number" min={0} step="any" value={prices[it.id] ?? ''}
                          aria-label={`Đơn giá mới của ${it.product_code}`}
                          onChange={(e) => setPrices((old) => ({ ...old, [it.id]: e.target.value }))}
                          style={{ width: 120, textAlign: 'right', padding: '4px 6px', borderRadius: 6, border: `1px solid ${bad ? 'var(--red)' : 'var(--border)'}` }} />
                      </td>
                      <td style={{ ...right, color: !touched || !received ? 'var(--muted)' : diff > 0 ? 'var(--red)' : '#15803d' }}>
                        {touched && received > 0 ? `${diff > 0 ? '+' : ''}${fmtVND(diff)}` : '—'}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {invalid && <div style={{ color: 'var(--red)', fontSize: 12.5, marginTop: 6 }}>Đơn giá mới phải lớn hơn 0.</div>}
          <label style={{ display: 'block', fontSize: 13, fontWeight: 600, margin: '12px 0 4px' }}>Lý do sửa giá <span style={{ color: 'var(--red)' }}>*</span></label>
          <textarea rows={2} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Ví dụ: nhà cung cấp báo lại giá theo phụ lục hợp đồng…"
            style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 13.5, resize: 'vertical' }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '12px 18px', borderTop: '1px solid var(--border)' }}>
          <button className="btn ghost" onClick={onClose}>Đóng</button>
          <button className="btn" disabled={!canSave} onClick={save} style={{ background: '#d97706', color: '#fff', border: 'none', opacity: canSave ? 1 : 0.5 }}>
            {saving ? 'Đang lưu…' : `Lưu giá mới${changed.length ? ` (${changed.length} dòng)` : ''}`}
          </button>
        </div>
      </div>
    </div>
  )
}
