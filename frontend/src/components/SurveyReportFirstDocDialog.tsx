// duoc-CR-613 (09/10/2026) — bản v1 của hộp «Thêm hồ sơ đầu tiên» (v2: duoc-CR-611,
// `frontend-v2/.../survey-report/survey-report-first-doc-dialog.tsx`). Khối Báo cáo thực hiện
// còn TRỐNG: chọn dòng hàng + giai đoạn mặc định + tên; backend dựng khung (5 giai đoạn + nút
// theo dòng, KHÔNG đổ mẫu) rồi thêm đúng hồ sơ đó. Ô chọn lấy từ `GET .../first-doc-options`.
import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import { toast } from './toast'
import { ReportModal, useCancel } from './SurveyReportModal'

/** Giá trị ô chọn dòng hàng của hồ sơ CHUNG — trùng `line_id = 0` gửi lên backend. */
const COMMON_LINE = '0'
/** Trần độ dài tên hồ sơ — khớp `max_length=255` của `ReportFirstDocIn`. */
const TITLE_MAX = 255

/** `GET /api/execution-report/{entity}/{id}/first-doc-options`. */
interface FirstDocOptions {
  lines: { line_id: number; name: string }[]
  phases: { order: number; name: string; location: string }[]
}

export interface ReportFirstDocPayload {
  title: string
  /** 0 = Chung (cả phiếu / cả đơn). */
  line_id: number
  phase_order: number
}

type Props = {
  /** `/api/execution-report/{entity}/{id}` — gốc đường API của khối. */
  base: string
  /** «phiếu» / «đơn» — chữ của dòng Chung. */
  ownerLabel: string
  busy: boolean
  onSave: (payload: ReportFirstDocPayload) => Promise<boolean>
  onClose: () => void
}

export default function SurveyReportFirstDocDialog({ base, ownerLabel, busy, onSave, onClose }: Props) {
  const [options, setOptions] = useState<FirstDocOptions | null>(null)
  const [loadFailed, setLoadFailed] = useState(false)
  const [title, setTitle] = useState('')
  const [lineId, setLineId] = useState(COMMON_LINE)
  const [phaseOrder, setPhaseOrder] = useState('0')
  const dirty = title !== '' || lineId !== COMMON_LINE || phaseOrder !== '0'
  const cancel = useCancel(dirty, onClose)
  //  Chặn bấm đúp / Enter liên tiếp ngay trong nhịp — `busy` là state, chỉ đúng ở lần render sau.
  const savingRef = useRef(false)

  useEffect(() => {
    let alive = true
    api.get(`${base}/first-doc-options`)
      .then((r) => { if (alive) setOptions(r.data.data) })
      //  `client.ts` KHÔNG toast lỗi cho GET — hộp tự báo ở dưới, và khóa nút Thêm.
      .catch(() => { if (alive) setLoadFailed(true) })
    return () => { alive = false }
  }, [base])

  const loading = !options && !loadFailed
  const lines = options?.lines ?? []
  const phases = options?.phases ?? []

  async function save() {
    if (savingRef.current) return
    const trimmed = title.trim()
    if (!trimmed) { toast.error('Nhập tên hồ sơ'); return }
    savingRef.current = true
    try {
      await onSave({ title: trimmed, line_id: Number(lineId), phase_order: Number(phaseOrder) })
    } finally {
      savingRef.current = false
    }
  }

  return (
    <ReportModal
      title="Thêm hồ sơ đầu tiên"
      dirty={dirty}
      width={520}
      onClose={onClose}
      footer={
        <>
          <span />
          <span style={{ display: 'flex', gap: 8 }}>
            <button type="button" className="btn ghost" disabled={busy} onClick={cancel}>Hủy</button>
            <button type="button" className="btn" disabled={busy || loading || loadFailed} onClick={save}>
              <i className="ti ti-plus" /> Thêm hồ sơ
            </button>
          </span>
        </>
      }
    >
      <div style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 12 }}>
        Chọn dòng hàng và giai đoạn cho hồ sơ. Hệ thống dựng sẵn 5 giai đoạn mặc định và một nút cho
        mỗi dòng hàng, KHÔNG đổ bộ hồ sơ mẫu — chi tiết (ngày, người làm, tiên quyết…) sửa sau ở nút
        bút chì trên hồ sơ.
      </div>
      {loadFailed && (
        <div style={{ color: 'var(--err, #dc2626)', fontSize: 12.5, marginBottom: 10 }}>
          Không tải được danh sách dòng hàng / giai đoạn. Đóng hộp rồi thử lại; nếu vẫn lỗi thì báo
          quản trị hệ thống.
        </div>
      )}
      <div className="form-grid">
        <div className="form-row full">
          <label htmlFor="first-doc-line">Dòng hàng</label>
          <select id="first-doc-line" value={lineId} disabled={loading} onChange={(e) => setLineId(e.target.value)}>
            <option value={COMMON_LINE}>Chung (cả {ownerLabel})</option>
            {lines.map((line) => (
              <option key={line.line_id} value={String(line.line_id)}>{line.name}</option>
            ))}
          </select>
          {!loading && !loadFailed && lines.length === 0 && (
            <div style={{ color: 'var(--muted)', fontSize: 12, marginTop: 4 }}>
              {ownerLabel === 'đơn' ? 'Đơn' : 'Phiếu'} chưa có dòng hàng nào — hồ sơ sẽ vào Chung.
            </div>
          )}
        </div>
        <div className="form-row full">
          <label htmlFor="first-doc-phase">Giai đoạn</label>
          <select id="first-doc-phase" value={phaseOrder} disabled={loading} onChange={(e) => setPhaseOrder(e.target.value)}>
            {loading && <option value="0">Đang tải giai đoạn…</option>}
            {phases.map((phase) => (
              <option key={phase.order} value={String(phase.order)}>{phase.order + 1}. {phase.name}</option>
            ))}
          </select>
        </div>
        <div className="form-row full">
          <label htmlFor="first-doc-title">Tên hồ sơ <span className="req">*</span></label>
          <input
            id="first-doc-title"
            autoFocus
            value={title}
            maxLength={TITLE_MAX}
            placeholder="VD: Giấy phép nhập khẩu chuyên ngành"
            onChange={(e) => setTitle(e.target.value)}
            onKeyDown={(e) => {
              //  Enter chốt chữ của bộ gõ tiếng Việt không phải Enter «thêm».
              if (e.nativeEvent.isComposing) return
              //  Enter = lưu, chặn mặc định để không submit form cha (bẫy biểu mẫu CR-317).
              if (e.key === 'Enter') { e.preventDefault(); void save() }
            }}
          />
        </div>
      </div>
    </ReportModal>
  )
}
