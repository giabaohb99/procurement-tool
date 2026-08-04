import { History } from 'lucide-react'

import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'

// Timeline lịch sử chỉnh sửa bài viết (đọc từ /api/audit-logs).
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
        <div className="mt-1 space-y-0.5 text-sm">
          {Object.entries(data).map(([field, value]) => (
            <div key={field}>
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

export default function HelpAuditTimeline({
  logs, hideHeading = false,
}: {
  logs: HelpAuditLog[]
  /** Ẩn tiêu đề khi khối bao ngoài đã có tiêu đề riêng. */
  hideHeading?: boolean
}) {
  return (
    <div>
      {!hideHeading && (
        <h3 className="mb-4 flex items-center gap-2 text-base font-semibold text-navy">
          <History className="size-4" /> Lịch sử chỉnh sửa
        </h3>
      )}

      {logs.length === 0 ? (
        <div className="py-4 text-center text-muted-foreground">Chưa có lịch sử chỉnh sửa nào.</div>
      ) : (
        <div className="space-y-4">
          {logs.map((log, idx) => (
            <div key={idx} className="flex gap-3.5">
              <Avatar className="size-8 shrink-0">
                <AvatarFallback className="bg-accent text-sm font-semibold text-accent-foreground">
                  {log.by?.[0]?.toUpperCase() || 'S'}
                </AvatarFallback>
              </Avatar>
              <div className="min-w-0">
                <div className="mb-0.5 flex flex-wrap items-center gap-2">
                  <strong className="text-navy">{log.by}</strong>
                  <Badge variant="outline" className="font-normal text-muted-foreground">
                    {log.action_label}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {new Date(log.at).toLocaleString('vi-VN')}
                  </span>
                </div>
                <div className="text-sm text-muted-foreground">
                  <LogMessage message={log.message} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
