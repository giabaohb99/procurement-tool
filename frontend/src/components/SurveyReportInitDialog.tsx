// duoc-CR-614 (09/10/2026) — bản v1 của hộp chọn mẫu «Khởi tạo báo cáo mẫu» (v2:
// `frontend-v2/.../survey-report/survey-report-init-dialog.tsx`). Danh sách mẫu lấy từ
// `GET .../templates`: mẫu chung hồ sơ nhập khẩu (5 giai đoạn) và tiến độ kế hoạch công việc
// nhập khẩu (21 việc, một giai đoạn — theo file Excel của Phòng Thu mua).
import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import { ReportModal } from './SurveyReportModal'

interface TemplateOption {
  id: number
  name: string
  description: string
  phase_count: number
  doc_count: number
}

type Props = {
  /** `/api/execution-report/{entity}/{id}` — gốc đường API của khối. */
  base: string
  busy: boolean
  onConfirm: (template: number) => Promise<boolean>
  onClose: () => void
}

export default function SurveyReportInitDialog({ base, busy, onConfirm, onClose }: Props) {
  const [options, setOptions] = useState<TemplateOption[] | null>(null)
  const [loadFailed, setLoadFailed] = useState(false)
  //  0 = chưa chọn tay → dùng mẫu ĐẦU danh sách (mẫu chung, đúng hành vi cũ của nút).
  const [picked, setPicked] = useState(0)
  //  Chặn bấm đúp ngay trong nhịp — `busy` là state, chỉ đúng ở lần render sau.
  const savingRef = useRef(false)

  useEffect(() => {
    let alive = true
    api.get(`${base}/templates`)
      .then((r) => { if (alive) setOptions(r.data.data) })
      //  `client.ts` KHÔNG toast lỗi cho GET — hộp tự báo ở dưới, và khóa nút Khởi tạo.
      .catch(() => { if (alive) setLoadFailed(true) })
    return () => { alive = false }
  }, [base])

  const loading = !options && !loadFailed
  const selected = picked || options?.[0]?.id || 0

  async function confirm() {
    if (savingRef.current || !selected) return
    savingRef.current = true
    try { await onConfirm(selected) } finally { savingRef.current = false }
  }

  return (
    <ReportModal
      title="Khởi tạo báo cáo mẫu"
      dirty={false}
      width={560}
      onClose={onClose}
      footer={
        <>
          <span />
          <span style={{ display: 'flex', gap: 8 }}>
            <button type="button" className="btn ghost" disabled={busy} onClick={onClose}>Hủy</button>
            <button type="button" className="btn" disabled={busy || loading || loadFailed || !selected} onClick={confirm}>
              <i className="ti ti-sparkles" /> Khởi tạo
            </button>
          </span>
        </>
      }
    >
      <div style={{ color: 'var(--muted)', fontSize: 13, marginBottom: 12 }}>
        Chọn mẫu để dựng sẵn giai đoạn và bộ hồ sơ. Sau đó sửa, thêm, xóa tự do ngay trên dạng Bảng.
      </div>
      {loading && <div style={{ color: 'var(--muted)', fontSize: 13 }}>Đang tải danh sách mẫu…</div>}
      {loadFailed && (
        <div style={{ color: 'var(--err, #dc2626)', fontSize: 12.5 }}>
          Không tải được danh sách mẫu. Đóng hộp rồi thử lại; nếu vẫn lỗi thì báo quản trị hệ thống.
        </div>
      )}
      {options && (
        <div className="srp-tpl-list" role="radiogroup" aria-label="Mẫu báo cáo">
          {options.map((option) => (
            <label key={option.id} className={`srp-tpl${selected === option.id ? ' on' : ''}`}>
              <input
                type="radio"
                name="report-template"
                value={option.id}
                checked={selected === option.id}
                onChange={() => setPicked(option.id)}
              />
              <span>
                <b>{option.name}</b>
                <small>{option.phase_count} giai đoạn · {option.doc_count} hồ sơ — {option.description}</small>
              </span>
            </label>
          ))}
        </div>
      )}
    </ReportModal>
  )
}
