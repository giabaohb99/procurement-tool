import { useEffect, useState } from 'react'
import { Link, useOutletContext } from 'react-router-dom'
import { History } from 'lucide-react'

import { api } from '@/api/client'
import type { HelpAuditLog } from '@/components/help-audit-timeline'
import { fetchFaqs, type Faq } from '@/lib/faq-api'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import type { AdminOutletContext } from '@/layouts/admin-layout'
import { findNode } from '@/lib/help-tree'

// /admin/lich-su — nhật ký thay đổi của MỌI bài viết hướng dẫn VÀ câu hỏi thường gặp.
// Backend: GET /api/audit-logs?entity=... (bỏ entity_id = lấy toàn bộ của entity đó).
// API chỉ nhận 1 entity mỗi lần nên gọi 2 lượt rồi trộn theo thời gian.

const LIMIT = 200

interface GlobalAuditLog extends HelpAuditLog {
  entity_id: number
  entity: 'help_article' | 'faq'
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
  const [faqs, setFaqs] = useState<Faq[]>([])

  useEffect(() => {
    let cancelled = false

    const load = (entity: 'help_article' | 'faq') =>
      api.get('/api/audit-logs', { params: { entity, limit: LIMIT } })
        .then((res) => (res.data.data as GlobalAuditLog[]).map((l) => ({ ...l, entity })))
        .catch(() => [] as GlobalAuditLog[])

    Promise.all([load('help_article'), load('faq'), fetchFaqs().catch(() => [] as Faq[])])
      .then(([articleLogs, faqLogs, faqList]) => {
        if (cancelled) return
        setFaqs(faqList)
        setLogs(
          [...articleLogs, ...faqLogs]
            .sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime())
            .slice(0, LIMIT),
        )
      })

    return () => { cancelled = true }
  }, [])

  return (
    <div className="mx-auto max-w-4xl px-8 py-7 pb-16">
      <h1 className="text-xl font-bold text-navy">Lịch sử thay đổi</h1>
      <p className="mb-6 mt-1 text-sm text-muted-foreground">
        Toàn bộ thao tác tạo / sửa / xóa trên bài viết hướng dẫn và câu hỏi thường gặp,
        mới nhất trước (tối đa {LIMIT} bản ghi).
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
            // Bản ghi đã xóa sẽ không còn trong cây / danh sách — vẫn giữ log nhưng không link được
            const isFaq = log.entity === 'faq'
            const target = isFaq
              ? faqs.find((f) => f.id === log.entity_id)
              : findNode(tree, log.entity_id)
            const label = isFaq ? (target as Faq)?.question : (target as any)?.title
            const href = isFaq ? `/admin/faq/${log.entity_id}` : `/admin/${log.entity_id}`
            return (
              <li key={idx} className="flex gap-3.5 border-b p-4 last:border-b-0">
                <Avatar className="size-8 shrink-0">
                  <AvatarFallback className="bg-accent text-sm font-semibold text-accent-foreground">
                    {log.by?.[0]?.toUpperCase() || 'S'}
                  </AvatarFallback>
                </Avatar>

                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    {label ? (
                      <Link to={href} className="truncate font-semibold text-navy hover:text-primary hover:underline">
                        {label}
                      </Link>
                    ) : (
                      <span className="truncate font-semibold text-muted-foreground line-through">
                        {isFaq ? 'Câu hỏi' : 'Bài viết'} #{log.entity_id}
                      </span>
                    )}
                    <Badge variant="outline" className="font-normal text-muted-foreground">
                      {isFaq ? 'Câu hỏi' : 'Bài viết'} · {log.action_label}
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
