import { useEffect, useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import { History } from 'lucide-react'

import { api } from '@/api/client'
import type { HelpAuditLog } from '@/components/help-audit-timeline'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import type { AdminOutletContext } from '@/layouts/admin-layout'
import { findNode } from '@/lib/help-tree'

// /admin/lich-su — nhật ký thay đổi của MỌI bài viết hướng dẫn.
// Backend: GET /api/audit-logs?entity=help_article (bỏ entity_id = lấy toàn bộ).

const LIMIT = 200

interface GlobalAuditLog extends HelpAuditLog {
  entity_id: number
}

/** message của update_article là JSON {"Tiêu đề": "...", ...} — parse để hiện cho dễ đọc. */
function LogMessage({ message }: { message: string }) {
  if (!message) return null

  if (message.startsWith('{')) {
    try {
      const data = JSON.parse(message) as Record<string, unknown>
      return (
        <div className="mt-1 space-y-0.5 text-sm text-muted-foreground">
          {Object.entries(data).map(([field, value]) => (
            <div key={field}>
              • Đổi <b className="text-navy">{field}</b> thành{' '}
              <b className="text-navy">{String(value) || 'Trống'}</b>
            </div>
          ))}
        </div>
      )
    } catch {
      // không phải JSON hợp lệ → hiện nguyên văn
    }
  }
  return <div className="mt-1 text-sm text-muted-foreground">{message}</div>
}

export default function AdminHistory() {
  const { tree } = useOutletContext<AdminOutletContext>()
  const [logs, setLogs] = useState<GlobalAuditLog[] | null>(null)

  useEffect(() => {
    let cancelled = false
    api.get('/api/audit-logs', { params: { entity: 'help_article', limit: LIMIT } })
      .then((res) => { if (!cancelled) setLogs(res.data.data) })
      .catch(() => { if (!cancelled) setLogs([]) })
    return () => { cancelled = true }
  }, [])

  return (
    <div className="mx-auto max-w-4xl px-8 py-7 pb-16">
      <h1 className="text-xl font-bold text-navy">Lịch sử thay đổi</h1>
      <p className="mb-6 mt-1 text-sm text-muted-foreground">
        Toàn bộ thao tác tạo / sửa / xóa trên tài liệu hướng dẫn, mới nhất trước
        (tối đa {LIMIT} bản ghi).
      </p>

      {!logs ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }, (_, i) => <Skeleton key={i} className="h-16 w-full" />)}
        </div>
      ) : logs.length === 0 ? (
        <div className="rounded-md border border-dashed px-6 py-12 text-center">
          <History className="mx-auto mb-2 size-8 text-muted-foreground" strokeWidth={1.5} />
          <strong className="block text-navy">Chưa có thay đổi nào</strong>
          <span className="text-sm text-muted-foreground">
            Mọi thao tác trên bài viết sẽ được ghi lại ở đây.
          </span>
        </div>
      ) : (
        <ul className="overflow-hidden rounded-md border">
          {logs.map((log, idx) => {
            // Bài đã xóa sẽ không còn trong cây — vẫn giữ log nhưng không link được
            const article = findNode(tree, log.entity_id)
            return (
              <li key={idx} className="flex gap-3.5 border-b p-4 last:border-b-0">
                <Avatar className="size-8 shrink-0">
                  <AvatarFallback className="bg-accent text-sm font-semibold text-accent-foreground">
                    {log.by?.[0]?.toUpperCase() || 'S'}
                  </AvatarFallback>
                </Avatar>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    {article ? (
                      <Link
                        to={`/admin/${article.id}`}
                        className="truncate font-semibold text-navy hover:text-primary hover:underline"
                      >
                        {article.title}
                      </Link>
                    ) : (
                      <span className="truncate font-semibold text-muted-foreground line-through">
                        Bài viết #{log.entity_id}
                      </span>
                    )}
                    <Badge variant="outline" className="font-normal text-muted-foreground">
                      {log.action_label}
                    </Badge>
                  </div>

                  <LogMessage message={log.message} />

                  <div className="mt-1 text-xs text-muted-foreground">
                    {log.by} · {new Date(log.at).toLocaleString('vi-VN')}
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
