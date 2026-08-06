import { useState } from 'react'
import { fmtDateTime } from '../utils/datetime'

/**
 * Dòng thời gian "Lịch sử thao tác" của một chứng từ.
 *
 * Trước đây 6 trang chi tiết mỗi trang tự vẽ một bản gần giống nhau và đổ HẾT log ra một lượt.
 * Phiếu bị sửa nhiều (thực tế trên hệ thống thật có phiếu 60 dòng) thì khối này dài hơn cả
 * nội dung phiếu, mà 99% thời gian người ta chỉ cần vài thao tác gần nhất.
 *
 * API trả MỚI NHẤT TRƯỚC nên cắt N dòng đầu là đúng thứ tự cần.
 */

export type LogItem = {
  action: string
  action_label: string
  message?: string
  by: string
  at: string
}

const MOI_LAN = 10
// Backend mặc định chỉ trả 100 dòng gần nhất (`/api/audit-logs`, tham số `limit`).
// Chạm ngưỡng thì phải nói ra, không thì người đọc tưởng phiếu chỉ có đúng chừng đó thao tác.
const TRAN = 100

/** Màu chấm: xanh lá = việc thành, đỏ = việc hỏng/hủy, còn lại xanh ngọc. */
function mauCham(action: string): string {
  if (action === 'approved' || action === 'paid' || action === 'create') return 'create'
  if (action === 'rejected' || action === 'cancelled' || action === 'delete') return 'delete'
  return 'update'
}

const nutPill: React.CSSProperties = {
  border: '1px solid #eaeef4', background: '#fff', borderRadius: 999,
  padding: '7px 16px', fontSize: 13, fontWeight: 600, cursor: 'pointer',
  fontFamily: 'inherit', display: 'inline-flex', alignItems: 'center', gap: 6,
}

export default function AuditTimeline({ logs, showMessage = true }: {
  logs: LogItem[]
  /** Danh mục dùng chung (CrudDetail) chỉ cần "ai làm gì lúc nào", không cần diễn giải. */
  showMessage?: boolean
}) {
  const [hien, setHien] = useState(MOI_LAN)
  const con = logs.length - hien

  return (
    <>
      <div className="timeline">
        {logs.slice(0, hien).map((l, i) => (
          <div key={i} className="tl-item">
            <span className={'tl-dot ' + mauCham(l.action)} />
            <div>
              <div style={{ fontSize: 13 }}>
                <b>{l.by}</b> — {l.action_label}{showMessage && l.message ? `: ${l.message}` : ''}
              </div>
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>{fmtDateTime(l.at)}</div>
            </div>
          </div>
        ))}
      </div>

      {(con > 0 || hien > MOI_LAN) && (
        <div style={{ display: 'flex', gap: 8, marginTop: 12 }}>
          {con > 0 && (
            <button type="button" onClick={() => setHien((n) => n + MOI_LAN)}
                    style={{ ...nutPill, color: 'var(--navy)' }}>
              Xem thêm {Math.min(con, MOI_LAN)} thao tác{con > MOI_LAN ? ` (còn ${con})` : ''}
            </button>
          )}
          {hien > MOI_LAN && (
            <button type="button" onClick={() => setHien(MOI_LAN)}
                    style={{ ...nutPill, color: 'var(--muted)' }}>
              <i className="ti ti-chevrons-up" style={{ fontSize: 15 }} />
              Thu gọn
            </button>
          )}
        </div>
      )}

      {logs.length >= TRAN && con <= 0 && (
        <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 10 }}>
          Chỉ hiện {TRAN} thao tác gần nhất.
        </div>
      )}
    </>
  )
}
