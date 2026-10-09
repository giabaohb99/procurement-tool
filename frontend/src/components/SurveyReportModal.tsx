// Khung hộp thoại dùng chung của khối «Báo cáo thực hiện» bản v1 — tách khỏi
// `SurveyReportCard.tsx` (duoc-CR-613) để hộp «Thêm hồ sơ đầu tiên» ở tệp riêng dùng lại được.
// C-01: chỉ đóng bằng Hủy / X; form dở thì hỏi xác nhận; KHÔNG bọc <form> để Enter trong ô
// con không submit form cha của trang.
import { askConfirm } from './confirm'

export function ReportModal({ title, dirty, width = 680, onClose, footer, children }: {
  title: string
  dirty: boolean
  width?: number
  onClose: () => void
  footer: React.ReactNode
  children: React.ReactNode
}) {
  async function requestClose() {
    if (dirty) {
      const ok = await askConfirm({ title: 'Đóng hộp thoại', message: 'Bạn có thay đổi chưa lưu. Đóng và bỏ thay đổi?', confirmText: 'Đóng', danger: true })
      if (!ok) return
    }
    onClose()
  }
  return (
    <div className="srp-modal-overlay">
      <div className="card srp-modal" style={{ width }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h3 className="sec-title" style={{ margin: 0, border: 0, padding: 0 }}>{title}</h3>
          <span className="clickable" style={{ color: '#94a3b8', fontSize: 18 }} onClick={requestClose}><i className="ti ti-x" /></span>
        </div>
        {children}
        <div className="srp-modal-foot">
          {footer}
        </div>
      </div>
    </div>
  )
}

export function useCancel(dirty: boolean, onClose: () => void) {
  return async () => {
    if (dirty) {
      const ok = await askConfirm({ title: 'Đóng hộp thoại', message: 'Bạn có thay đổi chưa lưu. Đóng và bỏ thay đổi?', confirmText: 'Đóng', danger: true })
      if (!ok) return
    }
    onClose()
  }
}
