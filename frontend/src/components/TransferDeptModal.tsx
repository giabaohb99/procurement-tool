import { useEffect, useState } from 'react'
import SearchSelect from './SearchSelect'

/** bao-CR-414 GĐ5 — hộp thoại CHUYỂN PHÒNG XỬ LÝ / TRẢ VỀ PHÒNG LẬP cho YCMH và YCBG.
 *
 * `mode = 'transfer'`: chọn phòng đích (bỏ phòng đang xử lý) + lý do bắt buộc.
 * `mode = 'return'`: chỉ hỏi lý do, đích là phòng lập phiếu (backend đặt `handler_dept_id` = 0).
 * Không có lựa chọn chuyển MỘT PHẦN dòng — cả phiếu đi cùng nhau (luật đã chốt ở HDSD). */
interface TransferDeptModalProps {
  open: boolean
  mode: 'transfer' | 'return'
  docLabel: string                               // "yêu cầu mua hàng" / "yêu cầu báo giá"
  options: { value: string; label: string }[]    // mọi phòng đang hoạt động
  currentDeptId: number                          // phòng ĐANG xử lý (phòng được nhờ, hoặc phòng lập nếu 0)
  requestingDeptId: number                       // phòng lập phiếu
  onConfirm: (handlerDeptId: number, reason: string) => void
  onCancel: () => void
}

export default function TransferDeptModal({
  open, mode, docLabel, options, currentDeptId, requestingDeptId, onConfirm, onCancel,
}: TransferDeptModalProps) {
  const [deptId, setDeptId] = useState('')
  const [reason, setReason] = useState('')
  const [touched, setTouched] = useState(false)

  useEffect(() => {
    if (open) { setDeptId(''); setReason(''); setTouched(false); document.body.style.overflow = 'hidden' }
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  useEffect(() => {
    if (!open) return
    const h = (e: KeyboardEvent) => { if (e.key === 'Escape') onCancel() }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [open, onCancel])

  if (!open) return null

  const isTransfer = mode === 'transfer'
  const effectiveCurrent = currentDeptId || requestingDeptId
  const targetOptions = options.filter((o) => Number(o.value) !== effectiveCurrent)
  const reasonOk = reason.trim().length > 0
  const deptOk = !isTransfer || !!deptId
  const canSubmit = reasonOk && deptOk

  function submit() {
    setTouched(true)
    if (!canSubmit) return
    onConfirm(isTransfer ? Number(deptId) : 0, reason.trim())
  }

  return (
    <div className="confirm-modal-overlay">
      <div className="confirm-modal" style={{ textAlign: 'left', maxWidth: 520 }} onClick={(e) => e.stopPropagation()}>
        <div className="confirm-modal-icon" style={{ color: isTransfer ? '#3b82f6' : '#f59e0b' }}>
          <i className={isTransfer ? 'ti ti-transfer' : 'ti ti-corner-up-left'} />
        </div>
        <h3 className="confirm-modal-title">{isTransfer ? 'Chuyển phòng xử lý' : 'Trả về phòng lập'}</h3>
        <p className="confirm-modal-message" style={{ marginBottom: 12 }}>
          {isTransfer
            ? `Đẩy cả ${docLabel} này sang phòng khác xử lý. Người phụ trách hiện tại ở mọi dòng sẽ được gỡ để phòng nhận phân công lại. Không chuyển một phần dòng.`
            : `Trả cả ${docLabel} này về phòng lập phiếu tự xử lý. Người phụ trách hiện tại ở mọi dòng sẽ được gỡ.`}
        </p>
        {isTransfer && (
          <div style={{ marginBottom: 12 }}>
            <label style={{ display: 'block', fontSize: 13, marginBottom: 4 }}>Phòng nhận xử lý <span style={{ color: 'var(--red)' }}>*</span></label>
            <SearchSelect value={deptId} onChange={setDeptId} options={targetOptions} placeholder="Chọn phòng ban" autoSelectSingle={false} />
            {touched && !deptOk && <div style={{ color: 'var(--red)', fontSize: 12, marginTop: 4 }}>Phải chọn phòng nhận</div>}
          </div>
        )}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', fontSize: 13, marginBottom: 4 }}>Lý do <span style={{ color: 'var(--red)' }}>*</span></label>
          <textarea className="form-control" rows={3} value={reason} placeholder="Ghi vào nhật ký phiếu, người lập và người phụ trách cũ đều đọc được"
            onChange={(e) => setReason(e.target.value)} style={{ width: '100%', resize: 'vertical' }} />
          {touched && !reasonOk && <div style={{ color: 'var(--red)', fontSize: 12, marginTop: 4 }}>Phải nêu lý do</div>}
        </div>
        <div className="confirm-modal-actions">
          <button type="button" className="btn secondary" style={{ color: 'var(--muted)', borderColor: '#e2e8f0' }} onClick={onCancel}>Đóng</button>
          <button type="button" className="btn" onClick={submit} disabled={!canSubmit}>
            {isTransfer ? 'Chuyển phòng' : 'Trả về'}
          </button>
        </div>
      </div>
    </div>
  )
}
