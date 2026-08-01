// Timeline lịch sử chỉnh sửa bài viết HDSD (đọc từ /api/audit-logs).
// service.update_article ghi message dạng JSON {"Tiêu đề": "...", ...} nên cần parse để hiện đẹp.

export interface HelpAuditLog {
  action: string
  action_label: string
  message: string
  by: string
  at: string
}

function LogMessage({ message }: { message: string }) {
  if (!message) return null

  if (message.startsWith('{')) {
    try {
      const data = JSON.parse(message) as Record<string, unknown>
      return (
        <div style={{ marginTop: 4, fontSize: 13.5 }}>
          {Object.entries(data).map(([field, value]) => (
            <div key={field} style={{ marginBottom: 2 }}>
              • Đổi <b>{field}</b> thành <b>{String(value) || 'Trống'}</b>
            </div>
          ))}
        </div>
      )
    } catch {
      // message không phải JSON hợp lệ → hiện nguyên văn
    }
  }
  return <div>{message}</div>
}

export default function HelpAuditTimeline({ logs }: { logs: HelpAuditLog[] }) {
  return (
    <div>
      <h3 style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 16, marginTop: 0, marginBottom: 16 }}>
        <i className="ti ti-history" /> Lịch sử chỉnh sửa
      </h3>

      {logs.length === 0 ? (
        <div style={{ color: 'var(--muted)', textAlign: 'center', padding: '16px 0' }}>
          Chưa có lịch sử chỉnh sửa nào.
        </div>
      ) : (
        logs.map((log, idx) => (
          <div key={idx} style={{ display: 'flex', marginBottom: 18 }}>
            <div style={{ width: 32, height: 32, flexShrink: 0, borderRadius: '50%', background: '#e0f2fe',
                          color: 'var(--teal)', display: 'grid', placeItems: 'center',
                          marginRight: 14, fontWeight: 600, fontSize: 14 }}>
              {log.by?.[0]?.toUpperCase() || 'S'}
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 2, flexWrap: 'wrap' }}>
                <strong style={{ color: 'var(--navy)' }}>{log.by}</strong>
                <span style={{ fontSize: 12, padding: '2px 8px', borderRadius: 20,
                               border: '1px solid var(--border)', color: 'var(--muted)' }}>
                  {log.action_label}
                </span>
                <span style={{ color: 'var(--muted)', fontSize: 13 }}>
                  {new Date(log.at).toLocaleString('vi-VN')}
                </span>
              </div>
              <div style={{ color: 'var(--muted)', fontSize: 14 }}>
                <LogMessage message={log.message} />
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  )
}
