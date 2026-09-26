// bao-CR-498 — hộp «Trả về đâu?» của bản v1, chỉ mở khi phiếu mở CẢ HAI đường trả
// (trả người lập sửa lại / trả phòng lập tự xử lý — bao-CR-414). Một đường thì nút «Trả về» đi thẳng.
export type ReturnTarget = 'requester' | 'department'
export type ReturnResolution = ReturnTarget | 'choose' | null

/** Cùng luật với `frontend-v2/.../utils/return-action.ts` — hai bản phải ra cùng kết quả. */
export function resolveReturnAction(canReturnToRequester: boolean, canReturnToDepartment: boolean): ReturnResolution {
  if (canReturnToRequester && canReturnToDepartment) return 'choose'
  if (canReturnToRequester) return 'requester'
  if (canReturnToDepartment) return 'department'
  return null
}

const OPTIONS: { target: ReturnTarget; icon: string; title: string; description: string }[] = [
  { target: 'requester', icon: 'ti-user-edit', title: 'Trả người lập sửa lại',
    description: 'Phiếu về trạng thái «Trả về», người lập sửa nội dung rồi gửi duyệt lại từ đầu.' },
  { target: 'department', icon: 'ti-building', title: 'Trả phòng lập tự xử lý',
    description: 'Phiếu giữ nguyên trạng thái, gỡ nhân sự thu mua đang phụ trách; phòng lập tự mua.' },
]

export default function ReturnChoiceModal({ open, docLabel, onClose, onPick }: {
  open: boolean
  docLabel: string
  onClose: () => void
  onPick: (target: ReturnTarget) => void
}) {
  if (!open) return null
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 5000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
      <div onClick={(e) => e.stopPropagation()} style={{ background: '#fff', borderRadius: 16, width: 460, maxWidth: '100%', boxShadow: '0 20px 60px rgba(15,23,42,.35)', padding: '20px 22px' }}>
        <h3 style={{ margin: '0 0 6px', fontSize: 16.5, color: '#0f172a', fontWeight: 700 }}>Trả {docLabel} về đâu?</h3>
        <div style={{ fontSize: 13.5, color: '#475569', marginBottom: 14 }}>Phiếu này đang mở cả hai đường trả. Chọn một đường, bước sau sẽ hỏi lý do.</div>
        <div style={{ display: 'grid', gap: 8 }}>
          {OPTIONS.map((o) => (
            <button key={o.target} type="button" className="btn ghost"
              style={{ display: 'flex', alignItems: 'flex-start', gap: 10, textAlign: 'left', padding: '10px 12px', height: 'auto' }}
              onClick={() => { onClose(); onPick(o.target) }}>
              <i className={'ti ' + o.icon} style={{ marginTop: 2, color: '#64748b' }} />
              <span>
                <span style={{ display: 'block', fontWeight: 600, fontSize: 14 }}>{o.title}</span>
                <span style={{ display: 'block', fontSize: 12.5, color: '#64748b', fontWeight: 400 }}>{o.description}</span>
              </span>
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: 14 }}>
          <button type="button" className="btn ghost" onClick={onClose}>Hủy</button>
        </div>
      </div>
    </div>
  )
}
